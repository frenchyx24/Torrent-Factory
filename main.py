#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38.PRO - Full Functional Update
"""

import os
import json
import logging
import threading
import time
from pathlib import Path
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify

# ============================================================
# INITIALISATION
# ============================================================

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

# ============================================================
# CONFIGURATION ET STOCKAGE
# ============================================================

APP_DATA = Path(os.environ.get("TF_CONFIG_DIR", "/config"))
APP_DATA.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA / "config.json"
LIBRARY_FILE = APP_DATA / "library.json"

DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker_url": "",
    "private": True,
    "logs_max": 5000
}

def load_json(path, default):
    if not path.exists(): return default.copy()
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default.copy()

CONFIG = load_json(CONFIG_FILE, DEFAULT_CONFIG)
LIBRARY = load_json(LIBRARY_FILE, {"series": [], "movies": [], "torrents": [], "tasks": []})
web_logs = deque(maxlen=CONFIG.get("logs_max", 5000))
log_seq = 0

def log_system(msg, level="info"):
    global log_seq
    log_seq += 1
    web_logs.append({"id": log_seq, "time": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level})

def get_dir_size(path):
    total = 0
    try:
        p = Path(path)
        if p.is_file(): return p.stat().st_size
        for entry in os.scandir(path):
            if entry.is_file(): total += entry.stat().st_size
            elif entry.is_dir(): total += get_dir_size(entry.path)
    except: pass
    return total

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024: return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

# ============================================================
# MOTEUR DE TÂCHES (SIMULATION)
# ============================================================

def task_worker():
    while True:
        time.sleep(2)
        has_updates = False
        for task in LIBRARY["tasks"]:
            if task["status"] == "running":
                task["progress"] += 5
                if task["progress"] >= 100:
                    task["progress"] = 100
                    task["status"] = "completed"
                    log_system(f"Torrent créé avec succès : {task['name']}", "success")
                    # On ajoute aux torrents finis
                    LIBRARY["torrents"].insert(0, {
                        "name": task["name"] + ".torrent",
                        "type": task.get("type", "Inconnu"),
                        "date": datetime.now().strftime("%d/%m %H:%M")
                    })
                has_updates = True
        if has_updates:
            with open(LIBRARY_FILE, "w") as f: json.dump(LIBRARY, f)

threading.Thread(target=task_worker, daemon=True).start()

# ============================================================
# ROUTES API
# ============================================================

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        data = request.get_json() or {}
        CONFIG.update(data)
        with open(CONFIG_FILE, "w") as f: json.dump(CONFIG, f)
        return jsonify({"success": True})
    return jsonify(CONFIG)

@app.route("/api/scan/<type>", methods=["POST"])
def api_scan(type):
    root_path = CONFIG.get(f"{type}_root")
    p = Path(root_path)
    items = []
    if p.exists():
        for entry in p.iterdir():
            if entry.name.startswith('.'): continue
            size_raw = get_dir_size(entry)
            items.append({
                "name": entry.name,
                "size": format_size(size_raw),
                "path": str(entry)
            })
    LIBRARY[type] = sorted(items, key=lambda x: x['name'])
    log_system(f"Scan {type} terminé : {len(items)} éléments.", "info")
    return jsonify(LIBRARY[type])

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json() or {}
    items = data.get("items", [])
    type_media = data.get("type", "Série")
    
    for item in items:
        task_id = int(time.time() * 1000) + len(LIBRARY["tasks"])
        LIBRARY["tasks"].append({
            "id": task_id,
            "name": item["name"],
            "current": "Initialisation...",
            "progress": 0,
            "status": "running",
            "type": type_media
        })
        log_system(f"Lancement de la création : {item['name']}", "info")
    
    return jsonify({"success": True})

@app.route("/api/tasks/stop/<int:task_id>", methods=["POST"])
def stop_task(task_id):
    for task in LIBRARY["tasks"]:
        if task.get("id") == task_id:
            task["status"] = "cancelled"
            log_system(f"Tâche {task['name']} annulée", "warning")
            break
    return jsonify({"success": True})

@app.route("/api/tasks/clean", methods=["POST"])
def clean_tasks():
    LIBRARY["tasks"] = [t for t in LIBRARY["tasks"] if t.get("status") == "running"]
    return jsonify({"success": True})

@app.route("/api/library/<type>")
def get_library(type):
    return jsonify(LIBRARY.get(type, []))

@app.route("/api/logs")
def api_logs():
    return jsonify(list(web_logs))

@app.route("/")
def index():
    return PAGE_HTML

# ============================================================
# L'INTERFACE V38.PRO FINALE
# ============================================================

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Torrent Factory</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f172a;
            --sidebar-bg: rgba(15, 23, 42, 0.95);
            --glass: rgba(30, 41, 59, 0.6);
            --glass-border: rgba(255, 255, 255, 0.08);
            --accent: #6366f1;
            --text-main: #f8fafc;
            --text-mute: #94a3b8;
        }

        body {
            background-color: var(--bg-dark);
            background-image: radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 100%);
            font-family: 'Outfit', sans-serif;
            color: var(--text-main);
            height: 100vh;
            display: flex;
            overflow: hidden;
            margin: 0;
        }

        .sidebar {
            width: 280px;
            background: var(--sidebar-bg);
            backdrop-filter: blur(25px);
            border-right: 1px solid var(--glass-border);
            display: flex;
            flex-direction: column;
            padding: 30px 20px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 40px;
            color: white;
        }

        .brand i {
            background: var(--accent);
            width: 38px;
            height: 38px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 18px;
            color: var(--text-mute);
            text-decoration: none;
            border-radius: 12px;
            margin-bottom: 4px;
            cursor: pointer;
            transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .nav-item:hover, .nav-item.active {
            background: rgba(99, 102, 241, 0.1);
            color: var(--accent);
        }

        .nav-item.active { font-weight: 600; background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99,102,241,0.2); }

        .main-container { flex: 1; padding: 40px; overflow-y: auto; position: relative; }

        .glass-card {
            background: var(--glass);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .search-container { position: relative; margin-bottom: 25px; }
        .search-container i { position: absolute; left: 15px; top: 12px; color: var(--text-mute); }
        .search-container input { padding-left: 45px; height: 45px; border-radius: 12px; background: rgba(0,0,0,0.2); border: 1px solid var(--glass-border); color: white; width: 100%; }
        .search-container input:focus { border-color: var(--accent); outline: none; box-shadow: 0 0 0 3px rgba(99,102,241,0.2); }

        .table { color: var(--text-main) !important; background: transparent !important; margin: 0; }
        .table thead th { border-bottom: 1px solid var(--glass-border) !important; color: var(--text-mute) !important; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; padding-bottom: 15px; }
        .table td { border-bottom: 1px solid rgba(255,255,255,0.03) !important; vertical-align: middle; padding: 18px 10px; color: white !important; font-size: 0.95rem; }
        
        .badge-size { background: rgba(99, 102, 241, 0.1); color: var(--accent); font-family: monospace; font-size: 0.75rem; border: 1px solid rgba(99, 102, 241, 0.2); }

        .btn-accent { background: var(--accent); border: none; color: white; padding: 10px 24px; border-radius: 12px; font-weight: 600; transition: 0.3s; }
        .btn-accent:hover { background: #4f46e5; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(99, 102, 241, 0.4); }
        .btn-accent:disabled { background: var(--text-mute); opacity: 0.5; transform: none; }

        .btn-zap { color: #f59e0b; font-size: 1.2rem; transition: 0.2s; }
        .btn-zap:hover { color: #fbbf24; transform: scale(1.2); }

        .progress { background: rgba(255,255,255,0.05); height: 6px; border-radius: 10px; }
        .progress-bar { background: var(--accent); border-radius: 10px; transition: 1s ease-in-out; }

        .log-line { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; gap: 15px; }
        .log-time { color: var(--text-mute); width: 80px; }
        .log-info { color: #cbd5e1; }
        .log-success { color: #10b981; }
        .log-warning { color: #f59e0b; }
        .log-error { color: #ef4444; }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="brand"><i class="bi bi-zap-fill"></i><span>Torrent Factory</span></div>
        <div class="nav-group flex-grow-1">
            <div class="nav-item active" onclick="switchView('series')" id="nav-series"><i class="bi bi-tv"></i> Séries</div>
            <div class="nav-item" onclick="switchView('movies')" id="nav-movies"><i class="bi bi-film"></i> Films</div>
            <div class="nav-item" onclick="switchView('torrents')" id="nav-torrents"><i class="bi bi-folder-check"></i> Torrents</div>
            <div class="nav-item" onclick="switchView('tasks')" id="nav-tasks"><i class="bi bi-activity"></i> Tâches</div>
            <div class="nav-item" onclick="switchView('logs')" id="nav-logs"><i class="bi bi-terminal"></i> Logs</div>
        </div>
        <div class="nav-item" onclick="switchView('settings')" id="nav-settings"><i class="bi bi-gear"></i> Réglages</div>
    </div>

    <div class="main-container">
        <!-- SERIES -->
        <div id="view-series" class="view-section">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div><h2>Bibliothèque Séries</h2><p class="text-mute small">Génération intelligente par packs ou épisodes.</p></div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-light btn-sm px-3" onclick="scan('series')"><i class="bi bi-arrow-clockwise me-2"></i>Scanner</button>
                    <button class="btn btn-accent btn-sm" onclick="massGenerate('series')"><i class="bi bi-layers me-2"></i>Tout Générer</button>
                </div>
            </div>
            <div class="search-container">
                <i class="bi bi-search"></i>
                <input type="text" id="search-series" placeholder="Rechercher une série..." onkeyup="filterList('series')">
            </div>
            <div class="glass-card p-0 overflow-hidden">
                <table class="table">
                    <thead><tr><th width="40" class="ps-4"><input type="checkbox" class="form-check-input" onclick="toggleAll('series', this)"></th><th>Nom</th><th>Langue</th><th>Mode</th><th class="text-end pe-4">Action</th></tr></thead>
                    <tbody id="list-series"></tbody>
                </table>
            </div>
        </div>

        <!-- MOVIES -->
        <div id="view-movies" class="view-section" style="display:none">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Bibliothèque Films</h2>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-light btn-sm px-3" onclick="scan('movies')"><i class="bi bi-search me-2"></i>Scanner</button>
                    <button class="btn btn-accent btn-sm" onclick="massGenerate('movies')"><i class="bi bi-play-fill me-2"></i>Tout Générer</button>
                </div>
            </div>
            <div class="search-container">
                <i class="bi bi-search"></i>
                <input type="text" id="search-movies" placeholder="Rechercher un film..." onkeyup="filterList('movies')">
            </div>
            <div class="glass-card p-0 overflow-hidden">
                <table class="table">
                    <thead><tr><th width="40" class="ps-4"><input type="checkbox" class="form-check-input" onclick="toggleAll('movies', this)"></th><th>Nom</th><th>Taille</th><th>Langue</th><th class="text-end pe-4">Action</th></tr></thead>
                    <tbody id="list-movies"></tbody>
                </table>
            </div>
        </div>

        <!-- TORRENTS -->
        <div id="view-torrents" class="view-section" style="display:none">
            <div class="d-flex justify-content-between align-items-center mb-4"><h2>Torrents Créés</h2></div>
            <div class="glass-card p-0 overflow-hidden">
                <table class="table">
                    <thead><tr><th class="ps-4">Fichier</th><th>Catégorie</th><th>Date</th><th class="text-end pe-4">Actions</th></tr></thead>
                    <tbody id="list-torrents"></tbody>
                </table>
            </div>
        </div>

        <!-- TASKS -->
        <div id="view-tasks" class="view-section" style="display:none">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Activités en cours</h2>
                <button class="btn btn-outline-danger btn-sm" onclick="cleanTasks()"><i class="bi bi-trash3 me-2"></i>Nettoyer</button>
            </div>
            <div id="list-tasks"></div>
        </div>

        <!-- LOGS -->
        <div id="view-logs" class="view-section" style="display:none">
            <div class="mb-4"><h2>Logs Système</h2></div>
            <div class="glass-card bg-black p-4" style="height: 550px; overflow-y: auto; border: 1px solid rgba(255,255,255,0.1);" id="log-output"></div>
        </div>

        <!-- SETTINGS -->
        <div id="view-settings" class="view-section" style="display:none">
            <div class="mb-4"><h2>Configuration</h2></div>
            <div class="row g-4">
                <div class="col-md-6">
                    <div class="glass-card h-100">
                        <h5 class="mb-3 text-accent"><i class="bi bi-folder"></i> Chemins</h5>
                        <div class="row g-3">
                            <div class="col-12"><label class="form-label text-mute small">Séries (Source)</label><input type="text" id="cfg-series-root" class="form-control"></div>
                            <div class="col-12"><label class="form-label text-mute small">Séries (Destination)</label><input type="text" id="cfg-series-out" class="form-control"></div>
                            <hr class="opacity-10 my-1">
                            <div class="col-12"><label class="form-label text-mute small">Films (Source)</label><input type="text" id="cfg-movies-root" class="form-control"></div>
                            <div class="col-12"><label class="form-label text-mute small">Films (Destination)</label><input type="text" id="cfg-movies-out" class="form-control"></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="glass-card h-100">
                        <h5 class="mb-3 text-accent"><i class="bi bi-gear"></i> Options</h5>
                        <div class="mb-3"><label class="form-label text-mute small">Tracker Announce URL</label><input type="text" id="cfg-tracker" class="form-control"></div>
                        <div class="mb-3"><label class="form-label text-mute small">Historique (lignes)</label><input type="number" id="cfg-logs-max" class="form-control"></div>
                        <div class="form-check form-switch mt-4 p-3 bg-white/5 rounded-3">
                            <input class="form-check-input ms-0 me-3" type="checkbox" id="cfg-private">
                            <label class="form-check-label">Flag Private (Torrents)</label>
                        </div>
                    </div>
                </div>
            </div>
            <button class="btn btn-accent w-100 py-3 mt-4" onclick="saveConfig()"><i class="bi bi-save me-2"></i>ENREGISTRER LA CONFIGURATION</button>
        </div>
    </div>

    <script>
        let currentData = { series: [], movies: [] };

        function switchView(viewId) {
            document.querySelectorAll('.view-section').forEach(s => s.style.display = 'none');
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            document.getElementById('view-' + viewId).style.display = 'block';
            document.getElementById('nav-' + viewId).classList.add('active');
            if(viewId === 'logs') fetchLogs();
            if(['series','movies','torrents','tasks'].includes(viewId)) loadLibrary(viewId);
        }

        async function loadConfig() {
            const res = await fetch('/api/config');
            const cfg = await res.json();
            document.getElementById('cfg-series-root').value = cfg.series_root;
            document.getElementById('cfg-series-out').value = cfg.series_out;
            document.getElementById('cfg-movies-root').value = cfg.movies_root;
            document.getElementById('cfg-movies-out').value = cfg.movies_out;
            document.getElementById('cfg-tracker').value = cfg.tracker_url || '';
            document.getElementById('cfg-logs-max').value = cfg.logs_max;
            document.getElementById('cfg-private').checked = cfg.private;
        }

        async function saveConfig() {
            const data = {
                series_root: document.getElementById('cfg-series-root').value,
                series_out: document.getElementById('cfg-series-out').value,
                movies_root: document.getElementById('cfg-movies-root').value,
                movies_out: document.getElementById('cfg-movies-out').value,
                tracker_url: document.getElementById('cfg-tracker').value,
                logs_max: parseInt(document.getElementById('cfg-logs-max').value),
                private: document.getElementById('cfg-private').checked
            };
            await fetch('/api/config', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
            alert('Configuration enregistrée !');
        }

        async function scan(type) {
            await fetch('/api/scan/' + type, {method: 'POST'});
            loadLibrary(type);
        }

        async function loadLibrary(type) {
            const res = await fetch('/api/library/' + type);
            const data = await res.json();
            currentData[type] = data;
            renderList(type, data);
        }

        function renderList(type, data) {
            const container = document.getElementById('list-' + type);
            if(!container) return;

            if(type === 'tasks') {
                container.innerHTML = data.length ? data.map(t => `
                    <div class="glass-card mb-3 border-start border-4 border-${t.status === 'completed' ? 'success' : (t.status === 'running' ? 'primary' : 'warning')}">
                        <div class="d-flex justify-content-between mb-2">
                            <div><div class="fw-bold">${t.name}</div><small class="text-mute">${t.current} (${t.type})</small></div>
                            ${t.status === 'running' ? `<button onclick="stopTask(${t.id})" class="btn btn-sm btn-outline-danger border-0"><i class="bi bi-x-circle"></i></button>` : `<span class="badge bg-${t.status === 'completed' ? 'success' : 'warning'}">${t.status.toUpperCase()}</span>`}
                        </div>
                        <div class="progress"><div class="progress-bar" style="width:${t.progress}%"></div></div>
                    </div>`).join('') : '<div class="text-center py-5 text-mute">Aucune activité en cours.</div>';
            } else if(type === 'torrents') {
                container.innerHTML = data.length ? data.map(t => `<tr><td class="ps-4 fw-bold">${t.name}</td><td><span class="badge bg-white/5 text-mute">${t.type}</span></td><td>${t.date}</td><td class="text-end pe-4"><button class="btn btn-sm btn-link text-white"><i class="bi bi-folder2-open"></i></button></td></tr>`).join('') : '<tr><td colspan="4" class="text-center py-5 text-mute">Aucun torrent généré.</td></tr>';
            } else {
                container.innerHTML = data.length ? data.map((item, i) => `
                    <tr id="row-${type}-${i}">
                        <td class="ps-4"><input type="checkbox" class="form-check-input check-${type}" data-index="${i}"></td>
                        <td><div class="fw-bold text-white">${item.name}</div><span class="badge badge-size">${item.size}</span></td>
                        <td><select class="form-select form-select-sm w-auto"><option>MULTI</option><option>FRENCH</option><option>VOSTFR</option></select></td>
                        ${type === 'series' ? '<td><select class="form-select form-select-sm w-auto"><option>Pack</option><option>Saison</option><option>EP</option></select></td>' : ''}
                        <td class="text-end pe-4"><button class="btn btn-link btn-zap" onclick="singleGenerate('${type}', ${i})"><i class="bi bi-zap-fill"></i></button></td>
                    </tr>`).join('') : '<tr><td colspan="5" class="text-center py-5 text-mute">Dossier vide. Cliquez sur Scanner.</td></tr>';
            }
        }

        function filterList(type) {
            const query = document.getElementById('search-' + type).value.toLowerCase();
            const filtered = currentData[type].filter(item => item.name.toLowerCase().includes(query));
            renderList(type, filtered);
        }

        function toggleAll(type, el) {
            document.querySelectorAll('.check-' + type).forEach(c => c.checked = el.checked);
        }

        async function singleGenerate(type, index) {
            const item = currentData[type][index];
            await fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ items: [item], type: type === 'series' ? 'Série' : 'Film' })
            });
            switchView('tasks');
        }

        async function massGenerate(type) {
            const selected = [];
            document.querySelectorAll('.check-' + type + ':checked').forEach(c => {
                selected.push(currentData[type][c.dataset.index]);
            });
            if(!selected.length) return alert('Sélectionnez au moins un élément !');
            
            await fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ items: selected, type: type === 'series' ? 'Série' : 'Film' })
            });
            switchView('tasks');
        }

        async function cleanTasks() { await fetch('/api/tasks/clean', {method: 'POST'}); loadLibrary('tasks'); }
        async function stopTask(id) { await fetch('/api/tasks/stop/' + id, {method: 'POST'}); loadLibrary('tasks'); }

        async function fetchLogs() {
            const res = await fetch('/api/logs');
            const logs = await res.json();
            const out = document.getElementById('log-output');
            out.innerHTML = logs.map(l => `<div class="log-line"><span class="log-time">${l.time}</span><span class="log-${l.level}">${l.msg}</span></div>`).join('');
            out.scrollTop = out.scrollHeight;
        }

        window.onload = () => { loadConfig(); loadLibrary('series'); setInterval(() => { if(document.getElementById('view-tasks').style.display === 'block') loadLibrary('tasks'); }, 3000); };
    </script>
</body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)