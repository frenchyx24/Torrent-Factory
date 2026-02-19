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

# --- Configuration ---
app = Flask(__name__, static_folder='dist', static_url_path='')
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
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TORRENT FACTORY V1 - DÉPLOYÉ")
    print(f"🌐 Interface: http://localhost:5000")
    print(f"📂 Config: {APP_DATA}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000)