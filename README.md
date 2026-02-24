<div align="center">

# ⚡ Torrent Factory v1.0.12-test
### *L'automatisation ultime avec mktorrent engine*

[![Version](https://img.shields.io/badge/version-1.0.12-test-indigo?style=for-the-badge)](https://github.com/${GITHUB_REPOSITORY})
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)](https://github.com/${GITHUB_REPOSITORY}/pkgs/container/torrent-factory)

**Torrent Factory v1.0.12-test** utilise désormais `mktorrent`, avec corrections et fiabilisations complètes pour le scan et la génération.

</div>

---

## 🚀 Installation v1.0.12-test

```bash
docker run -d \
  --name torrent-factory \
  -p 5000:5000 \
  -v /votre/chemin/config:/config \
  -v /votre/chemin/series:/data/series \
  -v /votre/chemin/movies:/data/movies \
  -v /votre/chemin/torrents:/data/torrents \
  ghcr.io/votre-repo/torrent-factory:latest