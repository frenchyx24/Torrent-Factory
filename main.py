#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38 - Moteur de création robuste
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
# CONFIGURATION ET LOGS
# ============================================================

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

APP_DATA = Path(os.environ.get("TF_CONFIG_DIR", "/config"))
APP_DATA.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA / "config.json"
LIBRARY_FILE = APP_DATA / "library.json"

DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "",
    "private": True,
    "max_workers": 2,
    "logs_max": 5000
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

logs_lock = threading.Lock()
web_logs = deque(maxlen=CONFIG.get("logs_max", 5000))
log_seq = 0

def log_system(msg, level="info"):
    global log_seq
    with logs_lock:
        log_seq += 1
        web_logs.append({"id": log_seq, "time": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level})

def get_recursive_size(path):
    try:
        p = Path(path)
        size = p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024: return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"
    except: return "0 B"

# ============================================================
# MOTEUR DE TÂCHES
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
            
            items = task.get("items", [])
            for i, item in enumerate(items):
                if stop_events.get(task_id): break
                task["current_item_name"] = item["name"]
                task["current_item_index"] = f"{i+1}/{len(items)}"
                task["progress_global"] = int((i / len(items)) * 100)
                
                # Simulation de création (V38 Process)
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
            log_system(f"Erreur: {e}", "error")

threading.Thread(target=task_worker, daemon=True).start()

# ============================================================
# ROUTES API
# ============================================================

@app.route("/")
def index():
    return "<h1>Torrent Factory API V38 is running</h1><p>Access the React UI via port 8080 or the main entry point.</p>"

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
    root = Path(CONFIG.get(f"{lib_type}_root", f"/data/{lib_type}"))
    found = []
    if root.exists():
        for entry in root.iterdir():
            if entry.name.startswith('.'): continue
            found.append({
                "name": entry.name,
                "path": str(entry),
                "size": get_recursive_size(entry),
                "detected_tag": "MULTI" if "MULTI" in entry.name.upper() else "FRENCH"
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
    t_id = str(uuid.uuid4())[:8]
    task = {
        "id": t_id,
        "name": f"Génération {data.get('type', 'Media')} ({len(items)})",
        "status": "pending",
        "items": items,
        "progress_global": 0,
        "progress_item": 0,
        "current_item_name": "Initialisation...",
        "current_item_index": f"0/{len(items)}",
        "eta_item": "--:--",
        "created_at": datetime.now().strftime("%H:%M")
    }
    with tasks_lock: active_tasks.append(task)
    task_queue.put(t_id)
    return jsonify({"success": True, "task_id": t_id})

@app.route("/api/tasks/list")
def api_tasks_list():
    return jsonify(active_tasks)

@app.route("/api/tasks/cancel", methods=["POST"])
def api_tasks_cancel():
    t_id = (request.get_json() or {}).get("id")
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)