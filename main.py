#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0.8 - Moteur Stable avec torrent-tool
"""

import os
import json
import threading
import time
import uuid
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Tentative d'import sécurisée
try:
    from torrent_tool import Torrent
except ImportError:
    Torrent = None

app = Flask(__name__, static_folder='dist')
CORS(app) # Autorise les requêtes cross-origin pour le dev

# Chemins par défaut
CONFIG_PATH = "/config/config.json"
DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "http://tracker.example.com/announce",
    "private": True,
    "piece_size": 524288,
    "comment": "Created with Torrent Factory v1.0.8",
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
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        add_log(f"Erreur sauvegarde config: {str(e)}", "error")

def task_processor():
    while True:
        config = load_config()
        for task in tasks:
            if task['status'] == 'running' and task['progress_item'] == 0:
                task['progress_item'] = 5
                
                def run_creation(t=task, c=config):
                    if Torrent is None:
                        t['status'] = 'cancelled'
                        add_log("Erreur : Bibliothèque torrent-tool non installée", "error")
                        return

                    try:
                        source = t['source_path']
                        out_dir = c['series_out'] if t['type'] == 'séries' else c['movies_out']
                        os.makedirs(out_dir, exist_ok=True)
                        
                        clean_name = t['name'].replace('/', '_').replace('\\', '_')
                        file_name = f"{clean_name} [{t['lang_tag']}].torrent"
                        dest = os.path.join(out_dir, file_name)
                        
                        # Création réelle avec torrent-tool
                        torrent = Torrent.create_from(source)
                        torrent.announce_urls = [c['tracker_url']]
                        torrent.comment = c['comment']
                        torrent.is_private = c['private']
                        if c.get('piece_size'):
                            torrent.piece_size = c['piece_size']
                        
                        torrent.save(dest)
                        
                        t['status'] = 'completed'
                        t['progress_item'] = 100
                        t['progress_global'] = 100
                        add_log(f"Torrent v1.0.8 généré avec succès : {file_name}", "success")
                    except Exception as e:
                        t['status'] = 'cancelled'
                        add_log(f"Erreur fatale creation : {str(e)}", "error")
                
                threading.Thread(target=run_creation).start()
        time.sleep(1)

# Lancement du processeur en arrière-plan
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
        base_path = config['series_root'] if task_type == 'séries' else config['movies_root']
        root_path = os.path.join(base_path, t['name'])
        
        if not os.path.exists(root_path):
            add_log(f"Dossier introuvable : {root_path}", "error")
            continue

        if task_type == 'séries':
            if mode == 'season':
                for s in sorted(os.listdir(root_path)):
                    sp = os.path.join(root_path, s)
                    if os.path.isdir(sp) and re.search(r'S\d+|Season|Saison', s, re.I):
                        tasks.append({
                            "id": str(uuid.uuid4())[:8],
                            "name": f"{t['name']} {s}",
                            "source_path": sp,
                            "type": task_type,
                            "lang_tag": t.get('lang_tag', 'MULTI'),
                            "status": "running",
                            "progress_item": 0,
                            "current_item_name": f"Hachage {s}",
                            "created_at": time.strftime("%H:%M")
                        })
            elif mode == 'episode':
                for root, _, files in os.walk(root_path):
                    for f in sorted(files):
                        if f.lower().endswith(('.mkv', '.mp4', '.avi')):
                            tasks.append({
                                "id": str(uuid.uuid4())[:8],
                                "name": f"{t['name']} - {f}",
                                "source_path": os.path.join(root, f),
                                "type": task_type,
                                "lang_tag": t.get('lang_tag', 'MULTI'),
                                "status": "running",
                                "progress_item": 0,
                                "current_item_name": f"Hachage {f[:25]}...",
                                "created_at": time.strftime("%H:%M")
                            })
            else: # Pack Complet
                seasons = [s for s in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, s)) and re.search(r'S\d+|Season|Saison', s, re.I)]
                tag = f"S{seasons[0][1:]}-S{seasons[-1][1:]}" if len(seasons) > 1 else seasons[0] if seasons else ""
                tasks.append({
                    "id": str(uuid.uuid4())[:8],
                    "name": f"{t['name']} {tag}".strip(),
                    "source_path": root_path,
                    "type": task_type,
                    "lang_tag": t.get('lang_tag', 'MULTI'),
                    "status": "running",
                    "progress_item": 0,
                    "current_item_name": f"Hachage Pack {tag}",
                    "created_at": time.strftime("%H:%M")
                })
        else: # Films
            tasks.append({
                "id": str(uuid.uuid4())[:8],
                "name": t['name'],
                "source_path": root_path,
                "type": "films",
                "lang_tag": t.get('lang_tag', 'MULTI'),
                "status": "running",
                "progress_item": 0,
                "current_item_name": "Hachage du film",
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
    # Si on cherche un fichier réel dans dist, on le sert
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    # Sinon on renvoie l'index (pour React Router)
    if os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return send_from_directory(app.static_folder, 'index.html')
    return "Frontend non compilé (dossier dist absent)", 404

if __name__ == '__main__':
    add_log("Démarrage de Torrent Factory V1.0.8", "info")
    # On s'assure que le dossier dist existe pour Flask
    if not os.path.exists('dist'): os.makedirs('dist')
    app.run(host='0.0.0.0', port=5000)