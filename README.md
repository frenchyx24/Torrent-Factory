<div align="center">

# ⚡ Torrent Factory V1.0.3
### *L'automatisation ultime pour votre bibliothèque média*

[![Version](https://img.shields.io/badge/version-1.0.3-indigo?style=for-the-badge)](https://github.com/${GITHUB_REPOSITORY})
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)](https://github.com/${GITHUB_REPOSITORY}/pkgs/container/torrent-factory)
[![License](https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge)](LICENSE)

**Torrent Factory** est une solution web "all-in-one" conçue pour transformer vos dossiers de films et séries en fichiers `.torrent` prêts à être partagés.

</div>

---

## 🌟 Nouveautés V1.0.3

- 🎨 **UI Contrast Fix** : Correction des boutons illisibles, meilleure visibilité globale.
- 🟢 **Green Switches** : Les options actives sont maintenant clairement identifiées en vert émeraude.
- 🔄 **Smart Update** : Le moteur fusionne maintenant les nouvelles options par défaut avec votre `config.json` existant sans rien écraser.
- ⏳ **Real-time Tasks** : Simulation réelle de la progression des tâches (0% -> 100%) dans l'onglet Activités.
- 🛠️ **Scan Fix** : Correction du bug qui vidait la page lors d'un rafraîchissement de bibliothèque.

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