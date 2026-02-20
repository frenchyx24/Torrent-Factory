<div align="center">

# ⚡ Torrent Factory V38
### *L'automatisation ultime pour votre bibliothèque média*

[![Version](https://img.shields.io/badge/version-38.0.0-indigo?style=for-the-badge)](https://github.com/${GITHUB_REPOSITORY})
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)](https://github.com/${GITHUB_REPOSITORY}/pkgs/container/torrent-factory)
[![License](https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge)](LICENSE)

**Torrent Factory** est une solution web "all-in-one" conçue pour transformer vos dossiers de films et séries en fichiers `.torrent` prêts à être partagés, le tout via une interface moderne et ultra-fluide.

[Fonctionnement](#-comment-ça-marche) • [Installation](#-installation-rapide) • [Configuration](#-configuration) • [Stack Technique](#-stack-technique)

</div>

---

## 🌟 Points Forts

- 🚀 **Interface Glassmorphism** : Une expérience utilisateur réactive bâtie avec React et Tailwind CSS.
- 🔍 **Scan Intelligent** : Détection automatique des nouveaux contenus dans vos répertoires.
- 🔊 **Analyse FFprobe** : Détection réelle des langues (MULTI, VFF, VOSTFR) via l'analyse des pistes audio.
- ⚙️ **Moteur V38** : Gestion des tâches en arrière-plan avec file d'attente et workers multiples.
- 🛡️ **Exclusions Avancées** : Nettoyage automatique des torrents (ignore les `.plexmatch`, `theme.mp3`, etc.).
- 🐳 **Docker Native** : Déploiement en une seule commande avec persistance des données.

---

## 🛠 Comment ça marche ?

Le processus est divisé en 5 étapes clés pour garantir une automatisation totale :

### 1. Configuration des Sources
Dès le premier lancement, vous définissez vos répertoires de données (`/data/series`, `/data/movies`) et vos dossiers de sortie. Vous configurez également vos trackers et vos préférences de création (taille des pièces, mode privé).

### 2. Scan & Indexation
L'application scanne vos dossiers. Pour chaque élément trouvé, elle calcule la taille totale et prépare les métadonnées.
- **Séries** : Détection des structures par saisons ou épisodes.
- **Films** : Identification des fichiers uniques.

### 3. Analyse Média (FFprobe)
C'est le cœur de l'intelligence V38. Le moteur analyse les flux audio des fichiers vidéo pour déterminer si le contenu est en Français, Anglais ou Multi-langues, vous suggérant ainsi le meilleur "Tag" pour votre torrent.

### 4. File d'attente des Tâches
Lorsque vous lancez une génération (individuelle ou groupée), une tâche est créée dans la file d'attente.
- Les **Workers** traitent les tâches en parallèle.
- Utilisation de `py3createtorrent` pour une compatibilité maximale.
- Application des filtres d'exclusion pour ne garder que l'essentiel.

### 5. Monitoring en Temps Réel
Suivez la progression globale et détaillée via l'onglet **Tâches**. Consultez les **Logs** système en direct pour vérifier le bon déroulement de chaque création.

---

## 🚀 Installation Rapide

### Via Docker (Recommandé)
```bash
docker run -d \
  --name torrent-factory \
  -p 5000:5000 \
  -v /votre/chemin/config:/config \
  -v /votre/chemin/series:/data/series \
  -v /votre/chemin/movies:/data/movies \
  -v /votre/chemin/torrents:/data/torrents \
  ghcr.io/${GITHUB_REPOSITORY_OWNER,,}/torrent-factory:latest
```

### Via le script d'installation
```bash
git clone https://github.com/${GITHUB_REPOSITORY}.git
cd torrent-factory
chmod +x install.sh
./install.sh
```

---

## ⚙️ Configuration

| Paramètre | Description |
| :--- | :--- |
| **Tracker URL** | L'annonce de votre tracker (ex: `udp://.../announce`). |
| **Mode Privé** | Active le flag `-P` pour les trackers privés. |
| **Exclusions** | Liste des fichiers à ignorer (ex: `.plexmatch, theme.mp3`). |
| **Workers** | Nombre de créations simultanées autorisées. |
| **Timeout** | Temps maximum alloué à la création d'un torrent volumineux. |

---

## 💻 Stack Technique

- **Frontend** : React 19, TypeScript, Tailwind CSS, Shadcn/UI, Lucide Icons.
- **Backend** : Python 3, Flask (Serveur API), Threading (Workers).
- **Outils** : FFprobe (Analyse), py3createtorrent (Moteur), Docker.

---

<div align="center">
Développé avec ❤️ pour la communauté.
</div>