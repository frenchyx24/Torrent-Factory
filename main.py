#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0.7 - Moteur Stable Final
"""

import os
import json
import threading
import time
import uuid
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from torrent_tool import Torrent

app = Flask(__name__, static_folder='dist')
CORS(app)

CONFIG_PATH = "/config/config.json"
DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "http://tracker.example.com/announce",
    "private": True,
    "piece_size": 524288,
    "comment": "Created with Torrent Factory v1.0.7",
    "language": "fr"
}

tasks = []
logs = []

def add_log(msg, level="info"):
    logs.append({"id": str(uuid.uuid4()), "time": time.strftime("%H:%M:%S"), "msg": msg, "level": level})
    if len(logs) > 100: logs.pop(0)

def load_config():
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config.update(json.load(f))
        except: pass
    return config

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

def get_size(path):
    total = 0
    try:
        if os.path.isfile(path): return os.path.getsize(path)
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
    except: pass
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if total < 1024: return f"{total:.2f} {unit}"
        total /= 1024
    return f"{total:.2f} PB"

def task_processor():
    while True:
        config = load_config()
        for t in tasks:
            if t['status'] == 'running' and t['progress_item'] == 0:
                t['progress_item'] = 10
                try:
                    out_dir = config['series_out'] if t['type'] == 'séries' else config['movies_out']
                    os.makedirs(out_dir, exist_ok=True)
                    
                    clean_name = t['name'].replace('/', '_').replace('\\', '_')
                    dest = os.path.join(out_dir, f"{clean_name} [{t['lang_tag']}].torrent")
                    
                    torrent = Torrent.create_from(t['source_path'])
                    torrent.announce_urls = [config['tracker_url']]
                    torrent.comment = config.get('comment', 'Created with Torrent Factory')
                    torrent.is_private = config['private']
                    if config.get('piece_size'): torrent.piece_size = int(config['piece_size'])
                    
                    t['progress_item'] = 50
                    torrent.save(dest)
                    
                    t['status'] = 'completed'
                    t['progress_item'] = 100
                    t['progress_global'] = 100
                    add_log(f"Succès : {clean_name}", "success")
                except Exception as e:
                    t['status'] = 'cancelled'
                    add_log(f"Erreur : {str(e)}", "error")
        time.sleep(1)

threading.Thread(target=task_processor, daemon=True).start()

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'POST':
        save_config(request.json)
        return jsonify(request.json)
    return jsonify(load_config())

@app.route('/api/library/<lib_type>')
def api_library(lib_type):
    config = load_config()
    root = config['series_root'] if lib_type == 'series' else config['movies_root']
    if not os.path.exists(root): return jsonify([])
    items = []
    for n in sorted(os.listdir(root)):
        path = os.path.join(root, n)
        items.append({"name": n, "size": get_size(path), "detected_tag": "MULTI"})
    return jsonify(items)

@app.route('/api/tasks/add', methods=['POST'])
def api_tasks_add():
    data = request.json
    config = load_config()
    for t in data.get('tasks', []):
        base = config['series_root'] if data['type'] == 'séries' else config['movies_root']
        tasks.append({
            "id": str(uuid.uuid4())[:8],
            "name": t['name'],
            "source_path": os.path.join(base, t['name']),
            "type": data['type'],
            "lang_tag": t.get('lang_tag', 'MULTI'),
            "status": "running",
            "progress_item": 0,
            "progress_global": 0,
            "current_item_name": "Initialisation...",
            "created_at": time.strftime("%H:%M")
        })
    return jsonify({"status": "ok"})

@app.route('/api/tasks/list')
def api_tasks_list(): return jsonify(tasks)

@app.route('/api/tasks/clear')
def api_tasks_clear():
    global tasks
    tasks = [t for t in tasks if t['status'] == 'running']
    return jsonify({"status": "ok"})

@app.route('/api/tasks/cancel', methods=['POST'])
def api_tasks_cancel():
    tid = request.json.get('id')
    for t in tasks:
        if t['id'] == tid: t['status'] = 'cancelled'
    return jsonify({"status": "ok"})

@app.route('/api/logs')
def api_logs(): return jsonify(logs)

@app.route('/api/torrents/list')
def api_torrents():
    config = load_config()
    res = {"series": [], "movies": []}
    for k in ['series_out', 'movies_out']:
        p = config.get(k)
        if p and os.path.exists(p):
            res[k.split('_')[0]] = sorted([f for f in os.listdir(p) if f.endswith('.torrent')])
    return jsonify(res)

@app.route('/api/drives')
def api_drives(): return jsonify([{"name": "Système", "path": "/"}])

@app.route('/api/browse')
def api_browse():
    path = request.args.get('path', '/')
    try:
        items = [{"name": n, "path": os.path.join(path, n)} for n in sorted(os.listdir(path)) if os.path.isdir(os.path.join(path, n))]
        return jsonify({"current": path, "items": items})
    except: return jsonify({"current": path, "items": []})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    add_log("Torrent Factory V1.0.7 Ready", "info")
    if not os.path.exists('dist'): os.makedirs('dist')
    app.run(host='0.0.0.0', port=5000)