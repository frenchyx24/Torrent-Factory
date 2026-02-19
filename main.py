#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38 - Backend & Static Server
Auto-install dependencies & Cross-platform support
"""

import os
import sys
import subprocess
import platform
import json
import logging
from pathlib import Path
from datetime import datetime

# --- Auto-installation des dépendances ---
def install_dependencies():
    required = ["flask", "py3createtorrent", "requests"]
    for package in required:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            print(f"📦 Installation de {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

from flask import Flask, request, jsonify, send_from_directory

# --- Configuration des chemins ---
# On définit le dossier de base comme étant celui où se trouve main.py
BASE_DIR = Path(__file__).parent.resolve()
STATIC_FOLDER = BASE_DIR / "dist"

app = Flask(__name__, static_folder=str(STATIC_FOLDER), static_url_path='')
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_default_app_data() -> Path:
    system = platform.system().lower()
    if system == "windows":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
        return base / "TorrentFactory"
    else:
        return Path.home() / ".config" / "TorrentFactory"

APP_DATA = Path(os.environ.get("TF_CONFIG_DIR", str(get_default_app_data())))
APP_DATA.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA / "config.json"
DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "max_workers": 2,
    "private": True,
    "analyze_audio": True
}

if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r") as f:
        CONFIG = json.load(f)
else:
    CONFIG = DEFAULT_CONFIG.copy()

# --- API Routes ---
@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        data = request.get_json()
        CONFIG.update(data)
        with open(CONFIG_FILE, "w") as f:
            json.dump(CONFIG, f)
        return jsonify({"success": True})
    return jsonify(CONFIG)

@app.route("/api/logs")
def get_logs():
    return jsonify([
        {"id": 1, "time": datetime.now().strftime("%H:%M:%S"), "msg": "Système Torrent Factory prêt", "level": "info"}
    ])

# --- Serve Frontend ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Si le fichier existe dans dist, on le sert
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    # Sinon on sert l'index.html (pour le routage React)
    else:
        if not os.path.exists(os.path.join(app.static_folder, 'index.html')):
            return f"Erreur : index.html introuvable dans {app.static_folder}. Vérifiez que le build a été effectué.", 404
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TORRENT FACTORY V1 - DÉPLOYÉ")
    print(f"🌐 Interface: http://localhost:5000")
    print(f"📂 Config: {APP_DATA}")
    print(f"📁 Static Folder: {STATIC_FOLDER}")
    
    if not STATIC_FOLDER.exists():
        print(f"⚠️ ATTENTION : Le dossier {STATIC_FOLDER} n'existe pas !")
    elif not (STATIC_FOLDER / "index.html").exists():
        print(f"⚠️ ATTENTION : index.html est absent de {STATIC_FOLDER}")
    else:
        print(f"✅ Interface détectée et prête.")
        
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000)