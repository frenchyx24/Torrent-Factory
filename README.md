<div align="center">

# ⚡ Torrent Factory V1.0.4
### *L'automatisation ultime pour votre bibliothèque média*

[![Version](https://img.shields.io/badge/version-1.0.4-indigo?style=for-the-badge)](https://github.com/${GITHUB_REPOSITORY})
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)](https://github.com/${GITHUB_REPOSITORY}/pkgs/container/torrent-factory)
[![License](https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge)](LICENSE)

**Torrent Factory** est une solution web "all-in-one" conçue pour transformer vos dossiers de films et séries en fichiers `.torrent` prêts à être partagés.

</div>

---

## 🌟 Nouveautés V1.0.4

- 🛠️ **Task Engine Fix** : Création réelle des fichiers `.torrent` après la fin de la progression.
- 📂 **Sorted Lists** : Les torrents et les éléments de bibliothèque sont maintenant triés par ordre alphabétique.
- 🚀 **Stability** : Amélioration du traitement des tâches en arrière-plan.
- 🎨 **UI Contrast Fix** : Correction des boutons illisibles, meilleure visibilité globale.
- 🟢 **Green Switches** : Les options actives sont maintenant clairement identifiées en vert émeraude.

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