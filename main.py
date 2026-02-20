#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0.8 - Full Production Build
"""

import os
import json
import threading
import time
import uuid
import sys
import logging
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Logs configurés pour la prod
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from torrent_tool import Torrent
    logger.info("Moteur hachage Torrent-Tool chargé.")
except ImportError:
    logger.error("ALERTE : torrent-tool n'est pas installé correctement !")
    Torrent = None

app = Flask(__name__, static_folder='dist')
CORS(app)

CONFIG_PATH = "/config/config.json"
if not os.path.exists("/config"): CONFIG_PATH = "config.json"

DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "http://tracker.example.com/announce",
    "private": True,
    "piece_size": 524288,
    "comment": "Torrent Factory V1.0.8",
    "language": "fr"
}

tasks = []
logs_list = []

def add_log(msg, level="info"):
    logs_list.append({"id": str(uuid.uuid4()), "time": time.strftime("%H:%M:%S"), "msg": msg, "level": level})
    if len(logs_list) > 100: logs_list.pop(0)

def init_folders():
    for f in ["/config", "/data/series", "/data/movies", "/data/torrents/series", "/data/torrents/movies", "dist"]:
        if not os.path.exists(f): 
            try: os.makedirs(f, exist_ok=True)
            except: pass

def load_config():
    c = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f: c.update(json.load(f))
        except: pass
    return c

def get_readable_size(path):
    try:
        t = 0
        if os.path.isfile(path): t = os.path.getsize(path)
        else:
            for dp, _, fns in os.walk(path):
                for f in fns: t += os.path.getsize(os.path.join(dp, f))
        for u in ['B', 'KB', 'MB', 'GB', 'TB']:
            if t < 1024: return f"{t:.2f} {u}"
            t /= 1024
    except: return "N/A"

def task_processor():
    while True:
        cfg = load_config()
        for t in tasks:
            if t['status'] == 'running' and t['progress_item'] == 0:
                t['progress_item'] = 10
                try:
                    if not Torrent: raise Exception("torrent-tool manquant")
                    out = cfg['series_out'] if t['type'] == 'séries' else cfg['movies_out']
                    os.makedirs(out, exist_ok=True)
                    name = re.sub(r'[\\/*?:"<>|]', '_', t['name'])
                    dest = os.path.join(out, f"{name} [{t['lang_tag']}].torrent")
                    
                    torrent = Torrent.create_from(t['source_path'])
                    torrent.announce_urls = [cfg['tracker_url']]
                    torrent.is_private = cfg.get('private', True)
                    if cfg.get('piece_size'): torrent.piece_size = int(cfg['piece_size'])
                    
                    torrent.save(dest)
                    t['status'], t['progress_item'] = 'completed', 100
                    add_log(f"Succès: {name}", "success")
                except Exception as e:
                    t['status'] = 'cancelled'
                    add_log(f"Erreur: {str(e)}", "error")
        time.sleep(2)

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'POST':
        save_config = request.json
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f: json.dump(save_config, f, indent=4)
        return jsonify(save_config)
    return jsonify(load_config())

@app.route('/api/library/<lib_type>')
def api_library(lib_type):
    cfg = load_config()
    root = cfg['series_root'] if lib_type == 'series' else cfg['movies_root']
    if not os.path.exists(root): return jsonify([])
    try:
        return jsonify([{"name": n, "size": get_readable_size(os.path.join(root, n)), "detected_tag": "MULTI"} for n in sorted(os.listdir(root))])
    except: return jsonify([])

@app.route('/api/tasks/add', methods=['POST'])
def api_tasks_add():
    d, cfg = request.json, load_config()
    for t in d.get('tasks', []):
        base = cfg['series_root'] if d['type'] == 'séries' else cfg['movies_root']
        tasks.append({
            "id": str(uuid.uuid4())[:8], "name": t['name'], "source_path": os.path.join(base, t['name']),
            "type": d['type'], "lang_tag": t.get('lang_tag', 'MULTI'), "status": "running",
            "progress_item": 0, "created_at": time.strftime("%H:%M")
        })
    return jsonify({"status": "ok"})

@app.route('/api/tasks/list')
def api_tasks_list(): return jsonify(tasks)

@app.route('/api/tasks/clear')
def api_tasks_clear():
    global tasks
    tasks = [t for t in tasks if t['status'] == 'running']
    return jsonify({"status": "ok"})

@app.route('/api/logs')
def api_logs(): return jsonify(logs_list)

@app.route('/api/drives')
def api_drives(): return jsonify([{"name": "Racine", "path": "/"}, {"name": "Data", "path": "/data"}])

@app.route('/api/browse')
def api_browse():
    p = request.args.get('path', '/')
    try:
        items = [{"name": n, "path": os.path.join(p, n)} for n in sorted(os.listdir(p)) if os.path.isdir(os.path.join(p, n))]
        return jsonify({"current": p, "items": items})
    except: return jsonify({"current": p, "items": []})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    fp = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(fp): return send_from_directory(app.static_folder, path)
    idx = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(idx): return send_from_directory(app.static_folder, 'index.html')
    return "<h1>V1.0.8</h1><p>En attente du build frontend...</p>", 200

if __name__ == '__main__':
    init_folders()
    threading.Thread(target=task_processor, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)