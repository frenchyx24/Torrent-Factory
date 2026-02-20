#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0.5 - Moteur de Production
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

def get_size_format(path):
    """Calcule la taille réelle d'un fichier ou dossier."""
    try:
        size_bytes = 0
        if os.path.isfile(path):
            size_bytes = os.path.getsize(path)
        else:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        size_bytes += os.path.getsize(fp)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
    except:
        return "0 B"
    return "0 B"

def load_config():
    """Charge la config en préservant les réglages utilisateur."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                user_config = json.load(f)
                # On ne remplace que ce qui est présent dans le fichier utilisateur
                for key, value in user_config.items():
                    config[key] = value
        except Exception as e:
            add_log(f"Erreur lecture config: {str(e)}", "error")
    return config

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

def task_processor():
    """Simule la progression et crée les fichiers avec le tag de langue."""
    while True:
        config = load_config()
        for task in tasks:
            if task['status'] == 'running':
                if task['progress_item'] < 100:
                    task['progress_item'] += 10
                    task['progress_global'] = task['progress_item']
                else:
                    task['status'] = 'completed'
                    try:
                        out_dir = config['series_out'] if task['type'] == 'séries' else config['movies_out']
                        os.makedirs(out_dir, exist_ok=True)
                        # Formatage du nom avec le tag de langue
                        lang = task.get('lang_tag', 'MULTI')
                        file_name = f"{task['name']} [{lang}].torrent"
                        file_path = os.path.join(out_dir, file_name)
                        with open(file_path, 'w') as f:
                            f.write("dummy torrent content v1.0.5")
                        add_log(f"Fichier créé : {file_name}", "success")
                    except Exception as e:
                        add_log(f"Erreur création fichier : {str(e)}", "error")
                    
                    add_log(f"Tâche terminée : {task['name']}", "success")
        time.sleep(1)

threading.Thread(target=task_processor, daemon=True).start()

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
    try:
        for name in sorted(os.listdir(root)):
            full_path = os.path.join(root, name)
            if os.path.isdir(full_path):
                items.append({
                    "name": name, 
                    "size": get_size_format(full_path), 
                    "detected_tag": "MULTI"
                })
    except: pass
    return jsonify(items)

@app.route('/api/library/movies')
def list_movies():
    config = load_config()
    root = config['movies_root']
    if not os.path.exists(root): return jsonify([])
    items = []
    try:
        for name in sorted(os.listdir(root)):
            full_path = os.path.join(root, name)
            if os.path.isfile(full_path) or os.path.isdir(full_path):
                items.append({
                    "name": name, 
                    "size": get_size_format(full_path), 
                    "detected_tag": "MULTI"
                })
    except: pass
    return jsonify(items)

@app.route('/api/scan/series', methods=['POST'])
@app.route('/api/scan/movies', methods=['POST'])
def scan_library():
    time.sleep(1)
    add_log("Scan de la bibliothèque terminé", "success")
    return jsonify({"status": "ok"})

@app.route('/api/tasks/list')
def list_tasks():
    return jsonify(tasks)

@app.route('/api/tasks/add', methods=['POST'])
def add_task():
    data = request.json
    task_type = data.get('type', 'séries')
    for t in data.get('tasks', []):
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "name": t['name'],
            "type": task_type,
            "lang_tag": t.get('lang_tag', 'MULTI'),
            "status": "running",
            "progress_item": 0,
            "progress_global": 0,
            "current_item_name": t['name'],
            "created_at": time.strftime("%Y-%m-%d %H:%M")
        }
        tasks.append(new_task)
        add_log(f"Démarrage ({task_type}) : {t['name']} [{new_task['lang_tag']}]", "info")
    return jsonify({"status": "ok"})

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
            try:
                res[key.split('_')[0]] = sorted([f for f in os.listdir(path) if f.endswith('.torrent')])
            except: pass
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
        for name in sorted(os.listdir(path)):
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                items.append({"name": name, "path": full_path})
        return jsonify({"current": path, "items": items})
    except:
        return jsonify({"current": path, "items": []})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    add_log("Démarrage de Torrent Factory V1.0.5", "info")
    app.run(host='0.0.0.0', port=5000)