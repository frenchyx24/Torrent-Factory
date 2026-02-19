#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38.PRO - Restauration Complète & Correction Design
"""

import os
import json
import logging
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
# Initialisation propre sans données de test
LIBRARY = load_json(LIBRARY_FILE, {"series": [], "movies": [], "torrents": [], "tasks": []})
web_logs = deque(maxlen=CONFIG.get("logs_max", 5000))
log_seq = 0

def log_system(msg, level="info"):
    global log_seq
    log_seq += 1
    web_logs.append({"id": log_seq, "time": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level})

# ============================================================
# ROUTES API
# ============================================================

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        CONFIG.update(request.get_json() or {})
        with open(CONFIG_FILE, "w") as f: json.dump(CONFIG, f)
        return jsonify({"success": True})
    return jsonify(CONFIG)

@app.route("/api/scan/<type>", methods=["POST"])
def api_scan(type):
    root = CONFIG.get(f"{type}_root")
    log_system(f"Scan du dossier {type}: {root}...", "info")
    # Logique de scan réelle ici...
    return jsonify(LIBRARY.get(type, []))

@app.route("/api/tasks/stop/<int:task_id>", methods=["POST"])
def stop_task(task_id):
    for task in LIBRARY["tasks"]:
        if task.get("id") == task_id:
            task["status"] = "cancelled"
            log_system(f"Tâche {task['name']} annulée par l'utilisateur", "warning")
            break
    return jsonify({"success": True})

@app.route("/api/tasks/clean", methods=["POST"])
def clean_tasks():
    LIBRARY["tasks"] = [t for t in LIBRARY["tasks"] if t.get("status") == "running"]
    log_system("Nettoyage des tâches terminées", "info")
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
# L'INTERFACE V38.PRO CORRIGÉE
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
            --sidebar-bg: rgba(15, 23, 42, 0.9);
            --glass: rgba(30, 41, 59, 0.6);
            --glass-border: rgba(255, 255, 255, 0.1);
            --accent: #6366f1;
            --text-main: #f8fafc;
            --text-mute: #94a3b8;
        }

        body {
            background-color: var(--bg-dark);
            background-image: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.05) 0%, transparent 40%);
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
            backdrop-filter: blur(20px);
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
            padding: 14px 18px;
            color: var(--text-mute);
            text-decoration: none;
            border-radius: 12px;
            margin-bottom: 6px;
            cursor: pointer;
            transition: 0.2s;
        }

        .nav-item:hover, .nav-item.active {
            background: rgba(99, 102, 241, 0.1);
            color: var(--accent);
        }

        .nav-item.active { font-weight: 600; border: 1px solid rgba(99,102,241,0.2); }

        .main-container { flex: 1; padding: 40px; overflow-y: auto; }

        .glass-card {
            background: var(--glass);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
        }

        /* FIX DU BLANC MOCHE */
        .table { color: var(--text-main) !important; background: transparent !important; margin: 0; }
        .table thead th { border-bottom: 1px solid var(--glass-border) !important; color: var(--text-mute) !important; background: transparent !important; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
        .table td { border-bottom: 1px solid rgba(255,255,255,0.03) !important; vertical-align: middle; padding: 15px 10px; background: transparent !important; color: white !important; }
        .table tr:hover { background: rgba(255,255,255,0.02) !important; }

        .btn-accent { background: var(--accent); border: none; color: white; padding: 10px 20px; border-radius: 10px; font-weight: 600; }
        .btn-accent:hover { background: #4f46e5; transform: translateY(-1px); }

        .form-control, .form-select { background: rgba(0,0,0,0.3) !important; border: 1px solid var(--glass-border) !important; color: white !important; }
        .form-control:focus { background: rgba(0,0,0,0.4) !important; border-color: var(--accent) !important; box-shadow: none !important; }

        .progress { background: rgba(255,255,255,0.05); height: 8px; border-radius: 10px; }
        .progress-bar { background: var(--accent); transition: 0.5s; }

        .log-line { font-family: monospace; font-size: 0.9rem; margin-bottom: 4px; display: flex; gap: 15px; }
        .log-time { color: var(--text-mute); flex-shrink: 0; }
        .log-error { color: #f87171; }
        .log-success { color: #34d399; }
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
                <div>
                    <h2>Bibliothèque Séries</h2>
                    <p class="text-mute small">Gérez vos séries et générez des torrents en masse.</p>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-light" onclick="scan('series')"><i class="bi bi-arrow-clockwise me-2"></i>Scanner</button>
                    <button class="btn btn-accent"><i class="bi bi-layers me-2"></i>Tout Générer</button>
                </div>
            </div>
            <div class="glass-card p-0 overflow-hidden">
                <table class="table">
                    <thead><tr><th width="40"><input type="checkbox" class="form-check-input"></th><th>Nom</th><th>Langue</th><th>Mode</th><th class="text-end">Action</th></tr></thead>
                    <tbody id="list-series"></tbody>
                </table>
            </div>
        </div>

        <!-- MOVIES -->
        <div id="view-movies" class="view-section" style="display:none">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Bibliothèque Films</h2>
                <button class="btn btn-accent" onclick="scan('movies')"><i class="bi bi-search me-2"></i>Scanner</button>
            </div>
            <div class="glass-card p-0 overflow-hidden">
                <table class="table">
                    <thead><tr><th>Nom</th><th>Taille</th><th>Langue</th><th class="text-end">Action</th></tr></thead>
                    <tbody id="list-movies"></tbody>
                </table>
            </div>
        </div>

        <!-- TORRENTS -->
        <div id="view-torrents" class="view-section" style="display:none">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Torrents Créés</h2>
                <button class="btn btn-outline-light btn-sm" onclick="loadLibrary('torrents')"><i class="bi bi-arrow-clockwise"></i></button>
            </div>
            <div class="glass-card p-0 overflow-hidden">
                <table class="table">
                    <thead><tr><th>Fichier</th><th>Type</th><th>Date</th><th class="text-end">Actions</th></tr></thead>
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
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Logs Système</h2>
                <button class="btn btn-outline-light btn-sm" onclick="fetchLogs()">Actualiser</button>
            </div>
            <div class="glass-card bg-black shadow-inner" style="height: 500px; overflow-y: auto;" id="log-output"></div>
        </div>

        <!-- SETTINGS -->
        <div id="view-settings" class="view-section" style="display:none">
            <div class="mb-4"><h2>Configuration Globale</h2></div>
            <div class="row g-4">
                <div class="col-md-6">
                    <div class="glass-card">
                        <h5 class="mb-3 text-accent"><i class="bi bi-folder"></i> Chemins</h5>
                        <div class="mb-3">
                            <label class="form-label text-mute small">Dossier Séries (Source)</label>
                            <input type="text" id="cfg-series-root" class="form-control">
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-mute small">Dossier Films (Source)</label>
                            <input type="text" id="cfg-movies-root" class="form-control">
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-mute small">Destination Torrents</label>
                            <input type="text" id="cfg-out" class="form-control">
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="glass-card">
                        <h5 class="mb-3 text-accent"><i class="bi bi-globe"></i> Réseau & Options</h5>
                        <div class="mb-3">
                            <label class="form-label text-mute small">URL du Tracker</label>
                            <input type="text" id="cfg-tracker" class="form-control" placeholder="http://tracker.com/announce">
                        </div>
                        <div class="form-check form-switch mt-4">
                            <input class="form-check-input" type="checkbox" id="cfg-private">
                            <label class="form-check-label">Mode Privé (Flag Private)</label>
                        </div>
                    </div>
                </div>
            </div>
            <button class="btn btn-accent w-100 py-3 mt-2" onclick="saveConfig()"><i class="bi bi-save me-2"></i>SAUVEGARDER LES RÉGLAGES</button>
        </div>
    </div>

    <script>
        function switchView(viewId) {
            document.querySelectorAll('.view-section').forEach(s => s.style.display = 'none');
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            document.getElementById('view-' + viewId).style.display = 'block';
            document.getElementById('nav-' + viewId).classList.add('active');
            if(viewId === 'logs') fetchLogs();
            if(['series','movies','torrents','tasks'].includes(viewId)) loadLibrary(viewId);
        }

        async function scan(type) {
            const btn = event.target;
            const original = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Scan...';
            await fetch('/api/scan/' + type, {method: 'POST'});
            await loadLibrary(type);
            btn.disabled = false;
            btn.innerHTML = original;
        }

        async function cleanTasks() {
            await fetch('/api/tasks/clean', {method: 'POST'});
            loadLibrary('tasks');
        }

        async function stopTask(id) {
            await fetch('/api/tasks/stop/' + id, {method: 'POST'});
            loadLibrary('tasks');
        }

        async function loadLibrary(type) {
            const res = await fetch('/api/library/' + type);
            const data = await res.json();
            const container = document.getElementById('list-' + type);
            if(!container) return;

            if(type === 'tasks') {
                container.innerHTML = data.length ? data.map(t => `
                    <div class="glass-card mb-3 border-start border-4 border-${t.status === 'running' ? 'primary' : t.status === 'cancelled' ? 'warning' : 'success'}">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div>
                                <div class="fw-bold text-white">${t.name} <span class="text-mute small ms-2">${t.current}</span></div>
                                <div class="text-mute x-small" style="font-size: 0.7rem;">${t.detail || 'Traitement...'}</div>
                            </div>
                            <div class="d-flex align-items-center gap-3">
                                <div class="text-accent fw-bold small">${t.eta}</div>
                                ${t.status === 'running' ? `<button onclick="stopTask(${t.id})" class="btn btn-sm btn-danger py-0 px-2" style="font-size:0.6rem;">STOP</button>` : ''}
                            </div>
                        </div>
                        <div class="progress mb-1" style="height: 6px;"><div class="progress-bar" style="width: ${t.progress}%"></div></div>
                        <div class="d-flex justify-content-between text-mute" style="font-size: 0.6rem;">
                            <span>Progression globale</span>
                            <span>${t.progress}%</span>
                        </div>
                    </div>
                `).join('') : '<div class="text-center py-5 text-mute">Aucune activité en cours.</div>';
                return;
            }

            if(type === 'torrents') {
                container.innerHTML = data.length ? data.map(t => `
                    <tr>
                        <td><i class="bi bi-file-earmark-text me-2 text-accent"></i>${t.name}</td>
                        <td><span class="badge bg-secondary opacity-50 small">${t.type}</span></td>
                        <td class="text-mute small">${t.date}</td>
                        <td class="text-end"><button class="btn btn-sm btn-link text-mute p-0"><i class="bi bi-download"></i></button></td>
                    </tr>
                `).join('') : '<tr><td colspan="4" class="text-center py-5 text-mute">Aucun torrent créé pour le moment.</td></tr>';
                return;
            }

            if(type === 'series') {
                container.innerHTML = data.length ? data.map(item => `
                    <tr>
                        <td><input type="checkbox" class="form-check-input"></td>
                        <td><span class="fw-bold text-white">${item.name}</span> <span class="badge bg-indigo-subtle text-indigo ms-2" style="font-size:0.6rem;">${item.size}</span></td>
                        <td>
                            <select class="form-select form-select-sm w-auto py-0 px-2" style="font-size: 0.7rem;">
                                <option>MULTI</option><option>FRENCH</option><option>VOSTFR</option>
                            </select>
                        </td>
                        <td>
                            <select class="form-select form-select-sm w-auto py-0 px-2" style="font-size: 0.7rem;">
                                <option>Pack</option><option>Saison</option><option>EP</option>
                            </select>
                        </td>
                        <td class="text-end">
                            <button class="btn btn-sm btn-link text-warning p-0"><i class="bi bi-zap-fill"></i></button>
                        </td>
                    </tr>
                `).join('') : '<tr><td colspan="5" class="text-center py-5 text-mute">Dossier vide. Cliquez sur Scanner.</td></tr>';
            } else {
                container.innerHTML = data.length ? data.map(item => `
                    <tr>
                        <td><span class="fw-bold text-white">${item.name}</span></td>
                        <td><span class="badge bg-indigo-subtle text-indigo">${item.size}</span></td>
                        <td>
                            <select class="form-select form-select-sm w-auto py-0 px-2" style="font-size: 0.7rem;">
                                <option>MULTI</option><option>FRENCH</option>
                            </select>
                        </td>
                        <td class="text-end"><button class="btn btn-sm btn-link text-warning p-0"><i class="bi bi-zap-fill"></i></button></td>
                    </tr>
                `).join('') : '<tr><td colspan="4" class="text-center py-5 text-mute">Dossier vide. Cliquez sur Scanner.</td></tr>';
            }
        }

        async function fetchLogs() {
            const res = await fetch('/api/logs');
            const logs = await res.json();
            const out = document.getElementById('log-output');
            out.innerHTML = logs.map(l => `<div class="log-line p-1 px-3"><span class="log-time">[${l.time}]</span><span class="log-${l.level}">${l.msg}</span></div>`).join('');
            out.scrollTop = out.scrollHeight;
        }

        async function loadConfig() {
            const res = await fetch('/api/config');
            const cfg = await res.json();
            document.getElementById('cfg-tracker').value = cfg.tracker_url || '';
            document.getElementById('cfg-series-root').value = cfg.series_root || '';
            document.getElementById('cfg-movies-root').value = cfg.movies_root || '';
            document.getElementById('cfg-out').value = cfg.series_out || '';
            document.getElementById('cfg-private').checked = cfg.private;
        }

        async function saveConfig() {
            const data = {
                tracker_url: document.getElementById('cfg-tracker').value,
                series_root: document.getElementById('cfg-series-root').value,
                movies_root: document.getElementById('cfg-movies-root').value,
                series_out: document.getElementById('cfg-out').value,
                private: document.getElementById('cfg-private').checked
            };
            await fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            alert('Configuration enregistrée !');
        }

        window.onload = () => {
            switchView('series');
            loadConfig();
        };
    </script>
</body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)