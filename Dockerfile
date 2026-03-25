# --- Stage 1: Build Frontend ---
FROM node:20-slim AS builder
WORKDIR /app

# On copie uniquement le package.json pour optimiser le cache Docker
COPY package.json ./
RUN npm install

# Copie du reste du code source
COPY . .

# Variables d'environnement pour stabiliser le build Vite/Rollup
ENV CI=true
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build

# --- Stage 2: Final Image ---
FROM python:3.11-slim
WORKDIR /app

# Installation des outils système nécessaires (mktorrent natif)
RUN apt-get update && apt-get install -y \
    mktorrent \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie des fichiers buildés (React) et du code source (Python)
COPY --from=builder /app/dist ./dist
COPY main.py manifest.json ./

# Configuration de l'environnement de production
RUN mkdir -p /config /data/series /data/movies /data/torrents
ENV CONFIG_PATH=/config/config.json
ENV FLASK_APP=main.py

# Torrent Factory écoute sur le port 5000
EXPOSE 5000

# Lancement de l'application (Backend Flask qui sert aussi le Frontend)
CMD ["python", "main.py"]