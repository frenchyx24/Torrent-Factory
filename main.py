#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38.Final - Version Corrigée
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
from flask import Flask, request, jsonify, send_from_directory, make_response

# ============================================================
# INITIALISATION ET DÉPENDANCES
# ============================================================

app = Flask(__name__)
APP_DIR = Path(__file__).parent.resolve()
STATIC_FOLDER = APP_DIR / "dist"

logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

HAS_FFPROBE = False
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    result = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, timeout=3)
    HAS_FFPROBE = (result.returncode == 0)
except: pass

# ============================================================
# STOCKAGE ET CONFIG
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
        with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)
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

# ============================================================
# LOGIQUE DES TÂCHES (Worker)
# ============================================================

task_queue = Queue()
active_tasks = []
active_tasks_lock = threading.Lock()

def task_worker():
    while True:
        try:
            task_id = task_queue.get(timeout=1)
            # Logique simplifiée pour l'exemple, à étendre selon tes besoins V38
            log_system(f"Traitement tâche {task_id}...", "info")
            time.sleep(2)
            task_queue.task_done()
        except Empty: continue

threading.Thread(target=task_worker, daemon=True).start()

# ============================================================
# ROUTES API
# ============================================================

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        CONFIG.update(request.get_json() or {})
        save_json(CONFIG_FILE, CONFIG)
        return jsonify({"success": True})
    return jsonify(CONFIG)

@app.route("/api/library/<type>")
def api_library(type):
    return jsonify(LIBRARY_CACHE.get(type, []))

@app.route("/api/scan/<type>", methods=["POST"])
def api_scan(type):
    root = Path(CONFIG.get(f"{type}_root", f"/data/{type}"))
    found = []
    if root.exists():
        for entry in os.scandir(root):
            if entry.is_dir() or entry.name.endswith(('.mkv', '.mp4')):
                found.append({"name": entry.name, "path": entry.path, "detected_tag": "MULTI"})
    LIBRARY_CACHE[type] = found
    save_json(LIBRARY_FILE, LIBRARY_CACHE)
    return jsonify(found)

@app.route("/api/tasks/list")
def api_tasks_list():
    return jsonify(active_tasks)

@app.route("/api/logs")
def api_logs():
    return jsonify(list(web_logs))

# ============================================================
# SERVEUR WEB (Frontend)
# ============================================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # On essaie d'abord de servir le build React
    if path != "" and (STATIC_FOLDER / path).exists():
        return send_from_directory(str(STATIC_FOLDER), path)
    
    index_file = STATIC_FOLDER / "index.html"
    if index_file.exists():
        return send_from_directory(str(STATIC_FOLDER), "index.html")
    
    # Fallback sur l'interface intégrée corrigée
    return PAGE_HTML.replace("{{VERSION}}", "V38.Final")

# ============================================================
# INTERFACE HTML INTÉGRÉE (Corrigée)
# ============================================================

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Torrent Factory {{VERSION}}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{--bg-dark:#0f172a;--glass:rgba(30,41,59,.7);--glass-border:rgba(255,255,255,.1);--accent:#6366f1;--accent-glow:rgba(99,102,241,.4);--text-main:#f8fafc;--text-mute:#94a3b8}
body{background-color:var(--bg-dark);font-family:Outfit,sans-serif;color:var(--text-main);height:100vh;overflow:hidden}
.glass-panel{background:var(--glass);backdrop-filter:blur(16px);border:1px solid var(--glass-border);border-radius:16px;}
.sidebar{width:280px;padding:25px;display:flex;flex-direction:column;border-right:1px solid var(--glass-border);background:rgba(15,23,42,.8)}
.nav-item{padding:12px 18px;margin-bottom:6px;border-radius:12px;cursor:pointer;color:var(--text-mute);transition:.3s;display:flex;align-items:center;gap:12px}
.nav-item:hover, .nav-item.active{background:rgba(99,102,241,.2);color:#fff}
.main-content{flex:1;padding:30px;overflow-y:auto}
.custom-table{width:100%;color:#fff}
.btn-neon{background:var(--accent);color:#fff;border:none;padding:10px 24px;border-radius:8px;font-weight:600}
</style>
</head>
<body>
<div class="d-flex h-100">
<div class="sidebar">
<div class="app-title h4 mb-4"><i class="bi bi-lightning-charge-fill"></i> Torrent Factory</div>
<div class="nav-item active" onclick="switchView('series')" id="nav-series"><i class="bi bi-tv"></i> Séries</div>
<div class="nav-item" onclick="switchView('movies')" id="nav-movies"><i class="bi bi-film"></i> Films</div>
<div class="nav-item" onclick="switchView('torrents')" id="nav-torrents"><i class="bi bi-folder-check"></i> Torrents</div>
<div class="nav-item" onclick="switchView('tasks')" id="nav-tasks"><i class="bi bi-activity"></i> Tâches</div>
<div class="nav-item" onclick="switchView('logs')" id="nav-logs"><i class="bi bi-terminal"></i> Logs</div>
<div class="mt-auto nav-item" onclick="switchView('config')" id="nav-config"><i class="bi bi-gear-wide-connected"></i> Réglages</div>
</div>
<div class="main-content">
<div id="view-series" class="view-section"><h2>Bibliothèque Séries</h2><div id="list-series"></div></div>
<div id="view-movies" class="view-section" style="display:none"><h2>Bibliothèque Films</h2><div id="list-movies"></div></div>
<div id="view-torrents" class="view-section" style="display:none"><h2>Torrents Créés</h2></div>
<div id="view-tasks" class="view-section" style="display:none"><h2>Activités</h2></div>
<div id="view-logs" class="view-section" style="display:none"><h2>Logs Système</h2></div>
<div id="view-config" class="view-section" style="display:none"><h2>Configuration</h2></div>
</div>
</div>
<script>
function switchView(v){
    document.querySelectorAll('.view-section').forEach(e=>e.style.display='none');
    document.querySelectorAll('.nav-item').forEach(e=>e.classList.remove('active'));
    document.getElementById('view-'+v).style.display='block';
    document.getElementById('nav-'+v).classList.add('active');
}
// Initialisation simplifiée pour que ça marche immédiatement
document.addEventListener('DOMContentLoaded', () => {
    console.log("Interface prête");
});
</script>
</body>
</html>"""

if __name__ == "__main__":
    print(f"🚀 Torrent Factory {CONFIG.get('lang', 'fr')} démarré sur http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)