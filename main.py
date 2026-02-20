#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0.8 - Edition Ultra-Robuste
"""

import os
import json
import threading
import time
import uuid
import sys
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Configuration des logs pour voir ce qu'il se passe dans Docker
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tentative d'import de torrent-tool
try:
    from torrent_tool import Torrent
    logger.info("Moteur torrent-tool chargé avec succès.")
except ImportError as e:
    logger.error(f"ERREUR CRITIQUE : Impossible de charger torrent-tool : {e}")
    Torrent = None

app = Flask(__name__, static_folder='dist')
CORS(app)

# Chemins de configuration
CONFIG_PATH = "/config/config.json"
# Fallback local si /config n'est pas monté dans Docker
if not os.path.exists("/config"):
    CONFIG_PATH = "config.json"

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
logs_list = []

def add_log(msg, level="info"):
    entry = {"id": str(uuid.uuid4()), "time": time.strftime("%H:%M:%S"), "msg": msg, "level": level}
    logs_list.append(entry)
    if level == "error": logger.error(msg)
    else: logger.info(msg)
    if len(logs_list) > 100: logs_list.pop(0)

def init_folders():
    """Crée tous les dossiers nécessaires au démarrage pour éviter les crashs."""
    folders = [
        "/config", "/data/series", "/data/movies", 
        "/data/torrents/series", "/data/torrents/movies", "dist"
    ]
    for folder in folders:
        try:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
                logger.info(f"Dossier créé : {folder}")
        except Exception as e:
            logger.error(f"Impossible de créer le dossier {folder} : {e}")

def load_config():
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config.update(json.load(f))
        except Exception as e:
            logger.warning(f"Impossible de lire la config : {e}")
    return config

def save_config(config):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        add_log(f"Erreur sauvegarde config : {e}", "error")

def get_readable_size(path):
    try:
        total = 0
        if os.path.isfile(path):
            total = os.path.getsize(path)
        else:
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    total += os.path.getsize(os.path.join(dirpath, f))
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if total < 1024: return f"{total:.2f} {unit}"
            total /= 1024
        return f"{total:.2f} PB"
    except: return "Inconnue"

def task_processor():
    """Boucle de traitement des tâches en arrière-plan."""
    while True:
        config = load_config()
        for t in tasks:
            if t['status'] == 'running' and t['progress_item'] == 0:
                t['progress_item'] = 5
                try:
                    if Torrent is None:
                        raise ImportError("Moteur de hachage indisponible")

                    out_dir = config['series_out'] if t['type'] == 'séries' else config['movies_out']
                    os.makedirs(out_dir, exist_ok=True)
                    
                    clean_name = re.sub(r'[\\/*?:"<>|]', '_', t['name'])
                    dest = os.path.join(out_dir, f"{clean_name} [{t['lang_tag']}].torrent")
                    
                    add_log(f"Démarrage hachage : {t['name']}", "info")
                    
                    # Création via torrent-tool
                    torrent = Torrent.create_from(t['source_path'])
                    torrent.announce_urls = [config['tracker_url']]
                    torrent.comment = config.get('comment', 'V1.0.8 Production')
                    torrent.is_private = config.get('private', True)
                    
                    ps = config.get('piece_size')
                    if ps: torrent.piece_size = int(ps)
                    
                    t['progress_item'] = 60
                    torrent.save(dest)
                    
                    t['status'] = 'completed'
                    t['progress_item'] = 100
                    t['progress_global'] = 100
                    add_log(f"Génération terminée avec succès : {t['name']}", "success")
                except Exception as e:
                    t['status'] = 'cancelled'
                    add_log(f"Erreur tâche {t['name']} : {str(e)}", "error")
        time.sleep(2)

# --- ROUTES API ---

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
    try:
        items = []
        for n in sorted(os.listdir(root)):
            path = os.path.join(root, n)
            items.append({"name": n, "size": get_readable_size(path), "detected_tag": "MULTI"})
        return jsonify(items)
    except Exception as e:
        return jsonify([])

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
            "current_item_name": "Calcul des pièces...",
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
def api_logs(): return jsonify(logs_list)

@app.route('/api/torrents/list')
def api_torrents():
    config = load_config()
    res = {"series": [], "movies": []}
    for k in ['series_out', 'movies_out']:
        p = config.get(k)
        if p and os.path.exists(p):
            try:
                res[k.split('_')[0]] = sorted([f for f in os.listdir(p) if f.endswith('.torrent')])
            except: pass
    return jsonify(res)

@app.route('/api/drives')
def api_drives():
    return jsonify([
        {"name": "Racine Docker", "path": "/"},
        {"name": "Config", "path": "/config"},
        {"name": "Séries", "path": "/data/series"},
        {"name": "Films", "path": "/data/movies"}
    ])

@app.route('/api/browse')
def api_browse():
    path = request.args.get('path', '/')
    try:
        if not os.path.exists(path):
            return jsonify({"current": path, "items": [], "error": "Chemin inexistant"})
        items = [{"name": n, "path": os.path.join(path, n)} for n in sorted(os.listdir(path)) if os.path.isdir(os.path.join(path, n))]
        return jsonify({"current": path, "items": items})
    except Exception as e:
        return jsonify({"current": path, "items": [], "error": str(e)})

# --- SERVEUR FRONTEND ---

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Si le fichier existe dans dist, on le sert
    full_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    
    # Sinon on sert index.html pour le routing React
    index_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, 'index.html')
    
    # Fallback si le frontend n'est pas encore prêt (évite le crash 404 brutal)
    return """
    <html>
        <body style="background:#0f172a;color:white;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;">
            <div style="text-align:center;">
                <h1>Torrent Factory V1.0.8</h1>
                <p>Le backend est prêt, mais le frontend est en cours de build...</p>
                <p>Veuillez rafraîchir la page dans quelques secondes.</p>
                <div style="width:40px;height:40px;border:4px solid #6366f1;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;margin:20px auto;"></div>
                <style>@keyframes spin { to { transform: rotate(360deg); } }</style>
            </div>
        </body>
    </html>
    """, 200

if __name__ == '__main__':
    init_folders()
    add_log("Démarrage du processeur de tâches...", "info")
    threading.Thread(target=task_processor, daemon=True).start()
    
    logger.info("Serveur Flask V1.0.8 démarré sur le port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)