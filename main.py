#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.1.0 - The Golden Build
"""

import os
import json
import threading
import time
import uuid
import logging
import re
import subprocess
import shutil
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='dist')
CORS(app)

# Détermination du chemin de config
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
    "comment": "Torrent Factory V1.1.0",
    "language": "fr"
}

tasks = []
logs_list = []
tasks_lock = threading.Lock()

def add_log(msg, level="info"):
    entry = {"id": str(uuid.uuid4()), "time": time.strftime("%H:%M:%S"), "msg": msg, "level": level}
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

def get_readable_size(path):
    try:
        total = 0
        if os.path.isfile(path):
            total = os.path.getsize(path)
        else:
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if total < 1024:
                return f"{total:.2f} {unit}"
            total /= 1024
    except:
        return "Unknown"

def task_processor():
    while True:
        cfg = load_config()
        with tasks_lock:
            for t in tasks:
                if t['status'] == 'running' and t['progress_item'] == 0:
                    t['progress_item'] = 10
                    try:
                        out_dir = cfg['series_out'] if t['type'].lower() in ('series', 'séries') else cfg['movies_out']
                        os.makedirs(out_dir, exist_ok=True)
                        safe_name = re.sub(r'[\\/*?:"<>|]', '_', t['name'])
                        dest_path = os.path.join(out_dir, f"{safe_name} [{t['lang_tag']}].torrent")
                        
                        cmd = ["mktorrent", "-a", cfg['tracker_url'], "-o", dest_path]
                        if cfg.get('private'): cmd.append("-p")
                        if cfg.get('comment'): cmd.extend(["-c", cfg['comment']])
                        cmd.extend(["-l", str(cfg.get('piece_size', 21))])
                        cmd.append(t['source_path'])
                        
                        t['progress_item'] = 40
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                        
                        if result.returncode == 0:
                            t['status'], t['progress_item'] = 'completed', 100
                            add_log(f"Succès : {safe_name}", "success")
                        else:
                            raise Exception(result.stderr or "Erreur mktorrent")
                    except Exception as e:
                        t['status'] = 'cancelled'
                        add_log(f"Erreur {t['name']} : {str(e)}", "error")
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
    for n in sorted(os.listdir(root)):
        if n.startswith('.'): continue
        full = os.path.join(root, n)
        items.append({"name": n, "size": get_readable_size(full), "detected_tag": "MULTI"})
    return jsonify(items)

@app.route('/api/scan/<lib_type>', methods=['POST'])
def api_scan(lib_type):
    return api_library(lib_type)

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
    return jsonify(tasks)

@app.route('/api/tasks/cancel', methods=['POST'])
def api_tasks_cancel():
    tid = request.json.get('id')
    with tasks_lock:
        for t in tasks:
            if t['id'] == tid:
                t['status'] = 'cancelled'
                return jsonify({'status': 'ok'})
    return jsonify({'error': 'not found'}), 404

@app.route('/api/tasks/clear')
def api_tasks_clear():
    global tasks
    with tasks_lock:
        tasks = [t for t in tasks if t['status'] == 'running']
    return jsonify({"status": "ok"})

@app.route('/api/logs')
def api_logs():
    return jsonify(logs_list)

@app.route('/api/drives')
def api_drives():
    return jsonify([{"name": "Système", "path": "/"}, {"name": "Données", "path": "/data"}])

@app.route('/api/browse')
def api_browse():
    p = request.args.get('path', '/')
    try:
        items = [{"name": n, "path": os.path.join(p, n)} for n in sorted(os.listdir(p)) if os.path.isdir(os.path.join(p, n))]
        return jsonify({"current": p, "items": items})
    except:
        return jsonify({"current": p, "items": []})

@app.route('/api/torrents/list')
def api_torrents_list():
    cfg = load_config()
    res = {"series": [], "movies": []}
    def gather(path):
        items = []
        if path and os.path.exists(path):
            for fn in sorted(os.listdir(path)):
                if not fn.endswith('.torrent'): continue
                full = os.path.join(path, fn)
                stat = os.stat(full)
                items.append({'name': fn, 'path': full, 'size': stat.st_size, 'mtime': int(stat.st_mtime)})
        return items
    res['series'] = gather(cfg.get('series_out'))
    res['movies'] = gather(cfg.get('movies_out'))
    return jsonify(res)

@app.route('/api/torrents/delete', methods=['POST'])
def api_torrents_delete():
    p = request.json.get('path')
    if p and os.path.exists(p):
        os.remove(p)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'not found'}), 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    threading.Thread(target=task_processor, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)