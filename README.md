<div align="center">

# ⚡ Torrent Factory V1.3.1
### *L'outil ultime d'automatisation pour la création de torrents*

[![Version](https://img.shields.io/badge/version-1.3.1-indigo?style=for-the-badge)](#)
[![Docker](https://img.shields.io/badge/Status-Stable-emerald?style=for-the-badge)](#)

**Torrent Factory** est une solution complète conçue pour automatiser la création de fichiers `.torrent` à grande échelle. Que vous gériez des bibliothèques de films ou des séries entières, cet outil transforme une tâche manuelle fastidieuse en un processus fluide, rapide et monitoré.

</div>

---

## 📖 Sommaire
1. [Comment ça marche ?](#-comment-ça-marche-)
2. [Fonctionnalités Clés](#-fonctionnalités-clés)
3. [Architecture Technique](#-architecture-technique)
4. [Guide d'Utilisation](#-guide-dutilisation)
5. [Installation](#-installation)
6. [Configuration Avancée](#-configuration-avancée)

---

## 🛠 Comment ça marche ?

Torrent Factory repose sur un modèle **Client-Serveur** optimisé pour la performance :

1.  **Le Backend (Python/Flask)** : Il agit comme le cerveau. Il scanne vos répertoires de stockage (Movies/Series), gère une file d'attente de tâches et communique avec l'outil système `mktorrent`.
2.  **Le Moteur Titanium** : C'est un processeur de tâches asynchrone. Contrairement à d'autres outils qui bloquent l'interface pendant la création d'un torrent (ce qui peut prendre du temps pour des fichiers de plusieurs Go), Titanium travaille en arrière-plan. Vous pouvez lancer 50 créations, fermer votre navigateur, et revenir plus tard pour voir le résultat.
3.  **Le Frontend (React)** : Une interface moderne et intuitive qui vous permet de piloter le serveur, de surveiller la progression en temps réel et de gérer vos fichiers créés.

---

## ✨ Fonctionnalités Clés

- **Scan Automatique** : Détection instantanée de vos nouveaux contenus dans les dossiers sources.
- **Moteur Asynchrone** : File d'attente intelligente qui traite les tâches une par une sans jamais faire planter le serveur.
- **Gestion des Séries** : Modes de génération flexibles (Pack complet, par saison ou par épisode).
- **Auto-Tagging** : Détection intelligente des tags (FRENCH, MULTI, VOSTFR) basés sur les noms de fichiers.
- **Monitoring en Temps Réel** : Barre de progression détaillée pour chaque tâche et logs système consultables.
- **Explorateur de Fichiers Intégré** : Interface visuelle pour choisir vos répertoires directement sur le serveur.
- **Gestion Multi-Langue** : Support complet du Français, Anglais et Allemand.

---

## 🏗 Architecture Technique

- **Frontend** : React 19, TypeScript, Tailwind CSS pour le style, et Radix UI / Shadcn pour les composants.
- **Backend** : Flask (Python) avec un système de threading pour la gestion asynchrone.
- **Moteur de Création** : `mktorrent` (natif), reconnu pour sa rapidité et sa faible consommation de ressources.
- **Dockerisé** : Prêt à être déployé sur n'importe quel NAS (Synology, Unraid) ou serveur Linux.

---

## 🚀 Guide d'Utilisation

### 1. Configuration des Chemins
Rendez-vous dans l'onglet **Réglages**. Vous devez définir 4 chemins essentiels :
- **Series Root** : Où se trouvent vos dossiers de séries originaux.
- **Movies Root** : Où se trouvent vos dossiers de films originaux.
- **Series Out** : Où seront déposés les fichiers `.torrent` des séries.
- **Movies Out** : Où seront déposés les fichiers `.torrent` des films.

### 2. Lancement d'une Tâche
- Allez sur la page **Séries** ou **Films**.
- Sélectionnez les éléments que vous souhaitez transformer en torrent.
- Cliquez sur **"Tout Générer"**. Les tâches sont immédiatement envoyées au moteur Titanium.

### 3. Suivi et Téléchargement
- Consultez l'onglet **Tâches** pour voir la progression.
- Une fois terminé, allez dans l'onglet **Torrents** pour voir vos fichiers `.torrent` prêts à l'emploi. Vous pouvez les télécharger directement ou les supprimer.

---

## 📦 Installation

La méthode recommandée est d'utiliser **Docker** :

```bash
docker run -d \
  --name torrent-factory \
  -p 5000:5000 \
  -v /votre/chemin/config:/config \
  -v /votre/chemin/series:/data/series \
  -v /votre/chemin/movies:/data/movies \
  -v /votre/chemin/torrents:/data/torrents \
  votre-image-torrent-factory:latest
```

---

## ⚙️ Configuration Avancée

- **Tracker URL** : L'adresse de votre tracker privé (ex: `https://tracker.mon-site.com/announce`).
- **Taille de Pièce** : La puissance de 2 utilisée pour les pièces du torrent. Par défaut `21` (2 Mo), ce qui est le standard pour la plupart des trackers.
- **Mode Privé** : Si activé, le flag "private" sera ajouté au torrent pour empêcher l'échange de pairs (PEX) en dehors du tracker.