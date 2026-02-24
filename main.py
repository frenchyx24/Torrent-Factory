#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory v1.0.11-test - Corrections, fiabilisations et améliorations
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
import shutil
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='dist')
CORS(app)

# Résolution du chemin de configuration : variable d'env > /config/config.json > ./config/config.json > config.json
CONFIG_PATH = os.environ.get('CONFIG_PATH') or '/config/config.json'
if not os.path.exists(CONFIG_PATH):
    if os.path.exists('/config/config.json'):
        CONFIG_PATH = '/config/config.json'
    elif os.path.exists('config/config.json'):
        CONFIG_PATH = 'config/config.json'
    else:
        CONFIG_PATH = 'config.json'

DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "http://tracker.example.com/announce",
    "private": True,
    "piece_size": 21, # 2^21 = 2MB (mktorrent utilise des puissances de 2)
    "comment": "Torrent Factory v1.0.11-test",
    "language": "fr"
}

tasks = []
logs_list = []
tasks_lock = threading.Lock()


def _tasks_file_path():
    cfg_path = CONFIG_PATH or 'config.json'
    cfg_dir = os.path.dirname(cfg_path) or '.'
    return os.path.join(cfg_dir, 'tasks.json')


def load_tasks():
    global tasks
    path = _tasks_file_path()
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                tasks = json.load(f)
    except Exception:
        logger.exception('Failed to load tasks file')


def save_tasks():
    path = _tasks_file_path()
    try:
        with open(path, 'w') as f:
            json.dump(tasks, f, indent=2)
    except Exception:
        logger.exception('Failed to save tasks file')

def add_log(msg, level="info"):
    logs_list.append({"id": str(uuid.uuid4()), "time": time.strftime("%H:%M:%S"), "msg": msg, "level": level})
    if len(logs_list) > 200:
        logs_list.pop(0)

def init_folders():
    for f in ["/config", "config", "/data/series", "/data/movies", "/data/torrents/series", "/data/torrents/movies", "dist"]:
        try:
            os.makedirs(f, exist_ok=True)
        except Exception:
            pass

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
                    # Normaliser le type de tâche pour éviter les variantes 'séries'/'series'
                    kind = t.get('type', '')
                    if kind.lower() in ('séries', 'series', 'serie'):
                        out = cfg.get('series_out')
                    else:
                        out = cfg.get('movies_out')
                    os.makedirs(out, exist_ok=True)
                    name = re.sub(r'[\\/*?:"<>|]', '_', t['name'])
                    dest = os.path.join(out, f"{name} [{t['lang_tag']}].torrent")
                    
                    # Construction de la commande mktorrent
                    # -p : privé, -a : tracker, -o : output, -c : commentaire, -l : piece size
                    cmd = ["mktorrent", "-a", cfg['tracker_url'], "-o", dest]
                    if cfg.get('private'): cmd.append("-p")
                    if cfg.get('comment'): cmd.extend(["-c", cfg['comment']])
                    # mktorrent attend une puissance de 2 pour la taille des pièces (ex: 21 pour 2MB)
                    # On simplifie ici pour la v1.0.11
                    cmd.append(t['source_path'])
                    
                    # Vérifier que mktorrent est disponible
                    if not shutil.which('mktorrent'):
                        raise Exception('mktorrent not found in PATH')

                    logger.info(f"Execution: {' '.join(cmd)}")
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    except subprocess.TimeoutExpired:
                        raise Exception('mktorrent timeout')

                    if result.returncode == 0:
                        t['status'], t['progress_item'] = 'completed', 100
                        add_log(f"Succès: {name}", "success")
                    else:
                        stderr = (result.stderr or '').strip()
                        raise Exception(stderr or "Erreur mktorrent")
                        
                except Exception as e:
                    t['status'] = 'cancelled'
                    add_log(f"Erreur: {str(e)}", "error")
                finally:
                    # sauvegarder l'état des tâches après chaque tentative
                    try:
                        with tasks_lock:
                            save_tasks()
                    except Exception:
                        logger.exception('Failed saving tasks in loop')
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


def _scan_root(root):
    items = []
    try:
        if not root or not os.path.exists(root):
            return items
        for name in sorted(os.listdir(root)):
            full = os.path.join(root, name)
            if os.path.isdir(full):
                items.append({
                    'name': name,
                    'size': get_readable_size(full),
                    'detected_tag': 'MULTI'
                })
    except Exception as e:
        logger.exception('scan error: %s', e)
    return items


@app.route('/api/scan/series', methods=['POST'])
def api_scan_series():
    cfg = load_config()
    root = cfg.get('series_root')
    items = _scan_root(root)
    add_log(f"Scan séries exécuté: {len(items)} items", 'info')
    return jsonify({'status': 'ok', 'items': items})


@app.route('/api/scan/movies', methods=['POST'])
def api_scan_movies():
    cfg = load_config()
    root = cfg.get('movies_root')
    items = _scan_root(root)
    add_log(f"Scan films exécuté: {len(items)} items", 'info')
    return jsonify({'status': 'ok', 'items': items})

@app.route('/api/tasks/add', methods=['POST'])
def api_tasks_add():
    d = request.json or {}
    cfg = load_config()
    tasks_added = []
    raw_type = (d.get('type') or '').lower()
    if raw_type in ('séries', 'series', 'serie'):
        kind = 'series'
        base_root = cfg.get('series_root')
    else:
        kind = 'movies'
        base_root = cfg.get('movies_root')

    incoming = d.get('tasks') or []
    if not isinstance(incoming, list) or len(incoming) == 0:
        return jsonify({'error': 'no tasks provided'}), 400

    with tasks_lock:
        for t in incoming:
            name = t.get('name')
            if not name or not isinstance(name, str):
                continue
            src = os.path.join(base_root or '', name)
            new_task = {
                'id': str(uuid.uuid4())[:8],
                'name': name,
                'source_path': src,
                'type': kind,
                'lang_tag': t.get('lang_tag', 'MULTI'),
                'status': 'running',
                'progress_item': 0,
                'created_at': time.strftime('%H:%M')
            }
            tasks.append(new_task)
            tasks_added.append(new_task)
        try:
            save_tasks()
        except Exception:
            logger.exception('Failed to save tasks after add')

    add_log(f"Ajouté {len(tasks_added)} tâche(s)", 'info')
    return jsonify({'status': 'ok', 'added': tasks_added})

@app.route('/api/tasks/list')
def api_tasks_list():
    with tasks_lock:
        return jsonify(tasks)


@app.route('/api/tasks/<task_id>')
def api_tasks_get(task_id):
    for t in tasks:
        if t.get('id') == task_id:
            return jsonify(t)
    return jsonify({'error': 'not found'}), 404


@app.route('/api/tasks/retry', methods=['POST'])
def api_tasks_retry():
    data = request.json or {}
    tid = data.get('id')
    if not tid:
        return jsonify({'error': 'missing id'}), 400
    with tasks_lock:
        for t in tasks:
            if t.get('id') == tid:
                t['status'] = 'running'
                t['progress_item'] = 0
                try:
                    save_tasks()
                except Exception:
                    logger.exception('Failed save tasks on retry')
                return jsonify({'status': 'ok'})
    return jsonify({'error': 'not found'}), 404


@app.route('/api/tasks/delete', methods=['POST'])
def api_tasks_delete():
    data = request.json or {}
    tid = data.get('id')
    if not tid:
        return jsonify({'error': 'missing id'}), 400
    with tasks_lock:
        global tasks
        ntasks = [t for t in tasks if t.get('id') != tid]
        if len(ntasks) == len(tasks):
            return jsonify({'error': 'not found'}), 404
        tasks = ntasks
        try:
            save_tasks()
        except Exception:
            logger.exception('Failed save tasks on delete')
    return jsonify({'status': 'ok'})

@app.route('/api/tasks/clear')
def api_tasks_clear():
    global tasks
    with tasks_lock:
        tasks = [t for t in tasks if t['status'] == 'running']
        try:
            save_tasks()
        except Exception:
            logger.exception('Failed to save tasks after clear')
    return jsonify({"status": "ok"})

@app.route('/api/logs')
def api_logs(): return jsonify(logs_list)


@app.route('/api/health')
def api_health():
    ok = True
    missing = []
    if not shutil.which('mktorrent'):
        ok = False
        missing.append('mktorrent')
    return jsonify({'ok': ok, 'missing': missing})

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
        series_path = cfg.get('series_out') or ''
        movies_path = cfg.get('movies_out') or ''

        seen = set()

        def gather(path):
            items = []
            if not path or not os.path.exists(path):
                return items
            for fn in sorted(os.listdir(path)):
                if not fn.endswith('.torrent'): continue
                if fn in seen: continue
                full = os.path.join(path, fn)
                if not os.path.isfile(full): continue
                seen.add(fn)
                stat = os.stat(full)
                items.append({
                    'name': fn,
                    'path': full,
                    'size': stat.st_size,
                    'mtime': int(stat.st_mtime)
                })
            return items

        res['series'] = gather(series_path)
        res['movies'] = gather(movies_path)
    except Exception as e:
        logger.exception('Erreur listing torrents: %s', e)
    return jsonify(res)


def _is_within_allowed(path, allowed_dirs):
    try:
        path = os.path.realpath(path)
        for d in allowed_dirs:
            if not d: continue
            if os.path.commonpath([path, os.path.realpath(d)]) == os.path.realpath(d):
                return True
    except Exception:
        return False
    return False


@app.route('/api/torrents/download')
def api_torrents_download():
    p = request.args.get('path')
    if not p: return jsonify({'error': 'missing path'}), 400
    cfg = load_config()
    allowed = [cfg.get('series_out'), cfg.get('movies_out')]
    if not _is_within_allowed(p, allowed):
        return jsonify({'error': 'forbidden'}), 403
    if not os.path.exists(p) or not os.path.isfile(p):
        return jsonify({'error': 'not found'}), 404
    # send file
    dirn, fname = os.path.split(p)
    return send_from_directory(dirn, fname, as_attachment=True)


@app.route('/api/torrents/delete', methods=['POST'])
def api_torrents_delete():
    data = request.json or {}
    p = data.get('path')
    if not p: return jsonify({'error': 'missing path'}), 400
    cfg = load_config()
    allowed = [cfg.get('series_out'), cfg.get('movies_out')]
    if not _is_within_allowed(p, allowed):
        return jsonify({'error': 'forbidden'}), 403
    try:
        if os.path.exists(p) and os.path.isfile(p):
            os.remove(p)
            return jsonify({'status': 'ok'})
        return jsonify({'error': 'not found'}), 404
    except Exception as e:
        logger.exception('Erreur suppression torrent: %s', e)
        return jsonify({'error': 'failed'}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    fp = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(fp): return send_from_directory(app.static_folder, path)
    idx = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(idx): return send_from_directory(app.static_folder, 'index.html')
    return "<h1>v1.0.11-test</h1><p>Build frontend requis.</p>", 200

if __name__ == '__main__':
    init_folders()
    load_tasks()
    threading.Thread(target=task_processor, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)