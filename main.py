#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38 - Moteur Complet Intégré
"""

import os
import sys
import subprocess
import platform
import json
import re
import time
import threading
import uuid
import logging
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify, send_from_directory

# ============================================================
# INITIALISATION
# ============================================================

app = Flask(__name__, static_folder='dist', static_url_path='/')
logging.getLogger("werkzeug").setLevel(logging.ERROR)

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
    "logs_max": 5000,
    "analyze_audio": True
}

def load_json(path, default):
    if not path.exists(): return default.copy()
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default.copy()

CONFIG = load_json(CONFIG_FILE, DEFAULT_CONFIG)
LIBRARY_CACHE = load_json(LIBRARY_FILE, {"series": [], "movies": []})

# ============================================================
# LOGIQUE V38 (MOTEUR)
# ============================================================

web_logs = deque(maxlen=CONFIG.get("logs_max", 5000))
log_seq = 0

def log_system(msg, level="info"):
    global log_seq
    log_seq += 1
    web_logs.append({"id": log_seq, "time": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level})

def get_recursive_size(path):
    try:
        p = Path(path)
        size = p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
        if size < 1024*1024: return f"{size/1024:.1f} KB"
        if size < 1024*1024*1024: return f"{size/1024/1024:.1f} MB"
        return f"{size/1024/1024/1024:.2f} GB"
    except: return "0 B"

def analyze_media_language(path):
    name_upper = Path(path).name.upper()
    if "MULTI" in name_upper: return "MULTI"
    if any(x in name_upper for x in ["FRENCH", "TRUEFRENCH", "VFF", "VFQ"]): return "FRENCH"
    if "VOSTFR" in name_upper: return "VOSTFR"
    return "VO"

# ============================================================
# GESTION DES TÂCHES
# ============================================================

task_queue = Queue()
active_tasks = []
stop_events = {}

def task_worker():
    while True:
        try:
            task_id = task_queue.get(timeout=1)
            task = next((t for t in active_tasks if t["id"] == task_id), None)
            if not task: continue
            
            task["status"] = "running"
            items = task.get("items", [])
            for i, item in enumerate(items):
                if stop_events.get(task_id): break
                task["current_item_name"] = item["name"]
                task["current_item_index"] = f"{i+1}/{len(items)}"
                task["progress_global"] = int((i / len(items)) * 100)
                
                # Ici on appellerait py3createtorrent réellement
                # Pour l'exemple, on simule la progression
                for p in range(0, 101, 10):
                    if stop_events.get(task_id): break
                    task["progress_item"] = p
                    time.sleep(0.2)
            
            task["status"] = "cancelled" if stop_events.get(task_id) else "completed"
            task["progress_global"] = 100
        except Empty: continue

threading.Thread(target=task_worker, daemon=True).start()

# ============================================================
# API ROUTES
# ============================================================

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        CONFIG.update(request.get_json() or {})
        with open(CONFIG_FILE, "w") as f: json.dump(CONFIG, f)
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
                "detected_tag": analyze_media_language(entry)
            })
    LIBRARY_CACHE[lib_type] = found
    with open(LIBRARY_FILE, "w") as f: json.dump(LIBRARY_CACHE, f)
    return jsonify(found)

@app.route("/api/library/<lib_type>")
def api_library(lib_type):
    return jsonify(LIBRARY_CACHE.get(lib_type, []))

@app.route("/api/tasks/add", methods=["POST"])
def api_tasks_add():
    data = request.get_json() or {}
    t_id = str(uuid.uuid4())[:8]
    task = {
        "id": t_id, 
        "name": f"Génération {data.get('type', 'Media')}", 
        "status": "pending", 
        "items": data.get("tasks", []), 
        "progress_global": 0, 
        "progress_item": 0,
        "current_item_name": "Initialisation...",
        "current_item_index": "0/0",
        "created_at": datetime.now().strftime("%H:%M")
    }
    active_tasks.append(task)
    task_queue.put(t_id)
    return jsonify({"success": True, "task_id": t_id})

@app.route("/api/tasks/list")
def api_tasks_list(): return jsonify(active_tasks)

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
def api_logs(): return jsonify(list(web_logs))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)