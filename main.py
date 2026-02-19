#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38.Final - Version Premium Corrigée
"""

import os
import json
import time
import threading
import logging
from pathlib import Path
from queue import Queue, Empty
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
    "lang": "fr",
    "series_root": "/data/series",
    "movies_root": "/data/movies",
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

@app.route("/api/logs")
def api_logs():
    return jsonify(list(web_logs))

@app.route("/")
def index():
    return PAGE_HTML.replace("{{VERSION}}", "V38.Final")

# ============================================================
# L'INTERFACE V38 PREMIUM (DESIGN RESTAURÉ ET NAVIGATION FIXÉE)
# ============================================================

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Torrent Factory {{VERSION}}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f172a;
            --sidebar-bg: rgba(15, 23, 42, 0.9);
            --glass: rgba(30, 41, 59, 0.7);
            --glass-border: rgba(255, 255, 255, 0.1);
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --text-main: #f8fafc;
            --text-mute: #94a3b8;
        }

        body {
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.03) 0%, transparent 40%);
            font-family: 'Outfit', sans-serif;
            color: var(--text-main);
            height: 100vh;
            margin: 0;
            display: flex;
            overflow: hidden;
        }

        /* SIDEBAR */
        .sidebar {
            width: 280px;
            background: var(--sidebar-bg);
            backdrop-filter: blur(20px);
            border-right: 1px solid var(--glass-border);
            display: flex;
            flex-direction: column;
            padding: 30px 20px;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 40px;
            padding: 0 10px;
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

        .nav-group {
            flex: 1;
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
            transition: all 0.2s ease;
            cursor: pointer;
            border: 1px solid transparent;
        }

        .nav-item:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #fff;
        }

        .nav-item.active {
            background: rgba(99, 102, 241, 0.1);
            color: var(--accent);
            border: 1px solid rgba(99, 102, 241, 0.2);
            font-weight: 600;
        }

        /* MAIN CONTENT */
        .main-container {
            flex: 1;
            padding: 40px;
            overflow-y: auto;
            position: relative;
        }

        .section-header {
            margin-bottom: 35px;
        }

        .section-header h2 {
            font-weight: 700;
            font-size: 2rem;
            margin-bottom: 5px;
        }

        .section-header p {
            color: var(--text-mute);
        }

        /* GLASS CARD */
        .glass-card {
            background: var(--glass);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
        }

        /* UTILS */
        .btn-accent {
            background: var(--accent);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: 600;
            transition: 0.2s;
        }

        .btn-accent:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(99, 102, 241, 0.3);
        }

        .footer-info {
            padding: 20px;
            border-top: 1px solid var(--glass-border);
            font-size: 0.8rem;
            color: var(--text-mute);
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="brand">
            <i class="bi bi-zap-fill"></i>
            <span>Torrent Factory</span>
        </div>
        
        <div class="nav-group">
            <div class="nav-item active" onclick="switchView('series')" id="nav-series">
                <i class="bi bi-tv"></i> <span>Séries</span>
            </div>
            <div class="nav-item" onclick="switchView('movies')" id="nav-movies">
                <i class="bi bi-film"></i> <span>Films</span>
            </div>
            <div class="nav-item" onclick="switchView('torrents')" id="nav-torrents">
                <i class="bi bi-folder-check"></i> <span>Torrents</span>
            </div>
            <div class="nav-item" onclick="switchView('tasks')" id="nav-tasks">
                <i class="bi bi-activity"></i> <span>Tâches</span>
            </div>
            <div class="nav-item" onclick="switchView('logs')" id="nav-logs">
                <i class="bi bi-terminal"></i> <span>Logs</span>
            </div>
        </div>

        <div class="nav-item" onclick="switchView('settings')" id="nav-settings">
            <i class="bi bi-gear"></i> <span>Réglages</span>
        </div>

        <div class="footer-info">
            Version {{VERSION}}<br>
            © 2024 Torrent Factory
        </div>
    </div>

    <div class="main-container">
        <!-- SERIES -->
        <div id="view-series" class="view-section">
            <div class="section-header">
                <h2>Bibliothèque Séries</h2>
                <p>Gérez vos séries et générez des torrents en masse.</p>
            </div>
            <div class="glass-card text-center py-5">
                <i class="bi bi-search mb-3 d-block opacity-25" style="font-size: 3rem;"></i>
                <p class="text-mute">Prêt pour le scan des séries...</p>
                <button class="btn btn-accent mt-3">Lancer le scan</button>
            </div>
        </div>

        <!-- MOVIES -->
        <div id="view-movies" class="view-section" style="display:none">
            <div class="section-header">
                <h2>Bibliothèque Films</h2>
                <p>Gérez vos films individuels.</p>
            </div>
            <div class="glass-card text-center py-5">
                <p class="text-mute">Aucun film détecté pour le moment.</p>
            </div>
        </div>

        <!-- TORRENTS -->
        <div id="view-torrents" class="view-section" style="display:none">
            <div class="section-header">
                <h2>Torrents Créés</h2>
                <p>Historique des fichiers .torrent générés.</p>
            </div>
        </div>

        <!-- TASKS -->
        <div id="view-tasks" class="view-section" style="display:none">
            <div class="section-header">
                <h2>Activités</h2>
                <p>Suivi de la progression en temps réel.</p>
            </div>
        </div>

        <!-- LOGS -->
        <div id="view-logs" class="view-section" style="display:none">
            <div class="section-header">
                <h2>Logs Système</h2>
                <p>Événements et erreurs du serveur.</p>
            </div>
            <div class="glass-card bg-black" style="font-family: monospace; font-size: 0.9rem; height: 400px; overflow-y: auto;">
                <div id="log-output"></div>
            </div>
        </div>

        <!-- SETTINGS -->
        <div id="view-settings" class="view-section" style="display:none">
            <div class="section-header">
                <h2>Réglages</h2>
                <p>Configuration des dossiers et du tracker.</p>
            </div>
            <div class="glass-card">
                <div class="mb-3">
                    <label class="form-label">URL du Tracker</label>
                    <input type="text" class="form-control bg-dark border-secondary text-white" placeholder="http://...">
                </div>
                <button class="btn btn-accent">Sauvegarder</button>
            </div>
        </div>
    </div>

    <script>
        function switchView(viewId) {
            // Cacher toutes les sections
            document.querySelectorAll('.view-section').forEach(section => {
                section.style.display = 'none';
            });
            // Désactiver tous les menus
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Afficher la section demandée
            const target = document.getElementById('view-' + viewId);
            if(target) target.style.display = 'block';
            
            // Activer le menu
            const nav = document.getElementById('nav-' + viewId);
            if(nav) nav.classList.add('active');

            console.log("Navigated to:", viewId);
        }

        // Fix initial state
        window.onload = () => switchView('series');
    </script>
</body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)