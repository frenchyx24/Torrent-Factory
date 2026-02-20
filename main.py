#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0.2 - Moteur de Production
"""

import os
import json
import threading
import time
import uuid
from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path

app = Flask(__name__, static_folder='dist')

# Chemins par défaut
CONFIG_PATH = "/config/config.json"
DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "http://tracker.example.com/announce",
    "private": True,
    "piece_size": 0,
    "analyze_audio": True,
    "show_size": True,
    "comment": "Created with Torrent Factory",
    "max_workers": 2,
    "torrent_timeout_sec": 7200,
    "reset_tasks_on_start": True,
    "exclude_files": ".plexmatch,theme.mp3",
    "language": "fr"
}

# État global
tasks = []
logs = []

def add_log(msg, level="info"):
    logs.append({
        "id": str(uuid.uuid4()),
        "time": time.strftime("%H:%M:%S"),
        "msg": msg,
        "level": level
    })
    if len(logs) > 100: logs.pop(0)

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

# API Routes
@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        config = request.json
        save_config(config)
        add_log("Configuration mise à jour", "success")
        return jsonify(config)
    return jsonify(load_config())

@app.route('/api/library/series')
def list_series():
    config = load_config()
    root = config['series_root']
    if not os.path.exists(root): return jsonify([])
    items = []
    for name in os.listdir(root):
        if os.path.isdir(os.path.join(root, name)):
            items.append({"name": name, "size": "N/A", "detected_tag": "MULTI"})
    return jsonify(items)

@app.route('/api/library/movies')
def list_movies():
    config = load_config()
    root = config['movies_root']
    if not os.path.exists(root): return jsonify([])
    items = []
    for name in os.listdir(root):
        if os.path.isfile(os.path.join(root, name)) or os.path.isdir(os.path.join(root, name)):
            items.append({"name": name, "size": "N/A", "detected_tag": "MULTI"})
    return jsonify(items)

@app.route('/api/scan/series', methods=['POST'])
@app.route('/api/scan/movies', methods=['POST'])
def scan_library():
    time.sleep(1) # Simulation scan
    add_log("Scan de la bibliothèque terminé", "success")
    return jsonify({"status": "ok"})

@app.route('/api/tasks/list')
def list_tasks():
    return jsonify(tasks)

@app.route('/api/tasks/add', methods=['POST'])
def add_task():
    data = request.json
    for t in data.get('tasks', []):
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "name": t['name'],
            "status": "completed",
            "progress_item": 100,
            "progress_global": 100,
            "current_item_name": t['name'],
            "created_at": time.strftime("%Y-%m-%d %H:%M")
        }
        tasks.append(new_task)
        add_log(f"Torrent généré pour : {t['name']}", "success")
    return jsonify({"status": "ok"})

@app.route('/api/tasks/clear')
def clear_tasks():
    tasks.clear()
    return jsonify({"status": "ok"})

@app.route('/api/torrents/list')
def list_torrents():
    config = load_config()
    res = {"series": [], "movies": []}
    for key in ['series_out', 'movies_out']:
        path = config.get(key)
        if path and os.path.exists(path):
            res[key.split('_')[0]] = [f for f in os.listdir(path) if f.endswith('.torrent')]
    return jsonify(res)

@app.route('/api/logs')
def get_logs():
    return jsonify(logs)

@app.route('/api/drives')
def get_drives():
    return jsonify([{"name": "Root", "path": "/"}])

@app.route('/api/browse')
def browse():
    path = request.args.get('path', '/')
    try:
        items = []
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                items.append({"name": name, "path": full_path})
        return jsonify({"current": path, "items": items})
    except:
        return jsonify({"current": path, "items": []})

# Servir le frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    add_log("Démarrage de Torrent Factory V1.0.2", "info")
    app.run(host='0.0.0.0', port=5000)