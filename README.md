<div align="center">

# ⚡ Torrent Factory

<img src="https://raw.githubusercontent.com/lucide-react/lucide/main/icons/lightning.svg" width="80" height="80" />

**Le générateur de torrents nouvelle génération.**  
*Automatisez votre bibliothèque avec une interface web ultra-fluide.*

[![Docker Build](https://img.shields.io/github/actions/workflow/status/frenchyx24/Torrent-Factory/docker-publish.yml?style=for-the-badge&logo=docker&logoColor=white&color=2496ED)](https://github.com/frenchyx24/Torrent-Factory/actions)
[![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge&logo=github&color=6366f1)](https://github.com/frenchyx24/Torrent-Factory/releases)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

[Fonctionnalités](#-fonctionnalités) • [Installation Rapide](#-installation-rapide) • [Docker](#-docker) • [Configuration](#-configuration)

</div>

---

## ✨ Pourquoi Torrent Factory ?

Torrent Factory n'est pas juste un script. C'est une solution complète pour les passionnés de médias qui veulent gagner du temps.

*   🚀 **Interface Moderne** : Dashboard React sombre, réactif et intuitif.
*   🔍 **Scan Intelligent** : Détecte automatiquement vos nouvelles séries et films.
*   🔊 **Analyse Audio** : Utilise FFprobe pour identifier les langues (MULTI, FRENCH, VOSTFR).
*   📦 **Auto-Suffisant** : Le script Python gère ses propres dépendances.
*   🐳 **Cloud Ready** : Déploiement instantané via Docker & GHCR.

---

## 🚀 Installation Rapide

Pas envie de configurer ? Lancez cette commande et laissez la magie opérer :

```bash
curl -sSL https://raw.githubusercontent.com/frenchyx24/Torrent-Factory/main/install.sh | bash
```

---

## 🐳 Déploiement Docker

### ⚡ One-Liner (Instantané)
```bash
docker run -d \
  --name torrent-factory \
  -p 5000:5000 \
  -v $(pwd)/config:/config \
  -v /votre/chemin/series:/data/series \
  ghcr.io/frenchyx24/torrent-factory:latest
```

### 🛠 Docker Compose
```yaml
version: '3.8'
services:
  torrent-factory:
    image: ghcr.io/frenchyx24/torrent-factory:latest
    ports:
      - "5000:5000"
    volumes:
      - ./config:/config
      - /media/series:/data/series
    restart: unless-stopped
```

---

## ⚙️ Configuration

1.  Lancez l'application.
2.  Ouvrez `http://localhost:5000` dans votre navigateur.
3.  Allez dans l'onglet **Réglages** pour définir vos dossiers sources.
4.  Cliquez sur **Scanner** et commencez à générer !

---

## 🛠 Tech Stack

- **Frontend** : React 19, Tailwind CSS, Shadcn/UI, Lucide Icons.
- **Backend** : Python 3, Flask, Py3CreateTorrent.
- **Analyse** : FFmpeg / FFprobe.

---

<div align="center">

Développé avec ❤️ par [**frenchyx24**](https://github.com/frenchyx24)

</div>