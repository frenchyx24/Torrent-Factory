# ⚡ Torrent Factory V1

[![Docker Build](https://github.com/frenchyx24/Torrent-Factory/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/frenchyx24/Torrent-Factory/actions)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/frenchyx24/Torrent-Factory/releases)

Générateur automatique de torrents avec interface web moderne.

## 🐳 Installation Docker (La plus simple)

### Option 1 : Docker Run (One-liner)
Lancez l'application instantanément sans rien télécharger d'autre :
```bash
docker run -d \
  --name torrent-factory \
  -p 5000:5000 \
  -v $(pwd)/config:/config \
  -v /votre/chemin/series:/data/series \
  ghcr.io/frenchyx24/torrent-factory:latest
```

### Option 2 : Docker Compose
Créez un fichier `docker-compose.yml` et lancez :
```bash
docker-compose up -d
```

## 🚀 Installation Script (Linux/Windows)
```bash
curl -sSL https://raw.githubusercontent.com/frenchyx24/Torrent-Factory/main/install.sh | bash
```

## 🌟 Fonctionnalités
- **Image Docker prête à l'emploi** sur GHCR.
- **Auto-installation** des dépendances Python.
- **Analyse FFprobe** intégrée pour les langues.
- **Interface React** fluide et réactive.

---
Développé par **frenchyx24**.