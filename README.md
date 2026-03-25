# ⚡ Torrent Factory V1.0 Stable

[Français](#français) | [English](#english)

---

<a name="français"></a>
## 🇫🇷 Français - Documentation Détaillée

**Torrent Factory** est une solution "self-hosted" conçue pour automatiser la création de fichiers `.torrent` à grande échelle. Idéal pour les gestionnaires de serveurs de médias ou les créateurs de contenu souhaitant unifier leur flux de travail.

### 🛠 Comment ça marche ?
L'outil repose sur une architecture à trois couches :
1.  **Interface Utilisateur (React 19)** : Une interface moderne sous Tailwind CSS qui communique via une API REST.
2.  **API Backend (Python/Flask)** : Gère la logique métier, le scan des bibliothèques et l'orchestration des tâches.
3.  **Moteur Stable (mktorrent)** : Utilise l'outil système natif `mktorrent` pour une performance brute et une consommation mémoire minimale.

### ✨ Fonctionnalités
- **Scan Intelligent** : Détecte les nouveaux dossiers et fichiers dans vos racines "Séries" et "Films".
- **File d'Attente Asynchrone** : Le "Moteur Stable" traite les tâches en arrière-plan. Vous pouvez fermer l'onglet, la création continue sur le serveur.
- **Modes de Génération (Séries)** : 
    - *Pack Complet* : Crée un seul torrent pour tout le dossier de la série.
    - *Par Saison* : Crée un torrent distinct pour chaque sous-dossier de saison.
    - *Par Épisode* : Crée un torrent pour chaque fichier individuel.
- **Explorateur de Fichiers** : Un sélecteur de dossiers visuel pour configurer vos chemins sans erreurs de frappe.
- **Monitoring** : Barre de progression en temps réel et console de logs pour débugger les erreurs (permissions, chemins manquants, etc.).

### 🚀 Installation (Docker)
```bash
docker run -d \
  --name torrent-factory \
  -p 5000:5000 \
  -v /votre/config:/config \
  -v /vos/series:/data/series \
  -v /vos/films:/data/movies \
  -v /vos/sorties:/data/torrents \
  votre-image:latest
```

---

<a name="english"></a>
## 🇺🇸 English - Detailed Documentation

**Torrent Factory** is a self-hosted solution designed to automate the creation of `.torrent` files at scale. Perfect for media server managers or content creators looking to unify their workflow.

### 🛠 How it works
The tool is built on a three-layer architecture:
1.  **User Interface (React 19)**: A modern interface using Tailwind CSS that communicates via a REST API.
2.  **Backend API (Python/Flask)**: Handles business logic, library scanning, and task orchestration.
3.  **Stable Engine (mktorrent)**: Uses the native `mktorrent` system tool for raw performance and minimal memory footprint.

### ✨ Key Features
- **Smart Scanning**: Instantly detects new folders and files in your "Series" and "Movies" roots.
- **Asynchronous Queue**: The "Stable Engine" processes tasks in the background. You can close the tab, and the creation continues on the server.
- **Generation Modes (Series)**: 
    - *Complete Pack*: Creates one torrent for the entire series folder.
    - *By Season*: Creates a separate torrent for each season sub-folder.
    - *By Episode*: Creates a torrent for every single file.
- **File Explorer**: A visual folder picker to configure your paths without typing errors.
- **Monitoring**: Real-time progress bar and log console to debug errors (permissions, missing paths, etc.).

### ⚙️ Configuration
- **Tracker URL**: Set your private tracker announce URL.
- **Piece Size**: Default is 21 (2MB), optimized for most private trackers.
- **Private Mode**: Automatically sets the "private" flag to prevent DHT/PEX leaks.

### 🚀 Deployment (Docker)
```bash
docker run -d \
  --name torrent-factory \
  -p 5000:5000 \
  -v /your/config:/config \
  -v /your/series:/data/series \
  -v /your/movies:/data/movies \
  -v /your/outputs:/data/torrents \
  your-image:latest