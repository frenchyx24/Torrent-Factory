#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38 - Moteur Réel Intégré
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
from flask import Flask, request, jsonify, send_from_directory

# ============================================================
# INITIALISATION & DEPENDANCES
# ============================================================

app = Flask(__name__, static_folder='dist', static_url_path='/')
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# Vérification FFprobe
HAS_FFPROBE = False
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    result = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, timeout=3)
    HAS_FFPROBE = (result.returncode == 0)
except Exception:
    HAS_FFPROBE = False

APP_DATA = Path(os.environ.get("TF_CONFIG_DIR", "/config"))
APP_DATA.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA / "config.json"
LIBRARY_FILE = APP_DATA / "library.json"
TASKS_FILE = APP_DATA / "tasks.json"

DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "",
    "private": True,
    "piece_size": 0,
    "max_workers": 2,
    "logs_max": 5000,
    "analyze_audio": True,
    "show_size": True,
    "comment": "Created with TF",
    "torrent_timeout_sec": 7200,
    "reset_tasks_on_start": True,
    "exclude_files": ".plexmatch,theme.mp3",
    "language": "fr"
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
    except: pass

CONFIG = load_json(CONFIG_FILE, DEFAULT_CONFIG)
LIBRARY_CACHE = load_json(LIBRARY_FILE, {"series": [], "movies": []})

# ============================================================
# LOGIQUE MOTEUR V38
# ============================================================

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
        return p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
    except: return 0

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024: return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"

def analyze_media_language(path):
    languages = set()
    if CONFIG.get("analyze_audio") and HAS_FFPROBE:
        try:
            target = path
            if path.is_dir():
                for f in path.rglob("*"):
                    if f.suffix.lower() in (".mkv", ".mp4", ".avi"):
                        target = f; break
            if target.is_file():
                cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream_tags=language", "-of", "csv=p=0", str(target)]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
                if res.returncode == 0:
                    for line in res.stdout.strip().split("\n"):
                        if line.strip(): languages.add(line.strip().lower())
        except: pass
    
    name_upper = path.name.upper()
    if "MULTI" in name_upper or (any(l in languages for l in ("fre", "fra")) and any(l in languages for l in ("eng", "en"))): return "MULTI"
    if "VOSTFR" in name_upper: return "VOSTFR"
    if any(l in languages for l in ("fre", "fra")) or any(x in name_upper for x in ["FRENCH", "TRUEFRENCH", "VFF"]): return "FRENCH"
    return "VO"

# ============================================================
# GESTION DES TÂCHES (VRAI PROCESSUS)
# ============================================================

task_queue = Queue()
active_tasks = []
stop_events = {}
tasks_lock = threading.Lock()

def build_torrent_commands(item, task_type):
    path = Path(item["path"])
    base_name = item.get("name", path.name)
    mode = item.get("mode", "movie")
    tag = item.get("lang_tag", "")
    suffix = f" {tag}" if tag else ""
    commands = []

    if mode == "movie" or task_type == "movies":
        commands.append((path, f"{base_name}{suffix}"))
    elif mode == "complete":
        commands.append((path, f"{base_name}{suffix} - S01"))
    elif mode == "season" and path.is_dir():
        for entry in path.iterdir():
            if entry.is_dir() and re.match(r"(saison|season|s\d)", entry.name, re.IGNORECASE):
                commands.append((entry, f"{base_name} - {entry.name}{suffix}"))
    return commands

def task_worker():
    while True:
        try:
            task_id = task_queue.get(timeout=1)
            with tasks_lock:
                task = next((t for t in active_tasks if t["id"] == task_id), None)
            if not task: continue

            task["status"] = "running"
            out_root = Path(CONFIG["movies_out"] if task["type"] == "movies" else CONFIG["series_out"])
            out_root.mkdir(parents=True, exist_ok=True)
            
            items = task.get("items", [])
            for i, item in enumerate(items):
                if stop_events.get(task_id): break
                
                task["current_item_name"] = item["name"]
                task["current_item_index"] = f"{i+1}/{len(items)}"
                task["progress_global"] = int((i / len(items)) * 100)
                
                commands = build_torrent_commands(item, task["type"])
                for cmd_idx, (source, title) in enumerate(commands):
                    if stop_events.get(task_id): break
                    
                    safe_title = re.sub(r'[<>:"/\\|?*]', "", title).strip()
                    output_file = out_root / f"{safe_title}.torrent"
                    task["current_detail"] = f"[{cmd_idx+1}/{len(commands)}] {safe_title}"
                    
                    # Appel réel à py3createtorrent avec toutes les options
                    cmd = [sys.executable, "-m", "py3createtorrent", "-o", str(output_file)]
                    if CONFIG.get("tracker_url"): cmd.extend(["-t", CONFIG["tracker_url"]])
                    if CONFIG.get("private"): cmd.append("-P")
                    if CONFIG.get("piece_size"): cmd.extend(["-p", str(CONFIG["piece_size"])])
                    if CONFIG.get("comment"): cmd.extend(["-c", CONFIG["comment"]])
                    
                    # Ajout des exclusions
                    exclude = CONFIG.get("exclude_files", "")
                    if exclude:
                        for pattern in exclude.split(','):
                            if pattern.strip():
                                cmd.extend(["-x", pattern.strip()])
                    
                    cmd.append(str(source))
                    
                    try:
                        # Utilisation du timeout configuré
                        timeout = CONFIG.get("torrent_timeout_sec", 7200)
                        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        start_time = time.time()
                        while process.poll() is None:
                            if stop_events.get(task_id) or (time.time() - start_time > timeout):
                                process.terminate(); break
                            task["progress_item"] = min(task.get("progress_item", 0) + 5, 95)
                            time.sleep(0.5)
                        task["progress_item"] = 100
                        log_system(f"Torrent créé: {safe_title}", "success")
                    except Exception as e:
                        log_system(f"Erreur création {safe_title}: {e}", "error")

            task["status"] = "cancelled" if stop_events.get(task_id) else "completed"
            task["progress_global"] = 100
        except Empty: continue
        except Exception as e: log_system(f"Worker Error: {e}", "error")

# Lancement des workers selon la config
num_workers = CONFIG.get("max_workers", 2)
for _ in range(num_workers):
    threading.Thread(target=task_worker, daemon=True).start()

# ============================================================
# API ROUTES
# ============================================================

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        CONFIG.update(request.get_json() or {})
        save_json(CONFIG_FILE, CONFIG)
        return jsonify({"success": True})
    return jsonify(CONFIG)

@app.route("/api/scan/<lib_type>", methods=["POST"])
def api_scan(lib_type):
    root = Path(CONFIG.get(f"{lib_type}_root"))
    found = []
    if root.exists():
        for entry in root.iterdir():
            if entry.name.startswith('.'): continue
            size = get_recursive_size(entry) if CONFIG.get("show_size") else 0
            found.append({
                "name": entry.name,
                "path": str(entry),
                "size": format_size(size),
                "detected_tag": analyze_media_language(entry)
            })
    LIBRARY_CACHE[lib_type] = found
    save_json(LIBRARY_FILE, LIBRARY_CACHE)
    return jsonify(found)

@app.route("/api/library/<lib_type>")
def api_library(lib_type):
    return jsonify(LIBRARY_CACHE.get(lib_type, []))

@app.route("/api/torrents/list")
def api_torrents_list():
    res = {"series": [], "movies": []}
    for key in ["series", "movies"]:
        path = Path(CONFIG.get(f"{key}_out"))
        if path.exists():
            for f in path.glob("*.torrent"):
                res[key].append(f.name)
    return jsonify(res)

@app.route("/api/tasks/add", methods=["POST"])
def api_tasks_add():
    data = request.get_json() or {}
    t_id = str(uuid.uuid4())[:8]
    task = {
        "id": t_id, "name": f"Génération {data.get('type')}", "status": "pending",
        "type": data.get("type"), "items": data.get("tasks", []),
        "progress_global": 0, "progress_item": 0, "created_at": datetime.now().strftime("%H:%M")
    }
    with tasks_lock: active_tasks.append(task)
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

@app.route("/api/browse")
def api_browse():
    path = Path(request.args.get("path", "/"))
    items = []
    try:
        if path.is_dir():
            for entry in path.iterdir():
                if entry.is_dir() and not entry.name.startswith('.'):
                    items.append({"name": entry.name, "path": str(entry)})
    except: pass
    return jsonify({"current": str(path), "items": sorted(items, key=lambda x: x["name"].lower())})

@app.route("/api/drives")
def api_drives():
    drives = []
    if platform.system() == "Windows":
        for l in string.ascii_uppercase:
            if os.path.exists(f"{l}:\\"): drives.append({"name": f"{l}:\\", "path": f"{l}:\\"})
    else:
        for p in ["/", "/data", "/mnt", "/media"]:
            if os.path.exists(p): drives.append({"name": p, "path": p})
    return jsonify(drives)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    # Reset des tâches si configuré
    if CONFIG.get("reset_tasks_on_start"):
        active_tasks = []
    app.run(host="0.0.0.0", port=5000, threaded=True)