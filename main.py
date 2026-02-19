#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, make_response

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, 'dist')

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Configuration de l'application
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
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

CONFIG = load_config()

# --- API ROUTES ---

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
                items.append({"name": entry.name, "path": entry.path, "size": "0 GB"})
    except: pass
    return jsonify(sorted(items, key=lambda x: x['name']))

# --- SERVING FRONTEND ---

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # 1. Si le fichier existe physiquement (js, css, images)
    file_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    
    # 2. Sinon, on cherche index.html pour le SPA
    index_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, 'index.html')
    
    # 3. ULTIME SECOURS : Si index.html est absent, on affiche une erreur propre
    files_in_dist = os.listdir(app.static_folder) if os.path.exists(app.static_folder) else "DOSSIER ABSENT"
    html_error = f"""
    <html>
        <body style="background: #0f172a; color: white; font-family: sans-serif; padding: 50px; text-align: center;">
            <h1 style="color: #f43f5e;">⚠️ ERREUR DE DÉPLOIEMENT</h1>
            <p>Le serveur Flask tourne, mais l'interface React (dist/index.html) est introuvable.</p>
            <div style="background: #1e293b; padding: 20px; border-radius: 10px; display: inline-block; text-align: left; margin-top: 20px;">
                <p><b>Chemin cherché :</b> {index_path}</p>
                <p><b>Contenu du dossier dist :</b> {files_in_dist}</p>
            </div>
            <p style="margin-top: 20px; color: #94a3b8;">Vérifiez vos GitHub Actions, le build a probablement échoué.</p>
        </body>
    </html>
    """
    return make_response(html_error, 404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)