# ⚡ Torrent Factory V1

[![Docker Build](https://github.com/frenchyx24/Torrent-Factory/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/frenchyx24/Torrent-Factory/actions)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/frenchyx24/Torrent-Factory/releases)

Torrent Factory est un générateur automatique de torrents ultra-moderne avec une interface web intuitive. Il scanne vos dossiers, analyse les pistes audio et génère vos fichiers `.torrent` en masse.

## 🚀 Installation Express (Windows & Linux)

Ouvrez un terminal et lancez cette commande pour installer et démarrer Torrent Factory instantanément :

```bash
curl -sSL https://raw.githubusercontent.com/frenchyx24/Torrent-Factory/main/install.sh | bash
```

## 🛠 Méthodes d'Installation

### 🐳 Docker (Recommandé)
Idéal pour les serveurs (Unraid, TrueNAS, Synology).
```bash
docker-compose up -d
```

### 🐍 Python (Manuel)
Le script installe automatiquement ses propres dépendances au premier lancement.
```bash
git clone https://github.com/frenchyx24/Torrent-Factory.git
cd Torrent-Factory
python3 main.py
```

## 🌟 Fonctionnalités
- **Auto-Dépendances** : Le script installe tout seul ce dont il a besoin.
- **Multi-Plateforme** : Fonctionne parfaitement sur Windows et Linux.
- **Analyse FFprobe** : Détection automatique des langues (MULTI, FRENCH, VOSTFR).
- **Interface React** : Dashboard fluide et sombre.

## ⚙️ Configuration
Une fois lancé, rendez-vous sur `http://localhost:5000` pour configurer vos dossiers médias.

---
Développé par **frenchyx24**. Propulsé par la passion du partage.