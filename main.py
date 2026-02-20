#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0.7 - Moteur Stable
"""

import os
import json
import threading
import time
import uuid
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Import sécurisé de torrent-tool
try:
    from torrent_tool import Torrent
except ImportError:
    Torrent = None

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

def task_processor():
    while True:
        config = load_config()
        for task in tasks:
            if task['status'] == 'running' and task['progress_item'] == 0:
                task['progress_item'] = 5 # Début de l'opération
                
                def run_creation(t=task, c=config):
                    if Torrent is None:
                        t['status'] = 'cancelled'
                        add_log("Erreur critique : torrent-tool n'est pas installé.", "error")
                        return

                    try:
                        source = t['source_path']
                        out_dir = c['series_out'] if t['type'] == 'séries' else c['movies_out']
                        os.makedirs(out_dir, exist_ok=True)
                        
                        clean_name = t['name'].replace('/', '_').replace('\\', '_')
                        file_name = f"{clean_name} [{t['lang_tag']}].torrent"
                        dest = os.path.join(out_dir, file_name)
                        
                        # Génération réelle via torrent-tool
                        torrent = Torrent.create_from(source)
                        torrent.announce_urls = [c['tracker_url']]
                        torrent.comment = c['comment']
                        torrent.is_private = c['private']
                        if c.get('piece_size'):
                            torrent.piece_size = int(c['piece_size'])
                        
                        torrent.save(dest)
                        
                        t['status'] = 'completed'
                        t['progress_item'] = 100
                        t['progress_global'] = 100
                        add_log(f"Torrent v1.0.7 généré : {file_name}", "success")
                    except Exception as e:
                        t['status'] = 'cancelled'
                        add_log(f"Échec création torrent : {str(e)}", "error")
                
                threading.Thread(target=run_creation).start()
        time.sleep(1)

threading.Thread(target=task_processor, daemon=True).start()

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        save_config(request.json)
        return jsonify(request.json)
    return jsonify(load_config())

@app.route('/api/tasks/add', methods=['POST'])
def add_task():
    data = request.json
    config = load_config()
    task_type = data.get('type', 'séries')
    
    for t in data.get('tasks', []):
        base_path = config['series_root'] if task_type == 'séries' else config['movies_root']
        root_path = os.path.join(base_path, t['name'])
        
        if not os.path.exists(root_path):
            add_log(f"Dossier introuvable : {root_path}", "error")
            continue

        tasks.append({
            "id": str(uuid.uuid4())[:8],
            "name": t['name'],
            "source_path": root_path,
            "type": task_type,
            "lang_tag": t.get('lang_tag', 'MULTI'),
            "status": "running",
            "progress_item": 0,
            "current_item_name": "Hachage en cours...",
            "created_at": time.strftime("%H:%M")
        })
            
    return jsonify({"status": "ok"})

@app.route('/api/tasks/list')
def list_tasks(): return jsonify(tasks)

@app.route('/api/logs')
def get_logs(): return jsonify(logs)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    if os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return send_from_directory(app.static_folder, 'index.html')
    return "Système en attente de compilation (dist/ absent)", 404

if __name__ == '__main__':
    add_log("Initialisation Torrent Factory V1.0.7", "info")
    if not os.path.exists('dist'): os.makedirs('dist')
    app.run(host='0.0.0.0', port=5000)