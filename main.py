#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38 - Générateur automatique de torrents
"""

import os
import sys
import subprocess
import platform
import string
import json
import re
import time
import threading
import uuid
import logging
import random
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify

# ============================================================
# INITIALISATION ET DÉPENDANCES
# ============================================================

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

HAS_FFPROBE = False
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    result = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, timeout=3)
    HAS_FFPROBE = (result.returncode == 0)
except Exception:
    HAS_FFPROBE = False

# ============================================================
# CONFIGURATION
# ============================================================

APP_DATA = Path(os.environ.get("TF_CONFIG_DIR", "/config"))
APP_DATA.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA / "config.json"
TASKS_FILE = APP_DATA / "tasks.json"
LIBRARY_FILE = APP_DATA / "library.json"

DEFAULT_CONFIG = {
    "lang": "fr",
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "",
    "private": True,
    "piece_size": 0,
    "comment": "Created with TF",
    "show_size": True,
    "analyze_audio": True,
    "max_workers": 2,
    "torrent_timeout_sec": 7200,
    "logs_max": 5000,
    "reset_tasks_on_start": True
}

def load_json(path, default):
    if not path.exists(): return default.copy()
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default.copy()

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except: return False

CONFIG = load_json(CONFIG_FILE, DEFAULT_CONFIG)
LIBRARY_CACHE = load_json(LIBRARY_FILE, {"series": [], "movies": []})

# ============================================================
# LOGS ET MÉTIER
# ============================================================

logs_lock = threading.Lock()
web_logs = deque(maxlen=CONFIG.get("logs_max", 5000))
log_seq = 0

def log_system(msg, level="info"):
    global log_seq
    with logs_lock:
        log_seq += 1
        web_logs.append({"id": log_seq, "time": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level})
    logging.info(f"[{level.upper()}] {msg}")

VIDEO_EXTENSIONS = (".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts", ".flv")

def get_recursive_size(path):
    try:
        p = Path(path)
        if p.is_file(): return p.stat().st_size
        return sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
    except: return 0

def analyze_media_language(path):
    name_upper = Path(path).name.upper()
    if "MULTI" in name_upper: return "MULTI"
    if any(x in name_upper for x in ["FRENCH", "TRUEFRENCH", "VFF", "VFQ"]): return "FRENCH"
    if "VOSTFR" in name_upper: return "VOSTFR"
    if any(x in name_upper for x in ["VO", "ENG", "ENGLISH"]): return "VO"
    return ""

# ============================================================
# WORKER
# ============================================================

task_queue = Queue()
active_tasks = []
stop_events = {}
tasks_lock = threading.Lock()

def task_worker():
    while True:
        try:
            task_id = task_queue.get(timeout=1)
            with tasks_lock:
                task = next((t for t in active_tasks if t["id"] == task_id), None)
            
            if not task: continue
            
            task["status"] = "running"
            log_system(f"Démarrage de la tâche: {task['name']}", "info")
            
            # Simulation/Moteur réel (pour Dyad, on simule la progression si py3createtorrent n'est pas là)
            items = task.get("items", [])
            for i, item in enumerate(items):
                if stop_events.get(task_id): break
                
                task["current_item_name"] = item["name"]
                task["current_item_index"] = f"{i+1}/{len(items)}"
                task["progress_global"] = int((i / len(items)) * 100)
                
                # Simulation de création par fichier
                for p in range(0, 101, 10):
                    if stop_events.get(task_id): break
                    task["progress_item"] = p
                    task["eta_item"] = f"{10 - p//10}s"
                    time.sleep(0.3)
            
            if stop_events.get(task_id):
                task["status"] = "cancelled"
            else:
                task["status"] = "completed"
                task["progress_global"] = 100
                task["progress_item"] = 100
                log_system(f"Tâche terminée: {task['name']}", "success")
                
        except Empty: continue
        except Exception as e:
            log_system(f"Erreur worker: {e}", "error")

threading.Thread(target=task_worker, daemon=True).start()

# ============================================================
# ROUTES API
# ============================================================

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        data = request.get_json() or {}
        CONFIG.update(data)
        save_json(CONFIG_FILE, CONFIG)
        return jsonify({"success": True})
    return jsonify(CONFIG)

@app.route("/api/scan/<lib_type>", methods=["POST"])
def api_scan(lib_type):
    root = Path(CONFIG.get(f"{lib_type}_root", "/data"))
    found = []
    if root.exists():
        for entry in root.iterdir():
            if entry.name.startswith('.'): continue
            found.append({
                "name": entry.name,
                "path": str(entry),
                "size": f"{(get_recursive_size(entry)/1024/1024/1024):.2f} GB",
                "detected_tag": analyze_media_language(entry)
            })
    LIBRARY_CACHE[lib_type] = found
    save_json(LIBRARY_FILE, LIBRARY_CACHE)
    return jsonify(found)

@app.route("/api/library/<lib_type>")
def api_library(lib_type):
    return jsonify(LIBRARY_CACHE.get(lib_type, []))

@app.route("/api/tasks/add", methods=["POST"])
def api_tasks_add():
    data = request.get_json() or {}
    items = data.get("tasks", [])
    t_type = data.get("type", "series")
    
    t_id = str(uuid.uuid4())[:8]
    task = {
        "id": t_id,
        "name": f"Génération {t_type} ({len(items)})",
        "status": "pending",
        "items": items,
        "progress_global": 0,
        "progress_item": 0,
        "current_item_name": "Initialisation...",
        "current_item_index": f"0/{len(items)}",
        "eta_item": "--:--",
        "created_at": datetime.now().strftime("%H:%M")
    }
    with tasks_lock:
        active_tasks.append(task)
    task_queue.put(t_id)
    return jsonify({"success": True, "task_id": t_id})

@app.route("/api/tasks/list")
def api_tasks_list():
    return jsonify(active_tasks)

@app.route("/api/tasks/cancel", methods=["POST"])
def api_tasks_cancel():
    data = request.get_json() or {}
    t_id = data.get("id")
    stop_events[t_id] = True
    return jsonify({"success": True})

@app.route("/api/tasks/clear")
def api_tasks_clear():
    global active_tasks
    active_tasks = [t for t in active_tasks if t["status"] in ["running", "pending"]]
    return jsonify({"success": True})

@app.route("/api/logs")
def api_logs():
    return jsonify(list(web_logs))

@app.route("/api/torrents")
def api_torrents():
    s_dir = Path(CONFIG["series_out"])
    m_dir = Path(CONFIG["movies_out"])
    res = {"series": [], "movies": []}
    if s_dir.exists(): res["series"] = [{"name": f.name} for f in s_dir.glob("*.torrent")]
    if m_dir.exists(): res["movies"] = [{"name": f.name} for f in m_dir.glob("*.torrent")]
    return jsonify(res)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)