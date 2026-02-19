#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, make_response

# On définit les dossiers de base
APP_DIR = Path(__file__).parent.resolve()
STATIC_FOLDER = APP_DIR / "dist"

app = Flask(__name__, static_folder=str(STATIC_FOLDER), static_url_path='')
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Configuration via Variable d'environnement ou /config par défaut
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
        try:
            with open(CONFIG_FILE, "r") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except: return DEFAULT_CONFIG
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
    if not root_path.exists(): return jsonify([])
    items = []
    try:
        for entry in os.scandir(root_path):
            if entry.is_dir():
                items.append({"name": entry.name, "path": entry.path, "size": "N/A"})
    except: pass
    return jsonify(sorted(items, key=lambda x: x['name']))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(STATIC_FOLDER / path):
        return send_from_directory(str(STATIC_FOLDER), path)
    
    index_path = STATIC_FOLDER / "index.html"
    if index_path.exists():
        return send_from_directory(str(STATIC_FOLDER), "index.html")
    
    # Page de secours si build manquant
    return make_response(f"<h1>Erreur : Interface non trouvee dans {STATIC_FOLDER}</h1><p>Verifiez votre build Docker.</p>", 404)

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 TORRENT FACTORY - DEMARRAGE")
    print(f"📂 Chemin App: {APP_DIR}")
    print(f"📁 Chemin Static: {STATIC_FOLDER}")
    print(f"⚙️  Chemin Config: {CONFIG_DIR}")
    if not (STATIC_FOLDER / "index.html").exists():
        print("⚠️  ATTENTION : index.html est ABSENT du dossier static !")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=5000)