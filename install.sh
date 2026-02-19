#!/bin/bash

echo "⚡ Torrent Factory - Installation"
echo "--------------------------------"

# Vérification de Docker
if ! [ -x "$(command -v docker)" ]; then
  echo "❌ Erreur: Docker n'est pas installé." >&2
  exit 1
fi

# Création des dossiers
mkdir -p config data/series data/movies data/torrents

# Téléchargement du docker-compose.yml si nécessaire
if [ ! -f "docker-compose.yml" ]; then
    curl -O https://raw.githubusercontent.com/${GITHUB_REPOSITORY:-frenchyx24/Torrent-Factory}/main/docker-compose.yml
fi

echo "🚀 Lancement de l'application..."
docker compose up -d

echo "✅ Terminé ! Accédez à l'interface sur http://localhost:5000"