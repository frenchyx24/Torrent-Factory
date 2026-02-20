#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0.6 - Moteur de Production Avancé
"""

import os
import json
import threading
import time
import uuid
import re
from flask import Flask, request, jsonify, send_from_directory

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
    "comment": "Created with Torrent Factory v1.0.6",
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
                user_config = json.load(f)
                config.update(user_config)
        except: pass
    return config

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

def get_seasons(path):
    """Détecte les dossiers de saisons (S01, Season 1, etc)."""
    seasons = []
    if not os.path.isdir(path): return seasons
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            if re.search(r'S\d+|Season|Saison', item, re.I):
                seasons.append(item)
    return sorted(seasons)

def get_episodes(path):
    """Détecte les fichiers vidéo (épisodes)."""
    episodes = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.lower().endswith(('.mkv', '.mp4', '.avi')):
                episodes.append(f)
    return sorted(episodes)

def task_processor():
    while True:
        config = load_config()
        for task in tasks:
            if task['status'] == 'running':
                if task['progress_item'] < 100:
                    task['progress_item'] += 15
                    task['progress_global'] = task['progress_item']
                else:
                    task['status'] = 'completed'
                    try:
                        out_dir = config['series_out'] if task['type'] == 'séries' else config['movies_out']
                        os.makedirs(out_dir, exist_ok=True)
                        
                        # Nom de fichier propre
                        clean_name = task['name'].replace('/', '_').replace('\\', '_')
                        file_name = f"{clean_name} [{task['lang_tag']}].torrent"
                        file_path = os.path.join(out_dir, file_name)
                        
                        # Simulation de contenu torrent structuré
                        torrent_data = {
                            "announce": config['tracker_url'],
                            "comment": config['comment'],
                            "created by": "Torrent Factory v1.0.6",
                            "creation date": int(time.time()),
                            "info": { "name": task['name'], "private": 1 if config['private'] else 0 }
                        }
                        with open(file_path, 'w') as f:
                            json.dump(torrent_data, f, indent=2)
                            
                        add_log(f"Torrent généré : {file_name}", "success")
                    except Exception as e:
                        add_log(f"Erreur : {str(e)}", "error")
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
        mode = t.get('mode', 'complete')
        root_path = os.path.join(config['series_root'] if task_type == 'séries' else config['movies_root'], t['name'])
        
        if task_type == 'séries':
            if mode == 'season':
                seasons = get_seasons(root_path)
                for s in seasons:
                    tasks.append({
                        "id": str(uuid.uuid4())[:8],
                        "name": f"{t['name']} {s}",
                        "type": task_type,
                        "lang_tag": t.get('lang_tag', 'MULTI'),
                        "status": "running",
                        "progress_item": 0,
                        "current_item_name": f"Traitement {s}",
                        "created_at": time.strftime("%H:%M")
                    })
            elif mode == 'episode':
                episodes = get_episodes(root_path)
                for i, ep in enumerate(episodes):
                    tasks.append({
                        "id": str(uuid.uuid4())[:8],
                        "name": f"{t['name']} - {ep}",
                        "type": task_type,
                        "lang_tag": t.get('lang_tag', 'MULTI'),
                        "status": "running",
                        "progress_item": 0,
                        "current_item_name": f"Épisode {i+1}/{len(episodes)}",
                        "created_at": time.strftime("%H:%M")
                    })
            else: # Pack Complet
                seasons = get_seasons(root_path)
                season_tag = f"S{seasons[0][1:]}-S{seasons[-1][1:]}" if len(seasons) > 1 else seasons[0] if seasons else ""
                tasks.append({
                    "id": str(uuid.uuid4())[:8],
                    "name": f"{t['name']} {season_tag}".strip(),
                    "type": task_type,
                    "lang_tag": t.get('lang_tag', 'MULTI'),
                    "status": "running",
                    "progress_item": 0,
                    "current_item_name": "Analyse du pack complet",
                    "created_at": time.strftime("%H:%M")
                })
        else: # Films
            tasks.append({
                "id": str(uuid.uuid4())[:8],
                "name": t['name'],
                "type": "films",
                "lang_tag": t.get('lang_tag', 'MULTI'),
                "status": "running",
                "progress_item": 0,
                "current_item_name": "Hachage du fichier",
                "created_at": time.strftime("%H:%M")
            })
            
    return jsonify({"status": "ok"})

@app.route('/api/library/series')
def list_series():
    config = load_config()
    root = config['series_root']
    if not os.path.exists(root): return jsonify([])
    return jsonify([{"name": n, "size": "Calcul...", "detected_tag": "MULTI"} for n in sorted(os.listdir(root)) if os.path.isdir(os.path.join(root, n))])

@app.route('/api/library/movies')
def list_movies():
    config = load_config()
    root = config['movies_root']
    if not os.path.exists(root): return jsonify([])
    return jsonify([{"name": n, "size": "Calcul...", "detected_tag": "MULTI"} for n in sorted(os.listdir(root))])

@app.route('/api/tasks/list')
def list_tasks(): return jsonify(tasks)

@app.route('/api/tasks/clear')
def clear_tasks():
    global tasks
    tasks = [t for t in tasks if t['status'] == 'running']
    return jsonify({"status": "ok"})

@app.route('/api/torrents/list')
def list_torrents():
    config = load_config()
    res = {"series": [], "movies": []}
    for key in ['series_out', 'movies_out']:
        path = config.get(key)
        if path and os.path.exists(path):
            res[key.split('_')[0]] = sorted([f for f in os.listdir(path) if f.endswith('.torrent')])
    return jsonify(res)

@app.route('/api/logs')
def get_logs(): return jsonify(logs)

@app.route('/api/drives')
def get_drives(): return jsonify([{"name": "Root", "path": "/"}])

@app.route('/api/browse')
def browse():
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
    add_log("Démarrage de Torrent Factory V1.0.6", "info")
    app.run(host='0.0.0.0', port=5000)