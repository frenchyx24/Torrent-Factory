<div align="center">

# ⚡ Torrent Factory v1.0.13-test
### *L'automatisation ultime avec mktorrent engine*

[![Version](https://img.shields.io/badge/version-1.0.13-test-indigo?style=for-the-badge)](https://github.com/${GITHUB_REPOSITORY})
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)](https://github.com/${GITHUB_REPOSITORY}/pkgs/container/torrent-factory)

**Torrent Factory v1.0.13-test** : All-in-One Docker multi-stage build, `mktorrent` intégré, avec corrections et fiabilisations complètes.

</div>

---

## 🚀 Installation v1.0.13-test

```bash
docker run -d \
  --name torrent-factory \
  -p 5000:5000 \
  -v /votre/chemin/config:/config \
  -v /votre/chemin/series:/data/series \
  -v /votre/chemin/movies:/data/movies \
  -v /votre/chemin/torrents:/data/torrents \
  ghcr.io/votre-repo/torrent-factory:latest