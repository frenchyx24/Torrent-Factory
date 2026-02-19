# ⚡ Torrent Factory V1

Torrent Factory est un outil puissant et moderne pour automatiser la création de fichiers `.torrent` pour vos films et séries. Il combine un backend Python robuste avec une interface web React élégante.

## 🚀 Fonctionnalités

- **Scan Intelligent** : Détecte automatiquement vos films et séries.
- **Analyse Audio** : Utilise FFprobe pour identifier les langues (MULTI, FRENCH, VOSTFR).
- **Multi-Mode** : Génération par Pack, par Saison ou par Épisode.
- **Interface Moderne** : Dashboard sombre avec monitoring en temps réel.
- **Docker Ready** : Déploiement en une seule commande.

## 🛠 Installation

### Option 1 : Docker (Recommandé)

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/votre-compte/torrent-factory.git
   cd torrent-factory
   ```
2. Lancez avec Docker Compose :
   ```bash
   docker-compose up -d
   ```
3. Accédez à l'interface sur `http://localhost:5000`.

### Option 2 : Installation Manuelle (Python)

1. Installez les dépendances Python :
   ```bash
   pip install -r requirements.txt
   ```
2. Compilez le frontend (nécessite Node.js) :
   ```bash
   npm install
   npm run build
   ```
3. Lancez le serveur :
   ```bash
   python main.py
   ```

## ⚙️ Configuration

La configuration se fait directement via l'interface web dans l'onglet **Réglages**. Vous pouvez y définir :
- Les chemins sources de vos médias.
- Le dossier de destination des torrents.
- L'URL de votre tracker.
- Le nombre de workers simultanés.

## 📦 Structure du Projet

- `/src` : Code source du frontend React.
- `main.py` : Serveur Flask et logique de création de torrents.
- `Dockerfile` : Instructions de build pour l'image Docker.
- `.github/workflows` : Automatisation CI/CD.

---
Made with ❤️ by Torrent Factory Team