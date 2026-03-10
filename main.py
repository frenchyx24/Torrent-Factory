#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.1.0 - The Golden Build
"""

import os
import json
import threading
import time
import uuid
import logging
import re
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='dist')
CORS(app)

# Détermination du chemin de config (Docker vs Local)
CONFIG_DIR = "/config" if os.path.exists("/config") else "config"
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "http://tracker.example.com/announce",
    "private": True,
    "piece_size": 21, 
    "comment": "Torrent Factory V1.1.0",
    "language": "fr"
}

tasks = []
logs_list = []

def add_log(msg, level="info"):
    entry = {"id": str(uuid.uuid4()), "time": time.strftime("%H:%M:%S"), "msg": msg, "level": level}
    logs_list.append(entry)
    if len(logs_list) > 100: logs_list.pop(0)
    logger.info(f"[{level.upper()}] {msg}")

def init_folders():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    cfg = load_config()
    for path_key in ['series_root', 'series_out', 'movies_root', 'movies_out']:
        try:
            os.makedirs(cfg[path_key], exist_ok=True)
        except Exception as e:
            logger.warning(f"Impossible de créer {cfg[path_key]}: {e}")

def load_config():
    c = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                saved = json.load(f)
                c.update(saved)
        except Exception as e:
            logger.error(f"Erreur lecture config: {e}")
    return c

def get_readable_size(path):
    try:
        total = 0
        if os.path.isfile(path):
            total = os.path.getsize(path)
        else:
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if total < 1024:
                return f"{total:.2f} {unit}"
            total /= 1024
    except:
        return "Unknown"

def task_processor():
    add_log("Démarrage du processeur de tâches V1.1.0", "info")
    while True:
        cfg = load_config()
        for t in tasks:
            if t['status'] == 'running' and t['progress_item'] == 0:
                t['progress_item'] = 10
                try:
                    out_dir = cfg['series_out'] if t['type'] == 'séries' else cfg['movies_out']
                    os.makedirs(out_dir, exist_ok=True)
                    
                    # Nettoyage du nom de fichier
                    safe_name = re.sub(r'[\\/*?:"<>|]', '_', t['name'])
                    torrent_filename = f"{safe_name} [{t['lang_tag']}].torrent"
                    dest_path = os.path.join(out_dir, torrent_filename)
                    
                    # Commande mktorrent optimisée
                    cmd = ["mktorrent", "-a", cfg['tracker_url'], "-o", dest_path]
                    if cfg.get('private'): cmd.append("-p")
                    if cfg.get('comment'): cmd.extend(["-c", cfg['comment']])
                    # Piece size (puissance de 2)
                    cmd.extend(["-l", str(cfg.get('piece_size', 21))])
                    # Source
                    cmd.append(t['source_path'])
                    
                    t['progress_item'] = 40
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                    
                    if result.returncode == 0:
                        t['status'], t['progress_item'] = 'completed', 100
                        add_log(f"Torrent généré avec succès : {safe_name}", "success")
                    else:
                        raise Exception(result.stderr or "Erreur inconnue de mktorrent")
                        
                except Exception as e:
                    t['status'] = 'cancelled'
                    add_log(f"Échec sur {t['name']} : {str(e)}", "error")
        time.sleep(1)

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'POST':
        new_cfg = request.json
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(new_cfg, f, indent=4)
            return jsonify(new_cfg)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify(load_config())

@app.route('/api/library/<lib_type>')
def api_library(lib_type):
    cfg = load_config()
    root = cfg['series_root'] if lib_type == 'series' else cfg['movies_root']
    if not os.path.exists(root):
        return jsonify([])
    try:
        items = []
        for n in sorted(os.listdir(root)):
            if n.startswith('.'): continue
            full_path = os.path.join(root, n)
            items.append({
                "name": n,
                "size": get_readable_size(full_path),
                "detected_tag": "MULTI" # Simplifié pour V1.1.0
            })
        return jsonify(items)
    except:
        return jsonify([])

@app.route('/api/tasks/add', methods=['POST'])
def api_tasks_add():
    data, cfg = request.json, load_config()
    for t in data.get('tasks', []):
        base_dir = cfg['series_root'] if data['type'] == 'séries' else cfg['movies_root']
        tasks.append({
            "id": str(uuid.uuid4())[:8],
            "name": t['name'],
            "source_path": os.path.join(base_dir, t['name']),
            "type": data['type'],
            "lang_tag": t.get('lang_tag', 'MULTI'),
            "status": "running",
            "progress_item": 0,
            "created_at": time.strftime("%H:%M")
        })
    return jsonify({"status": "ok"})

@app.route('/api/tasks/list')
def api_tasks_list():
    return jsonify(tasks)

@app.route('/api/tasks/clear')
def api_tasks_clear():
    global tasks
    tasks = [t for t in tasks if t['status'] == 'running']
    return jsonify({"status": "ok"})

@app.route('/api/logs')
def api_logs():
    return jsonify(logs_list)

@app.route('/api/torrents/list')
def api_torrents_list():
    cfg = load_config()
    res = {"series": [], "movies": []}
    try:
        if os.path.exists(cfg['series_out']):
            res['series'] = [f for f in sorted(os.listdir(cfg['series_out'])) if f.endswith('.torrent')]
        if os.path.exists(cfg['movies_out']):
            res['movies'] = [f for f in sorted(os.listdir(cfg['movies_out'])) if f.endswith('.torrent')]
    except:
        pass
    return jsonify(res)

@app.route('/api/drives')
def api_drives():
    return jsonify([{"name": "Système", "path": "/"}, {"name": "Données", "path": "/data"}])

@app.route('/api/browse')
def api_browse():
    p = request.args.get('path', '/')
    try:
        items = [{"name": n, "path": os.path.join(p, n)} for n in sorted(os.listdir(p)) if os.path.isdir(os.path.join(p, n))]
        return jsonify({"current": p, "items": items})
    except:
        return jsonify({"current": p, "items": []})

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "version": "1.1.0"})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    fp = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(fp):
        return send_from_directory(app.static_folder, path)
    idx = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(idx):
        return send_from_directory(app.static_folder, 'index.html')
    return "<h1>Torrent Factory V1.1.0</h1><p>Frontend non trouvé. Veuillez builder l'application.</p>", 200

if __name__ == '__main__':
    init_folders()
    threading.Thread(target=task_processor, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)