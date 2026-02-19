#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38 - Backend & Static Server
"""

import os
import sys
import subprocess
import platform
import string
import json
import re
import time
import threading
import uuid
import logging
import random
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify, send_from_directory

# --- Configuration Flask pour servir le build React ---
# On suppose que le build React est dans le dossier 'dist'
app = Flask(__name__, static_folder='dist', static_url_path='')

# --- Logique Backend (extraite du script original) ---
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
    "private": True
}
CONFIG = DEFAULT_CONFIG.copy()

# --- Routes API ---
@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(CONFIG)

@app.route("/api/logs")
def get_logs():
    return jsonify([{"id": 1, "time": "12:00", "msg": "Système prêt", "level": "info"}])

# --- Route pour servir l'application React ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    print("🚀 Torrent Factory V1 démarré sur http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)