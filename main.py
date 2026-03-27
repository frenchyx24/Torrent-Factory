#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0 - Stable Build
Générateur NFO Professionnel (Mediainfo JSON + TMDb)
"""

import os
import json
import threading
import time
import uuid
import logging
import re
import subprocess
import requests
from guessit import guessit
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='dist')
CORS(app)

CONFIG_DIR = "/config" if os.path.exists("/config") else "config"
CONFIG_PATH = os.environ.get('CONFIG_PATH') or os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "http://tracker.example.com/announce",
    "private": True,
    "piece_size": 21, 
    "comment": "Torrent Factory V1.0 Stable",
    "language": "fr",
    "max_workers": 2,
    "enable_nfo": True,
    "tmdb_api_key": ""
}

tasks = []
logs_list = []
tasks_lock = threading.Lock()

def add_log(msg, level="info"):
    entry = {"id": str(uuid.uuid4()), "time": time.strftime("%H:%M:%S"), "msg": msg, "level": level}
    with tasks_lock:
        logs_list.append(entry)
        if len(logs_list) > 200: logs_list.pop(0)
    logger.info(f"[{level.upper()}] {msg}")

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

def fetch_tmdb_info(name, api_key):
    if not api_key: return None
    try:
        info = guessit(name)
        title = info.get('title', name)
        year = info.get('year')
        search_type = "tv" if info.get('type') == 'episode' else "movie"
        
        url = f"https://api.themoviedb.org/3/search/{search_type}?api_key={api_key}&query={title}"
        if year: url += f"&year={year}"
        
        res = requests.get(url, timeout=5).json()
        if res.get('results'):
            item_id = res['results'][0]['id']
            # Get full details
            details = requests.get(f"https://api.themoviedb.org/3/{search_type}/{item_id}?api_key={api_key}&language=fr-FR").json()
            return details
    except: pass
    return None

def generate_pro_nfo(source_path, dest_nfo_path, cfg):
    """Génère un NFO de qualité professionnelle avec Mediainfo et TMDb."""
    try:
        target = source_path
        if os.path.isdir(source_path):
            video_files = []
            for root, _, files in os.walk(source_path):
                for f in files:
                    if f.lower().endswith(('.mkv', '.mp4', '.avi', '.ts')):
                        video_files.append(os.path.join(root, f))
            if not video_files: return False
            target = video_files[0]

        add_log(f"Analyse Mediainfo pour {os.path.basename(target)}", "info")
        # On utilise JSON pour avoir un parsing fiable des flux
        result = subprocess.run(["mediainfo", "--Output=JSON", target], capture_output=True, text=True)
        if result.returncode != 0: return False
        
        mi_data = json.loads(result.stdout)
        tracks = mi_data.get('media', {}).get('track', [])
        
        # Récupération infos TMDb
        tmdb = fetch_tmdb_info(os.path.basename(source_path), cfg.get('tmdb_api_key'))
        
        nfo_content = "╔════════════════════════════════════════════════════════════════════════╗\n"
        nfo_content += f"║  TORRENT FACTORY V1.0 - PROFESSIONAL NFO GENERATOR                     ║\n"
        nfo_content += "╚════════════════════════════════════════════════════════════════════════╝\n\n"

        if tmdb:
            nfo_content += f" [ INFORMATIONS GÉNÉRALES ]\n"
            nfo_content += f" ❯ TITRE       : {tmdb.get('title') or tmdb.get('name')}\n"
            if tmdb.get('release_date') or tmdb.get('first_air_date'):
                nfo_content += f" ❯ ANNÉE       : {(tmdb.get('release_date') or tmdb.get('first_air_date'))[:4]}\n"
            if tmdb.get('genres'):
                nfo_content += f" ❯ GENRE       : {', '.join([g['name'] for g in tmdb['genres']])}\n"
            if tmdb.get('vote_average'):
                nfo_content += f" ❯ NOTE IMDb   : {tmdb['vote_average']}/10\n"
            if tmdb.get('overview'):
                nfo_content += f"\n [ SYNOPSIS ]\n {tmdb['overview']}\n"
            nfo_content += "\n" + "─" * 74 + "\n\n"

        # Analyse Technique via Mediainfo
        for track in tracks:
            t_type = track.get('@type')
            if t_type == 'General':
                nfo_content += " [ FICHIER ]\n"
                nfo_content += f" ❯ Format      : {track.get('Format')} / {track.get('FileSize_String')}\n"
                nfo_content += f" ❯ Durée       : {track.get('Duration_String3')}\n"
                nfo_content += f" ❯ Bitrate     : {track.get('OverallBitRate_String')}\n"
            elif t_type == 'Video':
                nfo_content += "\n [ VIDÉO ]\n"
                nfo_content += f" ❯ Codec       : {track.get('Format')} {track.get('Format_Profile', '')}\n"
                nfo_content += f" ❯ Résolution  : {track.get('Width')}x{track.get('Height')} ({track.get('DisplayAspectRatio_String')})\n"
                nfo_content += f" ❯ Frame Rate  : {track.get('FrameRate')} FPS\n"
                nfo_content += f" ❯ Bitrate     : {track.get('BitRate_String')}\n"
            elif t_type == 'Audio':
                nfo_content += f"\n [ AUDIO {track.get('StreamOrder', '')} ]\n"
                nfo_content += f" ❯ Langue      : {track.get('Language_String', 'Inconnu')}\n"
                nfo_content += f" ❯ Codec       : {track.get('Format')} {track.get('Format_Profile', '')}\n"
                nfo_content += f" ❯ Canaux      : {track.get('Channels')} ({track.get('ChannelLayout', '')})\n"
            elif t_type == 'Text':
                nfo_content += f"\n [ SOUS-TITRE ]\n"
                nfo_content += f" ❯ Langue      : {track.get('Language_String', 'Inconnu')} ({track.get('Format')})\n"

        with open(dest_nfo_path, "w", encoding="utf-8") as f:
            f.write(nfo_content)
        return True
    except Exception as e:
        add_log(f"Erreur NFO : {str(e)}", "error")
    return False

def process_single_task(task_id):
    cfg = load_config()
    t = None
    with tasks_lock:
        for item in tasks:
            if item['id'] == task_id:
                t = item
                break
    
    if not t or t['status'] != 'running': return

    try:
        out_dir = cfg['series_out'] if t['type'].lower() == 'series' else cfg['movies_out']
        os.makedirs(out_dir, exist_ok=True)
        
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', t['name'])
        base_filename = f"{safe_name} [{t['lang_tag']}]"
        dest_torrent = os.path.join(out_dir, f"{base_filename}.torrent")
        dest_nfo = os.path.join(out_dir, f"{base_filename}.nfo")

        if not os.path.exists(t['source_path']):
            raise Exception("Source introuvable")

        # 1. Génération du NFO (Priorité)
        if cfg.get('enable_nfo'):
            with tasks_lock: t['progress_item'] = 10
            generate_pro_nfo(t['source_path'], dest_nfo, cfg)

        # 2. Création du Torrent
        with tasks_lock: t['progress_item'] = 30
        cmd = ["mktorrent", "-a", cfg['tracker_url'], "-o", dest_torrent]
        if cfg.get('private'): cmd.append("-p")
        if cfg.get('comment'): cmd.extend(["-c", cfg['comment']])
        p_size = int(cfg.get('piece_size', 21))
        cmd.extend(["-l", str(max(15, min(28, p_size)))])
        cmd.append(t['source_path'])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        
        with tasks_lock:
            if result.returncode == 0:
                t['status'], t['progress_item'] = 'completed', 100
                add_log(f"Succès : {t['name']}", "success")
            else:
                t['status'] = 'cancelled'
                add_log(f"Erreur mktorrent {t['name']} : {result.stderr}", "error")
    except Exception as e:
        with tasks_lock: t['status'] = 'cancelled'
        add_log(f"Crash {t['name']} : {str(e)}", "error")

def worker_manager():
    add_log("Moteur Stable V1.0 Multi-thread activé", "info")
    last_workers_count = 0
    executor = None

    while True:
        cfg = load_config()
        current_max_workers = int(cfg.get('max_workers', 2))
        
        if current_max_workers != last_workers_count:
            if executor: executor.shutdown(wait=False)
            executor = ThreadPoolExecutor(max_workers=current_max_workers)
            last_workers_count = current_max_workers
            add_log(f"Configuration : {current_max_workers} tâches simultanées", "info")

        pending_tasks = []
        with tasks_lock:
            for t in tasks:
                if t['status'] == 'running' and t['progress_item'] == 0:
                    t['progress_item'] = 1 
                    pending_tasks.append(t['id'])
        
        for tid in pending_tasks:
            executor.submit(process_single_task, tid)
            
        time.sleep(2)

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'POST':
        new_cfg = request.json
        with open(CONFIG_PATH, 'w') as f:
            json.dump(new_cfg, f, indent=4)
        return jsonify(new_cfg)
    return jsonify(load_config())

@app.route('/api/library/<lib_type>')
def api_library(lib_type):
    cfg = load_config()
    root = cfg['series_root'] if lib_type == 'series' else cfg['movies_root']
    if not os.path.exists(root): return jsonify([])
    items = []
    try:
        for n in sorted(os.listdir(root)):
            if n.startswith('.'): continue
            full = os.path.join(root, n)
            items.append({"name": n, "size": "Scan...", "detected_tag": "MULTI"})
    except: pass
    return jsonify(items)

@app.route('/api/tasks/add', methods=['POST'])
def api_tasks_add():
    data, cfg = request.json, load_config()
    added = []
    with tasks_lock:
        for t in data.get('tasks', []):
            kind = data.get('type', 'series')
            base = cfg['series_root'] if kind == 'series' else cfg['movies_root']
            src = os.path.join(base, t['name'])
            new_task = {
                "id": str(uuid.uuid4())[:8], "name": t['name'], "source_path": src,
                "type": kind, "lang_tag": t.get('lang_tag', 'MULTI'),
                "status": "running", "progress_item": 0, "created_at": time.strftime("%H:%M")
            }
            tasks.append(new_task)
            added.append(new_task)
    return jsonify({"status": "ok", "added": added})

@app.route('/api/tasks/list')
def api_tasks_list():
    with tasks_lock: return jsonify(tasks)

@app.route('/api/tasks/clear')
def api_tasks_clear():
    global tasks
    with tasks_lock: tasks = [t for t in tasks if t['status'] == 'running']
    return jsonify({"status": "ok"})

@app.route('/api/logs')
def api_logs():
    with tasks_lock: return jsonify(logs_list)

@app.route('/api/drives')
def api_drives():
    return jsonify([{"name": "Système", "path": "/"}, {"name": "Données", "path": "/data"}])

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
    def gather(path):
        items = []
        if path and os.path.exists(path):
            for fn in sorted(os.listdir(path)):
                if not fn.endswith(('.torrent', '.nfo')): continue
                full = os.path.join(path, fn)
                try:
                    stat = os.stat(full)
                    items.append({'name': fn, 'path': full, 'size': stat.st_size, 'mtime': int(stat.st_mtime)})
                except: pass
        return items
    if cfg.get('series_out'): res['series'] = gather(cfg['series_out'])
    if cfg.get('movies_out'): res['movies'] = gather(cfg['movies_out'])
    return jsonify(res)

@app.route('/api/torrents/delete', methods=['POST'])
def api_torrents_delete():
    p = request.json.get('path')
    if p and os.path.exists(p):
        os.remove(p)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'not found'}), 404

@app.route('/api/torrents/download')
def api_torrents_download():
    p = request.args.get('path')
    if p and os.path.exists(p):
        return send_from_directory(os.path.dirname(p), os.path.basename(p), as_attachment=True)
    return "Not found", 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    threading.Thread(target=worker_manager, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)