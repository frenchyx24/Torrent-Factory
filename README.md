<div align="center">

# ⚡ Torrent Factory V1.1.0
### *Automatisation ultime avec moteur mktorrent natif*

[![Version](https://img.shields.io/badge/version-1.1.0-indigo?style=for-the-badge)](https://github.com/${GITHUB_REPOSITORY})
[![Docker](https://img.shields.io/badge/Docker-Stable-blue?style=for-the-badge&logo=docker)](https://github.com/${GITHUB_REPOSITORY}/pkgs/container/torrent-factory)

**La V1.1.0** est la version de référence, utilisant un moteur mktorrent natif pour une performance et une stabilité inégalées lors de la création de torrents.

</div>

---

## 🚀 Installation V1.1.0

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

### ✨ Nouveautés V1.1.0
- **Moteur natif** : Plus de dépendances Python lourdes pour le hachage.
- **Sécurité** : Gestion robuste des permissions Docker.
- **Performance** : Build ultra-rapide.
- **UI** : Nouvelle interface "Gold" plus fluide.