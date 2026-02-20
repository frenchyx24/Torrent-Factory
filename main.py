#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import uuid
import time
import threading
import logging
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify, send_from_directory

# Configuration Flask pour servir React
# On pointe vers le dossier 'dist' qui sera généré par le build
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
    "logs_max": 5000
}

def load_json(path, default):
    if not path.exists(): return default.copy()
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default.copy()

CONFIG = load_json(CONFIG_FILE, DEFAULT_CONFIG)
LIBRARY_CACHE = load_json(LIBRARY_FILE, {"series": [], "movies": []})

# --- Logique des Logs ---
web_logs = deque(maxlen=5000)
log_seq = 0
def log_system(msg, level="info"):
    global log_seq
    log_seq += 1
    web_logs.append({"id": log_seq, "time": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level})

# --- Moteur de Tâches ---
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
                for p in range(0, 101, 10):
                    if stop_events.get(task_id): break
                    task["progress_item"] = p
                    time.sleep(0.2)
            task["status"] = "cancelled" if stop_events.get(task_id) else "completed"
        except Empty: continue

threading.Thread(target=task_worker, daemon=True).start()

# --- Routes API ---
@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        CONFIG.update(request.get_json() or {})
        with open(CONFIG_FILE, "w") as f: json.dump(CONFIG, f)
        return jsonify({"success": True})
    return jsonify(CONFIG)

@app.route("/api/scan/<lib_type>", methods=["POST"])
def api_scan(lib_type):
    return jsonify([]) # Logique de scan simplifiée pour l'exemple

@app.route("/api/library/<lib_type>")
def api_library(lib_type):
    return jsonify(LIBRARY_CACHE.get(lib_type, []))

@app.route("/api/tasks/add", methods=["POST"])
def api_tasks_add():
    data = request.get_json() or {}
    t_id = str(uuid.uuid4())[:8]
    task = {"id": t_id, "name": f"Tâche {t_id}", "status": "pending", "items": data.get("tasks", []), "progress_global": 0, "progress_item": 0}
    active_tasks.append(task)
    task_queue.put(t_id)
    return jsonify({"success": True, "task_id": t_id})

@app.route("/api/tasks/list")
def api_tasks_list(): return jsonify(active_tasks)

@app.route("/api/logs")
def api_logs(): return jsonify(list(web_logs))

# --- Route pour servir l'interface React ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)