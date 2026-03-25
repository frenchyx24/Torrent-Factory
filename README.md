<div align="center">

# ⚡ Torrent Factory V1.3.0
### *Automatisation ultime avec moteur Titanium asynchrone*

[![Version](https://img.shields.io/badge/version-1.3.0-indigo?style=for-the-badge)](https://github.com/${GITHUB_REPOSITORY})
[![Docker](https://img.shields.io/badge/Docker-Stable-blue?style=for-the-badge&logo=docker)](https://github.com/${GITHUB_REPOSITORY}/pkgs/container/torrent-factory)

**La V1.3.0** est la version de référence, utilisant un moteur mktorrent natif avec un processeur de tâches asynchrone pour une stabilité parfaite.

</div>

---

## 🚀 Installation V1.3.0

```bash
docker run -d \
  --name torrent-factory \
  -p 5000:5000 \
  -v /votre/chemin/config:/config \
  -v /votre/chemin/series:/data/series \
  -v /votre/chemin/movies:/data/movies \
  -v /votre/chemin/torrents:/data/torrents \
  ghcr.io/votre-repo/torrent-factory:latest
```

### ✨ Nouveautés V1.3.0
- **Moteur Titanium** : Traitement des tâches en arrière-plan sans bloquer l'API.
- **Correction Torrents** : Les fichiers sont désormais créés avec les bons noms et tags.
- **Stabilité** : Correction des fuites de mémoire et des blocages de threads.
- **UI** : Version unifiée v1.3.0.