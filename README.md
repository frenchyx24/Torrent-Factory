<div align="center">

# ⚡ Torrent Factory V1.0.9
### *L'automatisation ultime avec mktorrent engine*

[![Version](https://img.shields.io/badge/version-1.0.9-indigo?style=for-the-badge)](https://github.com/${GITHUB_REPOSITORY})
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)](https://github.com/${GITHUB_REPOSITORY}/pkgs/container/torrent-factory)

**Torrent Factory V1.0.9** utilise désormais `mktorrent`, garantissant une stabilité absolue lors du déploiement et de la génération des fichiers.

</div>

---

## 🚀 Installation V1.0.9

```bash
docker run -d \
  --name torrent-factory \
  -p 5000:5000 \
  -v /votre/chemin/config:/config \
  -v /votre/chemin/series:/data/series \
  -v /votre/chemin/movies:/data/movies \
  -v /votre/chemin/torrents:/data/torrents \
  ghcr.io/votre-repo/torrent-factory:latest