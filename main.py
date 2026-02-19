#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V38 - Générateur automatique de torrents
Fonctionne sous Windows et Linux, installe automatiquement les dépendances
"""

import os
import sys
import subprocess
import platform

# ============================================================
# ÉTAPE 1 : Installation des dépendances (AVANT tout import)
# ============================================================

def ensure_pip():
    """Vérifie que pip est disponible"""
    try:
        import pip  # noqa: F401
        return True
    except ImportError:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "ensurepip", "--upgrade"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            return False

def pip_install(package: str) -> bool:
    """Installe un package via pip"""
    try:
        print(f"Installation de {package}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", package],
            timeout=300
        )
        print(f"✓ {package} installé")
        return True
    except Exception as e:
        print(f"✗ Échec installation {package}: {e}")
        return False

def check_and_install_dependencies():
    """Vérifie et installe toutes les dépendances requises"""
    print("=" * 60)
    print("  VÉRIFICATION DES DÉPENDANCES")
    print("=" * 60)
    
    if not ensure_pip():
        print("ERREUR CRITIQUE: pip non disponible.")
        print("Installez pip manuellement puis relancez le script.")
        sys.exit(1)
    
    required = [
        ("flask", "flask"),
        ("py3createtorrent", "py3createtorrent"),
        ("static-ffmpeg", "static_ffmpeg"),
    ]
    
    for pip_name, import_name in required:
        try:
            __import__(import_name.replace("-", "_"))
            print(f"✓ {pip_name} déjà installé")
        except ImportError:
            if not pip_install(pip_name):
                print(f"ATTENTION: {pip_name} non installé (certaines fonctions peuvent être limitées)")
    
    print("=" * 60)
    print()

# Lancer l'installation AVANT les imports
check_and_install_dependencies()

# ============================================================
# ÉTAPE 2 : Imports (après installation)
# ============================================================

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

from flask import Flask, request, jsonify

# ============================================================
# ÉTAPE 3 : Configuration FFmpeg
# ============================================================

HAS_FFPROBE = False
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    
    # Test si ffprobe fonctionne
    result = subprocess.run(
        ["ffprobe", "-version"], 
        capture_output=True, 
        text=True, 
        timeout=3
    )
    HAS_FFPROBE = (result.returncode == 0)
except Exception:
    HAS_FFPROBE = False

# ============================================================
# ÉTAPE 4 : Configuration Flask et logging
# ============================================================

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# ============================================================
# ÉTAPE 5 : Chemins et stockage
# ============================================================

def get_default_app_data() -> Path:
    """Retourne le chemin de config selon l'OS"""
    system = platform.system().lower()
    if system == "windows":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
        return base / "TorrentFactory"
    else:
        return Path.home() / ".config" / "TorrentFactory"

APP_DATA = Path(os.environ.get("TF_CONFIG_DIR", str(get_default_app_data())))
APP_DATA.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA / "config.json"
TASKS_FILE = APP_DATA / "tasks.json"
LIBRARY_FILE = APP_DATA / "library.json"

DEFAULT_CONFIG = {
    "lang": "fr",
    "series_root": str(Path.cwd()),
    "series_out": str(Path.cwd() / "torrents_series"),
    "movies_root": str(Path.cwd()),
    "movies_out": str(Path.cwd() / "torrents_movies"),
    "tracker_url": "",
    "private": True,
    "piece_size": 0,
    "comment": "Created with TF",
    "show_size": False,
    "analyze_audio": True,
    "max_workers": 2,
    "torrent_timeout_sec": 7200,
    "logs_max": 5000,
    "reset_tasks_on_start": True
}

def load_json(path: Path, default: dict) -> dict:
    """Charge un fichier JSON avec fallback"""
    if not path.exists():
        return default.copy()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default.copy()

def save_json(path: Path, data: dict) -> bool:
    """Sauvegarde JSON atomique"""
    temp = path.with_suffix(".tmp")
    try:
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        temp.replace(path)
        return True
    except Exception:
        if temp.exists():
            try:
                temp.unlink()
            except Exception:
                pass
        return False

CONFIG = load_json(CONFIG_FILE, DEFAULT_CONFIG)
CONFIG["max_workers"] = max(1, int(CONFIG.get("max_workers", 2)))
CONFIG["torrent_timeout_sec"] = int(CONFIG.get("torrent_timeout_sec", 7200))
CONFIG["logs_max"] = int(CONFIG.get("logs_max", 5000))

LIBRARY_CACHE = load_json(LIBRARY_FILE, {"series": [], "movies": []})

# ============================================================
# ÉTAPE 6 : Système de logs incrémental
# ============================================================

logs_lock = threading.Lock()
web_logs = deque(maxlen=CONFIG["logs_max"])
log_seq = 0

def log_system(msg: str, level: str = "info"):
    """Enregistre un log avec timestamp et ID unique"""
    global log_seq
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    with logs_lock:
        log_seq += 1
        web_logs.append({
            "id": log_seq,
            "time": timestamp,
            "msg": msg,
            "level": level
        })
    
    log_func = getattr(logging, level.lower(), logging.info)
    log_func(msg)

# ============================================================
# ÉTAPE 7 : Utilitaires
# ============================================================

VIDEO_EXTENSIONS = (".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts", ".flv")

def format_duration(seconds: float) -> str:
    """Formate une durée en format lisible"""
    if seconds is None or seconds < 0:
        return "--:--"
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m:02d}m {s:02d}s"

def get_recursive_size(path: Path) -> int:
    """Calcule la taille récursive d'un fichier/dossier"""
    try:
        if path.is_file():
            return path.stat().st_size
        
        total = 0
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total += item.stat().st_size
                except Exception:
                    pass
        return total
    except Exception:
        return 0

def sanitize_filename(name: str) -> str:
    """Nettoie un nom de fichier des caractères interdits"""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    name = name.strip()
    return name[:200] if len(name) > 200 else name

def analyze_media_language(path: Path) -> str:
    """Détecte la langue via FFprobe et regex sur le nom"""
    languages = set()
    
    # Analyse FFprobe si disponible
    if CONFIG.get("analyze_audio", True) and HAS_FFPROBE:
        try:
            target = path
            
            # Si c'est un dossier, trouve le premier fichier vidéo
            if path.is_dir():
                for video_file in path.rglob("*"):
                    if video_file.is_file() and video_file.suffix.lower() in VIDEO_EXTENSIONS:
                        target = video_file
                        break
            
            if target.is_file():
                cmd = [
                    "ffprobe", "-v", "error",
                    "-select_streams", "a",
                    "-show_entries", "stream_tags=language",
                    "-of", "csv=p=0",
                    str(target)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=4
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        lang = line.strip().lower()
                        if lang:
                            languages.add(lang)
        except Exception:
            pass
    
    # Analyse regex sur le nom
    name_upper = path.name.upper()
    
    if re.search(r"\bMULTI\b", name_upper):
        languages.add("multi")
    if re.search(r"\b(TRUEFRENCH|VFF|VFQ|FRENCH|FR)\b", name_upper):
        languages.add("fre")
    if re.search(r"\bVOSTFR\b", name_upper):
        languages.add("vostfr")
    if re.search(r"\b(VO|ENGLISH|ENG)\b", name_upper):
        languages.add("eng")
    
    # Détermine le tag final
    has_french = any(l in languages for l in ("fre", "fra", "french", "fr", "vf"))
    has_english = any(l in languages for l in ("eng", "en", "english", "us"))
    
    if "multi" in languages or (has_french and has_english):
        return "MULTI"
    if "vostfr" in languages:
        return "VOSTFR"
    if has_french:
        return "FRENCH"
    if has_english:
        return "VO"
    
    return ""

# ============================================================
# ÉTAPE 8 : Système de tâches
# ============================================================

task_queue = Queue()
active_tasks_lock = threading.Lock()
active_tasks = []
stop_events_lock = threading.Lock()
stop_events = {}

def save_tasks_state():
    """Sauvegarde thread-safe de l'état des tâches"""
    with active_tasks_lock:
        save_json(TASKS_FILE, active_tasks)

def save_library_cache():
    """Sauvegarde thread-safe de la bibliothèque"""
    save_json(LIBRARY_FILE, LIBRARY_CACHE)

# Reset des tâches au démarrage
if CONFIG.get("reset_tasks_on_start", True):
    active_tasks.clear()
    save_tasks_state()

def get_task(task_id: str):
    """Récupère une tâche par son ID"""
    with active_tasks_lock:
        for task in active_tasks:
            if task.get("id") == task_id:
                return task
    return None

def set_stop_flag(task_id: str, value: bool):
    """Définit le flag d'arrêt d'une tâche"""
    with stop_events_lock:
        stop_events[task_id] = value

def get_stop_flag(task_id: str) -> bool:
    """Vérifie si une tâche doit s'arrêter"""
    with stop_events_lock:
        return bool(stop_events.get(task_id, False))

def clear_stop_flag(task_id: str):
    """Supprime le flag d'arrêt d'une tâche"""
    with stop_events_lock:
        stop_events.pop(task_id, None)

def build_torrent_commands(item: dict):
    """
    Construit la liste des commandes torrent à exécuter
    Retourne: [(Path source, str nom_torrent), ...]
    """
    path = Path(item["path"])
    base_name = item.get("name", path.name)
    mode = item.get("mode", "movie")
    tag = (item.get("lang_tag") or "").strip()
    suffix = f" {tag}" if tag else ""
    
    commands = []
    
    if mode == "movie":
        commands.append((path, f"{base_name}{suffix}"))
    
    elif mode == "complete":
        final_name = f"{base_name}{suffix}"
        seasons = item.get("seasons_list") or []
        
        if seasons:
            season_numbers = []
            for season in seasons:
                match = re.findall(r"\d+", str(season))
                if match:
                    season_numbers.append(f"S{int(match[0]):02d}")
            
            season_numbers = sorted(set(season_numbers))
            if season_numbers:
                final_name += " - " + " ".join(season_numbers)
        else:
            final_name += " - S01"
        
        commands.append((path, final_name))
    
    elif mode == "season":
        if path.is_dir():
            for entry in path.iterdir():
                if entry.is_dir() and re.match(
                    r"(saison|season|s\d)", 
                    entry.name, 
                    re.IGNORECASE
                ):
                    commands.append((entry, f"{base_name} - {entry.name}{suffix}"))
    
    elif mode == "episode":
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            stem = path.stem
            if suffix and suffix.upper() not in stem.upper():
                stem += suffix
            commands.append((path, stem))
        elif path.is_dir():
            for video_file in path.rglob("*"):
                if video_file.is_file() and video_file.suffix.lower() in VIDEO_EXTENSIONS:
                    stem = video_file.stem
                    if suffix and suffix.upper() not in stem.upper():
                        stem += suffix
                    commands.append((video_file, stem))
    
    return commands

def run_creation_process(task: dict):
    """Processus principal de création de torrents"""
    tracker = (CONFIG.get("tracker_url") or "").strip()
    task_type = task.get("type", "series")
    
    out_root = Path(
        CONFIG["movies_out"] if task_type == "movie" else CONFIG["series_out"]
    )
    out_root.mkdir(parents=True, exist_ok=True)
    
    items = task.get("items") or []
    total_items = len(items)
    
    if total_items == 0:
        task["progress_global"] = 100
        task["progress_item"] = 100
        task["eta_item"] = "Terminé"
        return
    
    for item_index, item in enumerate(items):
        if get_stop_flag(task["id"]):
            break
        
        source_path = Path(item["path"])
        if not source_path.exists():
            log_system(f"Chemin inexistant: {source_path}", "error")
            continue
        
        # Mise à jour état
        task["current_item_name"] = item.get("name", source_path.name)
        task["current_item_index"] = f"{item_index + 1}/{total_items}"
        task["current_detail"] = ""
        task["progress_global"] = int((item_index / total_items) * 100)
        task["progress_item"] = 0
        task["eta_item"] = "Analyse..."
        save_tasks_state()
        
        # Calcul taille (optionnel)
        size = 0
        if CONFIG.get("show_size", False):
            size = get_recursive_size(source_path)
        
        start_time = time.time()
        
        # Construction des commandes
        commands = build_torrent_commands(item)
        if not commands:
            log_system(f"Aucune commande à générer pour: {source_path}", "warning")
            continue
        
        # Thread de monitoring
        monitor_flag = True
        estimated_speed = 60 * 1024 * 1024  # 60 MB/s
        
        def monitor_progress():
            last_save = 0
            while monitor_flag:
                if get_stop_flag(task["id"]):
                    break
                
                elapsed = time.time() - start_time
                
                if elapsed > 1:
                    if size > 0:
                        done = min(elapsed * estimated_speed, size * 0.99)
                        percentage = int((done / size) * 100)
                        task["progress_item"] = min(max(percentage, 0), 99)
                        
                        remaining = (size - done) / estimated_speed
                        if remaining <= 1:
                            task["eta_item"] = "Finalisation..."
                        else:
                            task["eta_item"] = format_duration(remaining)
                    else:
                        # Sans taille, progression fictive
                        current = task.get("progress_item", 0)
                        task["progress_item"] = min(current + 1, 99)
                        task["eta_item"] = "Finalisation..."
                
                # Sauvegarde périodique
                if time.time() - last_save > 2:
                    save_tasks_state()
                    last_save = time.time()
                
                time.sleep(1)
        
        monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
        monitor_thread.start()
        
        # Exécution des torrents
        for cmd_index, (source, title) in enumerate(commands):
            if get_stop_flag(task["id"]):
                break
            
            safe_title = sanitize_filename(title)
            output_file = out_root / f"{safe_title}.torrent"
            
            task["current_detail"] = f"[{cmd_index + 1}/{len(commands)}] {safe_title}"
            task["eta_item"] = "Finalisation..."
            save_tasks_state()
            
            # Construction commande py3createtorrent
            cmd = [sys.executable, "-m", "py3createtorrent"]
            
            if tracker:
                cmd.extend(["-t", tracker])
            
            cmd.extend(["-o", str(output_file)])
            
            if CONFIG.get("private", True):
                cmd.append("-P")
            
            piece_size = int(CONFIG.get("piece_size", 0))
            if piece_size > 0:
                cmd.extend(["-p", str(piece_size)])
            
            cmd.append(str(source))
            
            # Exécution avec timeout
            timeout = int(CONFIG.get("torrent_timeout_sec", 7200))
            cmd_start = time.time()
            
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                while process.poll() is None:
                    # Vérification arrêt demandé
                    if get_stop_flag(task["id"]):
                        try:
                            process.terminate()
                            time.sleep(0.5)
                            if process.poll() is None:
                                process.kill()
                        except Exception:
                            pass
                        
                        # Suppression fichier partiel
                        try:
                            if output_file.exists():
                                output_file.unlink()
                        except Exception:
                            pass
                        break
                    
                    # Vérification timeout
                    if (time.time() - cmd_start) > timeout:
                        try:
                            process.kill()
                        except Exception:
                            pass
                        
                        try:
                            if output_file.exists():
                                output_file.unlink()
                        except Exception:
                            pass
                        
                        raise RuntimeError(
                            f"Timeout (>{timeout}s) sur: {safe_title}"
                        )
                    
                    time.sleep(0.5)
                
                # Torrent terminé avec succès
                if not get_stop_flag(task["id"]):
                    task["progress_item"] = 100
                    task["eta_item"] = "Terminé"
                    save_tasks_state()
            
            except Exception as e:
                raise RuntimeError(str(e))
        
        # Arrêt du monitoring
        monitor_flag = False
        monitor_thread.join(timeout=2)

def task_worker():
    """Worker thread qui traite les tâches de la queue"""
    while True:
        try:
            task_id = task_queue.get(timeout=1)
        except Empty:
            continue
        
        task = get_task(task_id)
        if not task:
            task_queue.task_done()
            continue
        
        set_stop_flag(task_id, False)
        task["status"] = "running"
        task["error_msg"] = ""
        task["eta_item"] = "Démarrage..."
        save_tasks_state()
        
        log_system(f"Démarrage: {task.get('name')}", "info")
        
        try:
            run_creation_process(task)
            
            if get_stop_flag(task_id):
                task["status"] = "cancelled"
                task["eta_item"] = "Annulé"
                log_system(f"Annulé: {task.get('name')}", "warning")
            else:
                task["status"] = "completed"
                task["progress_global"] = 100
                task["progress_item"] = 100
                task["eta_item"] = "Terminé"
                log_system(f"Terminé: {task.get('name')}", "info")
        
        except Exception as e:
            task["status"] = "error"
            task["error_msg"] = str(e)
            task["eta_item"] = "Erreur"
            log_system(f"Erreur {task.get('name')}: {e}", "error")
        
        finally:
            save_tasks_state()
            clear_stop_flag(task_id)
            task_queue.task_done()

# Lancement des workers
num_workers = max(1, int(CONFIG.get("max_workers", 2)))
for _ in range(num_workers):
    threading.Thread(target=task_worker, daemon=True).start()

# ============================================================
# ÉTAPE 9 : Routes API Flask
# ============================================================

@app.after_request
def add_security_headers(response):
    """Ajout des headers de sécurité"""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response

@app.route("/")
def index():
    """Page principale"""
    return PAGE_HTML.replace("{{VERSION}}", f"V38.{random.randint(1000, 9999)}")

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    """Gestion de la configuration"""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        
        # Normalisation des chemins
        for key in ("series_root", "series_out", "movies_root", "movies_out"):
            if key in data and data[key]:
                try:
                    data[key] = str(Path(data[key]).expanduser().resolve())
                except Exception:
                    pass
        
        # Normalisation des entiers
        for key in ("max_workers", "torrent_timeout_sec", "piece_size", "logs_max"):
            if key in data:
                try:
                    data[key] = int(data[key])
                except Exception:
                    pass
        
        CONFIG.update(data)
        save_json(CONFIG_FILE, CONFIG)
        
        return jsonify({"success": True})
    
    return jsonify(CONFIG)

@app.route("/api/library/<lib_type>")
def api_library(lib_type):
    """Récupération de la bibliothèque"""
    if lib_type not in ("series", "movies"):
        return jsonify([]), 400
    return jsonify(LIBRARY_CACHE.get(lib_type, []))

@app.route("/api/scan/<lib_type>", methods=["POST"])
def api_scan(lib_type):
    """Scan d'un répertoire"""
    if lib_type not in ("series", "movies"):
        return jsonify([]), 400
    
    root = Path(CONFIG.get(f"{lib_type}_root", str(Path.cwd()))).expanduser()
    found = []
    
    if not root.exists():
        LIBRARY_CACHE[lib_type] = []
        save_library_cache()
        return jsonify([])
    
    try:
        for entry in root.iterdir():
            # Ignore fichiers système
            if entry.name.startswith(("$", ".", "~")):
                continue
            
            item = None
            
            if lib_type == "series" and entry.is_dir():
                seasons = []
                try:
                    for sub in entry.iterdir():
                        if sub.is_dir() and re.match(
                            r"(saison|season|s\d)",
                            sub.name,
                            re.IGNORECASE
                        ):
                            seasons.append(sub.name)
                except Exception:
                    pass
                
                seasons.sort()
                item = {
                    "name": entry.name,
                    "path": str(entry),
                    "seasons_list": seasons
                }
            
            elif lib_type == "movies":
                if entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS:
                    item = {
                        "name": entry.name,
                        "path": str(entry),
                        "type": "file"
                    }
                elif entry.is_dir():
                    item = {
                        "name": entry.name,
                        "path": str(entry),
                        "type": "folder"
                    }
            
            if item:
                item_path = Path(item["path"])
                item["size"] = (
                    get_recursive_size(item_path)
                    if CONFIG.get("show_size", False)
                    else 0
                )
                item["detected_tag"] = analyze_media_language(item_path)
                found.append(item)
    
    except Exception as e:
        log_system(f"Erreur scan {lib_type}: {e}", "error")
    
    LIBRARY_CACHE[lib_type] = found
    save_library_cache()
    return jsonify(found)

@app.route("/api/torrents")
def api_torrents():
    """Liste des torrents créés"""
    series_dir = Path(CONFIG.get("series_out", str(Path.cwd() / "torrents_series")))
    movies_dir = Path(CONFIG.get("movies_out", str(Path.cwd() / "torrents_movies")))
    
    series = (
        [{"name": f.name} for f in series_dir.glob("*.torrent")]
        if series_dir.exists()
        else []
    )
    movies = (
        [{"name": f.name} for f in movies_dir.glob("*.torrent")]
        if movies_dir.exists()
        else []
    )
    
    return jsonify({"series": series, "movies": movies})

@app.route("/api/tasks/add", methods=["POST"])
def api_tasks_add():
    """Ajout d'une nouvelle tâche"""
    data = request.get_json(silent=True) or {}
    tasks = data.get("tasks") or []
    task_type = data.get("type", "series")
    
    if not isinstance(tasks, list) or not tasks:
        return jsonify({"success": False, "error": "Aucune tâche"}), 400
    
    task_id = str(uuid.uuid4())[:8]
    
    task = {
        "id": task_id,
        "status": "pending",
        "type": task_type,
        "name": f"{task_type.capitalize()} - {len(tasks)} item(s)",
        "items": tasks,
        "progress_global": 0,
        "progress_item": 0,
        "current_item_name": "...",
        "current_item_index": "0/0",
        "current_detail": "",
        "eta_item": "--:--",
        "error_msg": "",
        "created_at": datetime.now().strftime("%H:%M"),
    }
    
    with active_tasks_lock:
        active_tasks.append(task)
    
    save_tasks_state()
    task_queue.put(task_id)
    
    return jsonify({"success": True, "task_id": task_id})

@app.route("/api/tasks/list")
def api_tasks_list():
    """Liste des tâches actives"""
    with active_tasks_lock:
        return jsonify(active_tasks)

@app.route("/api/tasks/cancel", methods=["POST"])
def api_tasks_cancel():
    """Annulation d'une tâche"""
    data = request.get_json(silent=True) or {}
    task_id = data.get("id")
    
    if not task_id:
        return jsonify({"success": False, "error": "ID manquant"}), 400
    
    set_stop_flag(task_id, True)
    return jsonify({"success": True})

@app.route("/api/tasks/clear", methods=["POST", "GET"])
def api_tasks_clear():
    """Nettoyage des tâches terminées"""
    with active_tasks_lock:
        kept = [
            t for t in active_tasks
            if t.get("status") in ("pending", "running")
        ]
        active_tasks.clear()
        active_tasks.extend(kept)
    
    save_tasks_state()
    return jsonify({"success": True})

@app.route("/api/logs")
def api_logs():
    """Récupération des logs (incrémental)"""
    after = int(request.args.get("after", 0))
    limit = int(request.args.get("limit", 500))
    
    with logs_lock:
        filtered = [log for log in web_logs if log["id"] > after]
    
    if limit > 0:
        filtered = filtered[:limit]
    
    return jsonify(filtered)

@app.route("/api/drives")
def api_drives():
    """Liste des lecteurs/points de montage"""
    drives = []
    
    system = platform.system().lower()
    if system == "windows":
        for letter in string.ascii_uppercase:
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                drives.append({"name": drive_path, "path": drive_path})
    else:
        for mount_point in ("/", "/home", "/media", "/mnt", "/Volumes"):
            if os.path.exists(mount_point):
                drives.append({"name": mount_point, "path": mount_point})
    
    return jsonify(drives)

@app.route("/api/browse")
def api_browse():
    """Navigation dans le système de fichiers"""
    raw_path = request.args.get("path", "") or str(Path.cwd())
    
    # Protection contre null bytes
    if "\x00" in raw_path:
        return jsonify({"current": str(Path.cwd()), "items": []}), 400
    
    try:
        path = Path(raw_path).expanduser().resolve()
    except Exception:
        path = Path.cwd().resolve()
    
    items = []
    
    try:
        if path.is_dir():
            for entry in path.iterdir():
                if entry.is_dir() and not entry.name.startswith(("$", ".", "~", "System")):
                    items.append({"name": entry.name, "path": str(entry)})
            
            items.sort(key=lambda x: x["name"].lower())
    except Exception:
        pass
    
    return jsonify({"current": str(path), "items": items})

# ============================================================
# ÉTAPE 10 : Interface HTML
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
:root{--bg-dark:#0f172a;--glass:rgba(30,41,59,.7);--glass-border:rgba(255,255,255,.1);--accent:#6366f1;--accent-glow:rgba(99,102,241,.4);--text-main:#f8fafc;--text-mute:#94a3b8}
body{background-color:var(--bg-dark);background-image:radial-gradient(circle at 10% 20%,rgba(99,102,241,.15) 0%,transparent 40%),radial-gradient(circle at 90% 80%,rgba(16,185,129,.1) 0%,transparent 40%);font-family:Outfit,sans-serif;color:var(--text-main);height:100vh;overflow:hidden}
.glass-panel{background:var(--glass);backdrop-filter:blur(16px);border:1px solid var(--glass-border);border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.3)}
.sidebar{width:280px;padding:25px;display:flex;flex-direction:column;border-right:1px solid var(--glass-border);background:rgba(15,23,42,.8)}
.app-title{font-weight:700;font-size:1.4rem;margin-bottom:30px;color:#fff;display:flex;align-items:center;gap:10px}
.nav-item{padding:12px 18px;margin-bottom:6px;border-radius:12px;cursor:pointer;color:var(--text-mute);transition:.3s;font-weight:500;display:flex;align-items:center;gap:12px}
.nav-item:hover{background:rgba(255,255,255,.08);color:#fff;transform:translateX(5px)}
.nav-item.active{background:linear-gradient(90deg,rgba(99,102,241,.2) 0%,transparent 100%);color:#a5b4fc;border-left:3px solid var(--accent)}
.main-content{flex:1;padding:30px;overflow-y:auto;overflow-x:hidden}
.section-title{font-weight:600;font-size:1.8rem;margin-bottom:25px;display:flex;justify-content:space-between;align-items:center;color:#fff}
.custom-table{width:100%;border-collapse:separate;border-spacing:0 6px}
.custom-table th{color:var(--text-mute);font-weight:600;padding:10px 15px;font-size:.85rem;text-transform:uppercase;letter-spacing:1px}
.custom-table td{background:rgba(51,65,85,.5);padding:12px 15px;vertical-align:middle;border-top:1px solid var(--glass-border);border-bottom:1px solid var(--glass-border);color:#e2e8f0}
.custom-table tr td:first-child{border-top-left-radius:10px;border-bottom-left-radius:10px;border-left:1px solid var(--glass-border)}
.custom-table tr td:last-child{border-top-right-radius:10px;border-bottom-right-radius:10px;border-right:1px solid var(--glass-border)}
.form-control,.form-select{background:rgba(15,23,42,.85);border:1px solid var(--glass-border);color:#f8fafc;border-radius:8px;padding:8px 12px}
.btn-neon{background:var(--accent);color:#fff;border:none;padding:10px 24px;border-radius:8px;font-weight:600;box-shadow:0 4px 15px var(--accent-glow);transition:.3s}
.btn-neon:hover{transform:translateY(-2px);box-shadow:0 8px 25px var(--accent-glow);background:#5558e6}
.btn-icon{background:rgba(255,255,255,.1);color:#fff;border:none;width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;transition:.2s}
.btn-icon:hover{background:#fff;color:#000}
.torrent-card{background:rgba(51,65,85,.4);border:1px solid var(--glass-border);padding:10px 15px;border-radius:8px;margin-bottom:8px;display:flex;align-items:center;gap:10px;font-size:.9rem;color:#cbd5e1;transition:.2s}
.torrent-card:hover{background:rgba(99,102,241,.1);border-color:var(--accent);color:#fff}
.torrent-icon{color:var(--accent);font-size:1.1rem}
.lang-select{background:rgba(0,0,0,.2);border:1px solid var(--glass-border);color:var(--text-mute);font-size:.85rem;padding:8px;border-radius:6px;width:100%;margin-top:20px}
</style>
</head>
<body>
<div class="d-flex h-100">
<div class="sidebar">
<div class="app-title"><i class="bi bi-lightning-charge-fill"></i> Torrent Factory</div>
<div class="nav-item active" onclick="switchView('series')" id="nav-series"><i class="bi bi-tv"></i> Séries</div>
<div class="nav-item" onclick="switchView('movies')" id="nav-movies"><i class="bi bi-film"></i> Films</div>
<div class="nav-item" onclick="switchView('torrents')" id="nav-torrents"><i class="bi bi-folder-check"></i> Torrents</div>
<div class="nav-item" onclick="switchView('tasks')" id="nav-tasks"><i class="bi bi-activity"></i> Tâches</div>
<div class="nav-item" onclick="switchView('logs')" id="nav-logs"><i class="bi bi-terminal"></i> Logs</div>
<div class="mt-auto nav-item" onclick="switchView('config')" id="nav-config"><i class="bi bi-gear-wide-connected"></i> Réglages</div>
<select class="lang-select" id="lang-selector" onchange="changeLang(this.value)">
<option value="fr">Français</option><option value="en">English</option>
</select>
</div>
<div class="main-content">
<div id="view-series" class="view-section">
<div class="section-title"><span>Bibliothèque Séries</span>
<div class="d-flex gap-2">
<button class="btn-icon" onclick="forceScan('series')"><i class="bi bi-arrow-repeat"></i></button>
<button class="btn-neon" onclick="addSeriesBatch()"><i class="bi bi-layers-fill me-2"></i>Tout Générer</button>
</div></div>
<div class="glass-panel p-3 mb-3"><input type="text" id="search_series" class="form-control" placeholder="Rechercher..." onkeyup="renderSeries()"></div>
<div class="glass-panel p-0 overflow-hidden"><table class="custom-table mb-0"><thead><tr>
<th width="40"><input type="checkbox" onchange="toggleAll('series',this)" class="form-check-input"></th>
<th>Nom</th><th>Langue</th><th>Taille</th><th>Mode</th><th class="text-end">Action</th>
</tr></thead><tbody id="list-series"></tbody></table></div>
</div>
<div id="view-movies" class="view-section" style="display:none">
<div class="section-title"><span>Bibliothèque Films</span>
<div class="d-flex gap-2">
<button class="btn-icon" onclick="forceScan('movies')"><i class="bi bi-arrow-repeat"></i></button>
<button class="btn-neon" onclick="addMoviesBatch()"><i class="bi bi-layers-fill me-2"></i>Tout Générer</button>
</div></div>
<div class="glass-panel p-3 mb-3"><input type="text" id="search_movies" class="form-control" placeholder="Rechercher..." onkeyup="renderMovies()"></div>
<div class="glass-panel p-0 overflow-hidden"><table class="custom-table mb-0"><thead><tr>
<th width="40"><input type="checkbox" onchange="toggleAll('movies',this)" class="form-check-input"></th>
<th>Nom</th><th>Langue</th><th>Taille</th><th class="text-end">Action</th>
</tr></thead><tbody id="list-movies"></tbody></table></div>
</div>
<div id="view-tasks" class="view-section" style="display:none">
<div class="section-title"><span>Activités en cours</span>
<button class="btn-icon text-danger" onclick="clearTasks()"><i class="bi bi-trash"></i></button>
</div>
<div id="container-tasks"></div>
</div>
<div id="view-torrents" class="view-section" style="display:none">
<div class="section-title"><span>Torrents Créés</span>
<button class="btn-icon" onclick="loadTorrents()"><i class="bi bi-arrow-repeat"></i></button>
</div>
<div class="row">
<div class="col-6"><div class="glass-panel p-4"><h5 class="text-white mb-4 border-bottom border-secondary pb-2">Séries</h5><div id="torrents-series"></div></div></div>
<div class="col-6"><div class="glass-panel p-4"><h5 class="text-white mb-4 border-bottom border-secondary pb-2">Films</h5><div id="torrents-movies"></div></div></div>
</div>
</div>
<div id="view-config" class="view-section" style="display:none">
<div class="section-title">Configuration</div>
<div class="glass-panel p-5" style="max-width:980px"><div class="row g-4">
<div class="col-6"><label class="text-info fw-bold mb-1 small">SERIES (SOURCE)</label>
<div class="input-group"><input id="conf_series_root" class="form-control bg-dark">
<button class="btn btn-outline-info" onclick="openPicker('conf_series_root')">Parcourir</button></div></div>
<div class="col-6"><label class="text-info fw-bold mb-1 small">SERIES (DEST)</label>
<div class="input-group"><input id="conf_series_out" class="form-control bg-dark">
<button class="btn btn-outline-info" onclick="openPicker('conf_series_out')">Parcourir</button></div></div>
<div class="col-6"><label class="text-info fw-bold mb-1 small">MOVIES (SOURCE)</label>
<div class="input-group"><input id="conf_movies_root" class="form-control bg-dark">
<button class="btn btn-outline-info" onclick="openPicker('conf_movies_root')">Parcourir</button></div></div>
<div class="col-6"><label class="text-info fw-bold mb-1 small">MOVIES (DEST)</label>
<div class="input-group"><input id="conf_movies_out" class="form-control bg-dark">
<button class="btn btn-outline-info" onclick="openPicker('conf_movies_out')">Parcourir</button></div></div>
<div class="col-12"><label class="text-info fw-bold mb-1 small">TRACKER URL</label>
<input id="conf_tracker" class="form-control bg-dark" placeholder="udp://tracker.exemple:6969/announce"></div>
<div class="col-4"><label class="text-info fw-bold mb-1 small">PIECE SIZE (0=auto)</label>
<input id="conf_piece_size" type="number" class="form-control bg-dark" min="0"></div>
<div class="col-4"><label class="text-info fw-bold mb-1 small">MAX WORKERS</label>
<input id="conf_max_workers" type="number" class="form-control bg-dark" min="1" max="8"></div>
<div class="col-4"><label class="text-info fw-bold mb-1 small">TIMEOUT (sec)</label>
<input id="conf_timeout" type="number" class="form-control bg-dark" min="60"></div>
<div class="col-12 d-flex gap-5 mt-2 p-3 rounded" style="background:rgba(0,0,0,0.2)">
<div class="form-check form-switch"><input class="form-check-input" type="checkbox" id="conf_analyze_audio">
<label class="form-check-label text-white">Analyse Audio (FFprobe)</label></div>
<div class="form-check form-switch"><input class="form-check-input" type="checkbox" id="conf_private">
<label class="form-check-label text-white">Privé (-P)</label></div>
<div class="form-check form-switch"><input class="form-check-input" type="checkbox" id="conf_show_size">
<label class="form-check-label text-white">Taille (Scan lent)</label></div>
</div>
<div class="col-12 mt-2"><button class="btn-neon w-100 py-3" onclick="saveConfig()">ENREGISTRER</button></div>
</div></div>
</div>
<div id="view-logs" class="view-section" style="display:none">
<div class="section-title"><span>Logs</span>
<button class="btn-icon" onclick="clearLogView()"><i class="bi bi-eraser"></i></button>
</div>
<div id="log-container" class="glass-panel p-3" style="font-family:monospace;height:500px;overflow:auto;color:#a5b4fc"></div>
</div>
</div>
</div>
<div class="modal fade" id="pickerModal" tabindex="-1">
<div class="modal-dialog modal-lg"><div class="modal-content bg-dark text-white">
<div class="modal-header"><h5 class="modal-title">Choisir un dossier</h5>
<button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button></div>
<div class="modal-body">
<div class="d-flex justify-content-between align-items-center mb-2">
<div id="pickerPath" class="small text-info"></div>
<div class="d-flex gap-2">
<button class="btn btn-sm btn-secondary" onclick="pickerUp()">⬆</button>
<button class="btn btn-sm btn-outline-info" onclick="pickerRoots()">Racines</button>
</div></div>
<div id="pickerList"></div>
</div>
<div class="modal-footer"><button class="btn btn-success" onclick="pickerSelect()">Utiliser ce dossier</button></div>
</div></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
let DATA={series:[],movies:[]};
function changeLang(l){apiPost('config',{lang:l})}
function switchView(v){document.querySelectorAll('.view-section').forEach(e=>e.style.display='none');document.querySelectorAll('.nav-item').forEach(e=>e.classList.remove('active'));document.getElementById('view-'+v).style.display='block';document.getElementById('nav-'+v).classList.add('active');if(v==='torrents')loadTorrents();if(v==='tasks')refreshTasks()}
const makeTagSelect=(id,val)=>{const opts=['MULTI','FRENCH','VOSTFR','VO','TRUEFRENCH'];return`<select id="${id}" class="form-select form-select-sm" style="width:120px;"><option value="">Auto</option>${opts.map(o=>`<option value="${o}" ${o===val?'selected':''}>${o}</option>`).join('')}</select>`};
async function apiGet(e){return fetch('/api/'+e)}
async function apiPost(e,d){return fetch('/api/'+e,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d||{})})}
async function loadLibrary(){DATA.series=await(await apiGet('library/series')).json();DATA.movies=await(await apiGet('library/movies')).json();renderSeries();renderMovies()}
async function forceScan(t){if(t==='series'){document.getElementById('list-series').innerHTML='<tr><td colspan="6" class="text-center p-5 text-white">Scan...</td></tr>';DATA.series=await(await fetch('/api/scan/series',{method:'POST'})).json();renderSeries()}else{document.getElementById('list-movies').innerHTML='<tr><td colspan="5" class="text-center p-5 text-white">Scan...</td></tr>';DATA.movies=await(await fetch('/api/scan/movies',{method:'POST'})).json();renderMovies()}}
function renderSeries(){const q=(document.getElementById('search_series').value||'').toLowerCase();const list=DATA.series.filter(i=>(i.name||'').toLowerCase().includes(q));document.getElementById('list-series').innerHTML=list.map((s,i)=>`<tr><td><input type="checkbox" class="chk-series form-check-input" value="${i}" checked></td><td class="fw-bold text-white">${s.name}</td><td>${makeTagSelect(`tag-s-${i}`,s.detected_tag)}</td><td class="small text-info">${s.size?(s.size/1024/1024/1024).toFixed(2)+' GB':'-'}</td><td><select id="mode-s-${i}" class="form-select form-select-sm"><option value="complete">Pack</option><option value="season">Saison</option><option value="episode">EP</option></select></td><td class="text-end"><button class="btn btn-sm btn-outline-warning" onclick="createSingle('series',${i})"><i class="bi bi-lightning-fill"></i></button></td></tr>`).join('')||'<tr><td colspan="6" class="text-center p-4 text-muted">Vide</td></tr>'}
function renderMovies(){const q=(document.getElementById('search_movies').value||'').toLowerCase();const list=DATA.movies.filter(i=>(i.name||'').toLowerCase().includes(q));document.getElementById('search_movies').value||'').toLowerCase();const list=DATA.movies.filter(i=>(i.name||'').toLowerCase().includes(q));document.getElementById('list-movies').innerHTML=list.map((m,i)=>`<tr><td><input type="checkbox" class="chk-movies form-check-input" value="${i}" checked></td><td class="fw-bold text-white">${m.name}</td><td>${makeTagSelect(`tag-m-${i}`,m.detected_tag)}</td><td class="small text-info">${m.size?(m.size/1024/1024/1024).toFixed(2)+' GB':'-'}</td><td class="text-end"><button class="btn btn-sm btn-outline-warning" onclick="createSingle('movie',${i})"><i class="bi bi-lightning-fill"></i></button></td></tr>`).join('')||'<tr><td colspan="5" class="text-center p-4 text-muted">Vide</td></tr>'}
function createSingle(type,index){const list=type==='series'?DATA.series:DATA.movies;const item=list[index];const prefix=type==='series'?'s':'m';const taskItem={...item,mode:type==='series'?document.getElementById(`mode-${prefix}-${index}`).value:'movie',lang_tag:document.getElementById(`tag-${prefix}-${index}`).value};apiPost('tasks/add',{type,tasks:[taskItem]}).then(()=>switchView('tasks'))}
function addSeriesBatch(){const tasks=[];document.querySelectorAll('.chk-series:checked').forEach(c=>{const idx=parseInt(c.value);tasks.push({...DATA.series[idx],mode:document.getElementById(`mode-s-${idx}`).value,lang_tag:document.getElementById(`tag-s-${idx}`).value})});if(tasks.length)apiPost('tasks/add',{type:'series',tasks}).then(()=>switchView('tasks'))}
function addMoviesBatch(){const tasks=[];document.querySelectorAll('.chk-movies:checked').forEach(c=>{const idx=parseInt(c.value);tasks.push({...DATA.movies[idx],mode:'movie',lang_tag:document.getElementById(`tag-m-${idx}`).value})});if(tasks.length)apiPost('tasks/add',{type:'movie',tasks}).then(()=>switchView('tasks'))}
async function refreshTasks(){const tasks=await(await apiGet('tasks/list')).json();const container=document.getElementById('container-tasks');if(!tasks||!tasks.length){container.innerHTML='<div class="text-center text-muted p-5">Aucune tâche.</div>';return}const color=s=>({running:'#6366f1',completed:'#10b981',error:'#ef4444',cancelled:'#f59e0b',pending:'#94a3b8'}[s]||'#94a3b8');container.innerHTML=tasks.slice().reverse().map(t=>`<div class="glass-panel p-4 mb-3" style="border-left:4px solid ${color(t.status)}"><div class="d-flex justify-content-between mb-2 align-items-center"><div class="fw-bold text-white fs-5">${t.name}</div>${['running','pending'].includes(t.status)?`<button class="btn btn-sm btn-danger" onclick="cancelTask('${t.id}')">STOP</button>`:`<span class="badge ${t.status==='completed'?'bg-success':(t.status==='error'?'bg-danger':'bg-warning')}">${(t.status||'').toUpperCase()}</span>`}</div>${t.error_msg?`<div class="alert alert-danger py-2 mb-2">${t.error_msg}</div>`:''}<div class="d-flex justify-content-between text-white small mb-1"><span>${t.current_item_name} <span class="text-info ms-2">${t.current_detail||''}</span></span><span class="fw-bold text-warning">${t.eta_item||'--:--'}</span></div><div class="progress mb-2" style="height:8px;background:rgba(255,255,255,0.1);"><div class="progress-bar bg-info" style="width:${t.progress_item||0}%"></div></div><div class="progress" style="height:4px;background:rgba(255,255,255,0.05);"><div class="progress-bar bg-success" style="width:${t.progress_global||0}%"></div></div><div class="text-muted small mt-2">${t.current_item_index||''} • ${t.created_at||''}</div></div>`).join('')}
function cancelTask(id){apiPost('tasks/cancel',{id})}
function clearTasks(){fetch('/api/tasks/clear').then(()=>refreshTasks())}
async function loadTorrents(){const d=await(await apiGet('torrents')).json();const tpl=l=>(l||[]).map(f=>`<div class="torrent-card"><i class="bi bi-file-earmark-check-fill torrent-icon"></i><div class="text-truncate">${f.name}</div></div>`).join('')||'<div class="text-muted p-2">Vide</div>';document.getElementById('torrents-series').innerHTML=tpl(d.series);document.getElementById('torrents-movies').innerHTML=tpl(d.movies)}
async function loadConfig(){const c=await(await apiGet('config')).json();document.getElementById('conf_series_root').value=c.series_root||'';document.getElementById('conf_series_out').value=c.series_out||'';document.getElementById('conf_movies_root').value=c.movies_root||'';document.getElementById('conf_movies_out').value=c.movies_out||'';document.getElementById('conf_tracker').value=c.tracker_url||'';document.getElementById('conf_piece_size').value=c.piece_size??0;document.getElementById('conf_max_workers').value=c.max_workers??2;document.getElementById('conf_timeout').value=c.torrent_timeout_sec??7200;document.getElementById('conf_analyze_audio').checked=!!c.analyze_audio;document.getElementById('conf_private').checked=!!c.private;document.getElementById('conf_show_size').checked=!!c.show_size;if(c.lang)document.getElementById('lang-selector').value=c.lang;await loadLibrary()}
async function saveConfig(){const payload={series_root:document.getElementById('conf_series_root').value,series_out:document.getElementById('conf_series_out').value,movies_root:document.getElementById('conf_movies_root').value,movies_out:document.getElementById('conf_movies_out').value,tracker_url:document.getElementById('conf_tracker').value,piece_size:parseInt(document.getElementById('conf_piece_size').value||'0')||0,max_workers:parseInt(document.getElementById('conf_max_workers').value||'2')||2,torrent_timeout_sec:parseInt(document.getElementById('conf_timeout').value||'7200')||7200,analyze_audio:document.getElementById('conf_analyze_audio').checked,private:document.getElementById('conf_private').checked,show_size:document.getElementById('conf_show_size').checked,lang:document.getElementById('lang-selector').value};await apiPost('config',payload);alert("Configuration enregistrée. Redémarrer si changement max_workers.")}
function toggleAll(t,s){document.querySelectorAll('.chk-'+t).forEach(c=>c.checked=s.checked)}
let LOG_AFTER=0;
function clearLogView(){document.getElementById('log-container').innerHTML='';LOG_AFTER=0}
async function refreshLogs(){const logs=await(await fetch('/api/logs?after='+LOG_AFTER+'&limit=500')).json();if(!logs||!logs.length)return;LOG_AFTER=logs[logs.length-1].id;const container=document.getElementById('log-container');const atBottom=(container.scrollTop+container.clientHeight)>=(container.scrollHeight-10);container.insertAdjacentHTML('beforeend',logs.map(x=>`<div><span class="text-secondary">[${x.time}]</span> ${x.msg}</div>`).join(''));if(container.childNodes.length>2000){for(let i=0;i<500;i++)container.removeChild(container.firstChild)}if(atBottom)container.scrollTop=container.scrollHeight}
let PICKER_INPUT=null;let PICKER_CURRENT=null;let pickerModal=null;
async function openPicker(inputId){PICKER_INPUT=inputId;if(!pickerModal)pickerModal=new bootstrap.Modal(document.getElementById('pickerModal'));const currentValue=(document.getElementById(inputId).value||'').trim();if(currentValue){await pickerGo(currentValue)}else{await pickerRoots()}pickerModal.show()}
async function pickerRoots(){const drives=await(await fetch('/api/drives')).json();const list=drives||[];document.getElementById('pickerPath').innerText='Racines';document.getElementById('pickerList').innerHTML=list.map(d=>`<div class="torrent-card" style="cursor:pointer" onclick="pickerGo(${JSON.stringify(d.path)})"><i class="bi bi-hdd-fill torrent-icon"></i><div class="text-truncate">${d.name}</div></div>`).join('')||'<div class="text-muted p-2">Aucune racine</div>';PICKER_CURRENT=null}
async function pickerGo(path){const d=await(await fetch('/api/browse?path='+encodeURIComponent(path))).json();PICKER_CURRENT=d.current;document.getElementById('pickerPath').innerText=PICKER_CURRENT;const items=d.items||[];document.getElementById('pickerList').innerHTML=items.map(x=>`<div class="torrent-card" style="cursor:pointer" onclick="pickerGo(${JSON.stringify(x.path)})"><i class="bi bi-folder-fill torrent-icon"></i><div class="text-truncate">${x.name}</div></div>`).join('')||'<div class="text-muted p-2">Vide</div>'}
function pickerUp(){if(!PICKER_CURRENT)return pickerRoots();const p=PICKER_CURRENT.replace(/[\\/]+$/,'');const idx1=p.lastIndexOf('/');const idx2=p.lastIndexOf('\\');const idx=Math.max(idx1,idx2);if(idx<=0)return pickerRoots();pickerGo(p.substring(0,idx))}
function pickerSelect(){if(PICKER_INPUT&&PICKER_CURRENT){document.getElementById(PICKER_INPUT).value=PICKER_CURRENT}if(pickerModal)pickerModal.hide()}
document.addEventListener('DOMContentLoaded',async()=>{await loadConfig();setInterval(refreshTasks,1200);setInterval(refreshLogs,1000)});
</script>
</body>
</html>"""

# ============================================================
# ÉTAPE 11 : Lancement du serveur
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  🚀 TORRENT FACTORY V38 - DÉMARRAGE")
    print("=" * 60)
    print(f"  📂 Configuration: {APP_DATA}")
    print(f"  🌐 Interface Web: http://localhost:5000")
    print(f"  🔧 FFprobe: {'✓ Activé' if HAS_FFPROBE else '✗ Désactivé'}")
    print(f"  👷 Workers: {CONFIG['max_workers']}")
    print("=" * 60)
    print()
    
    log_system("Serveur démarré", "info")
    
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur...")
        log_system("Serveur arrêté", "info")