#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0.9 - Ultra Robust Build
"""

import os
import json
import threading
import time
import uuid
import sys
import logging
import re
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    "piece_size": 21, # 2^21 = 2MB (mktorrent utilise des puissances de 2)
    "comment": "Torrent Factory V1.0.9",
    "language": "fr"
}

tasks = []
logs_list = []

def add_log(msg, level="info"):
    logs_list.append({"id": str(uuid.uuid4()), "time": time.strftime("%H:%M:%S"), "msg": msg, "level": level})
    if len(logs_list) > 100: logs_list.pop(0)

def init_folders():
    for f in ["/config", "/data/series", "/data/movies", "/data/torrents/series", "/data/torrents/movies", "dist"]:
        if not os.path.exists(f): os.makedirs(f, exist_ok=True)

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
                t['progress_item'] = 20
                try:
                    out = cfg['series_out'] if t['type'] == 'séries' else cfg['movies_out']
                    os.makedirs(out, exist_ok=True)
                    name = re.sub(r'[\\/*?:"<>|]', '_', t['name'])
                    dest = os.path.join(out, f"{name} [{t['lang_tag']}].torrent")
                    
                    # Construction de la commande mktorrent
                    # -p : privé, -a : tracker, -o : output, -c : commentaire, -l : piece size
                    cmd = ["mktorrent", "-a", cfg['tracker_url'], "-o", dest]
                    if cfg.get('private'): cmd.append("-p")
                    if cfg.get('comment'): cmd.extend(["-c", cfg['comment']])
                    # mktorrent attend une puissance de 2 pour la taille des pièces (ex: 21 pour 2MB)
                    # On simplifie ici pour la V1.0.9
                    cmd.append(t['source_path'])
                    
                    logger.info(f"Execution: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        t['status'], t['progress_item'] = 'completed', 100
                        add_log(f"Succès: {name}", "success")
                    else:
                        raise Exception(result.stderr or "Erreur mktorrent")
                        
                except Exception as e:
                    t['status'] = 'cancelled'
                    add_log(f"Erreur: {str(e)}", "error")
        time.sleep(2)

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'POST':
        with open(CONFIG_PATH, 'w') as f: json.dump(request.json, f, indent=4)
        return jsonify(request.json)
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

@app.route('/api/torrents/list')
def api_torrents_list():
    cfg = load_config()
    res = {"series": [], "movies": []}
    try:
        if os.path.exists(cfg['series_out']):
            res['series'] = [f for f in sorted(os.listdir(cfg['series_out'])) if f.endswith('.torrent')]
        if os.path.exists(cfg['movies_out']):
            res['movies'] = [f for f in sorted(os.listdir(cfg['movies_out'])) if f.endswith('.torrent')]
    except: pass
    return jsonify(res)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    fp = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(fp): return send_from_directory(app.static_folder, path)
    idx = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(idx): return send_from_directory(app.static_folder, 'index.html')
    return "<h1>V1.0.9</h1><p>Build frontend requis.</p>", 200

if __name__ == '__main__':
    init_folders()
    threading.Thread(target=task_processor, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)