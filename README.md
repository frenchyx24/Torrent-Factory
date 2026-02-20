<div align="center">

# ⚡ Torrent Factory V1.0.5
### *L'automatisation ultime pour votre bibliothèque média*

[![Version](https://img.shields.io/badge/version-1.0.5-indigo?style=for-the-badge)](https://github.com/${GITHUB_REPOSITORY})
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)](https://github.com/${GITHUB_REPOSITORY}/pkgs/container/torrent-factory)
[![License](https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge)](LICENSE)

**Torrent Factory** est une solution web "all-in-one" conçue pour transformer vos dossiers de films et séries en fichiers `.torrent` prêts à être partagés.

</div>

---

## 🌟 Nouveautés V1.0.5

- 📏 **Real Sizes** : Calcul dynamique de la taille des dossiers et fichiers sur le disque.
- 🏷️ **Language Tags** : Les torrents générés incluent désormais le tag de langue dans le nom du fichier (ex: `Nom [FRENCH].torrent`).
- 💾 **Config Persistence** : Amélioration du moteur de fusion de configuration pour éviter toute perte de réglages lors des mises à jour.
- 🔢 **Version Sync** : Harmonisation de la version v1.0.5 sur l'ensemble de l'interface et du backend.
- 📂 **Sorted Lists** : Tri alphabétique maintenu pour une meilleure lisibilité.

---

## 🚀 Installation Rapide

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

---
{/* ... reste du README */}