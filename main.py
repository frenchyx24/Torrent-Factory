#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='dist', static_url_path='')
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Configuration
CONFIG_DIR = Path(os.environ.get("TF_CONFIG_DIR", "/config"))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "series_root": "/data/series",
    "series_out": "/data/torrents/series",
    "movies_root": "/data/movies",
    "movies_out": "/data/torrents/movies",
    "tracker": "udp://tracker.opentrackr.org:1337/announce",
    "private": True
}

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG

CONFIG = load_config()

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    global CONFIG
    if request.method == "POST":
        CONFIG.update(request.get_json())
        with open(CONFIG_FILE, "w") as f:
            json.dump(CONFIG, f, indent=4)
        return jsonify({"status": "success"})
    return jsonify(CONFIG)

@app.route("/api/scan/<type>")
def scan_dir(type):
    path_key = "series_root" if type == "series" else "movies_root"
    root_path = Path(CONFIG.get(path_key, ""))
    
    if not root_path.exists():
        return jsonify([])
    
    items = []
    try:
        for entry in os.scandir(root_path):
            if entry.is_dir():
                size = sum(f.stat().st_size for f in Path(entry.path).glob('**/*') if f.is_file())
                items.append({
                    "name": entry.name,
                    "path": entry.path,
                    "size": f"{size / (1024**3):.2f} GB" if size > 0 else "0 GB"
                })
    except Exception as e:
        logging.error(f"Scan error: {e}")
        
    return jsonify(sorted(items, key=lambda x: x['name']))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)