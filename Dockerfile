# --- Stage 1: Build Frontend ---
FROM node:20-slim AS builder
WORKDIR /app

# Optimisation du cache
COPY package.json ./
RUN npm install

# Copie du code source frontend
COPY . .

# Build de l'application React
ENV CI=true
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build

# --- Stage 2: Final Image ---
FROM python:3.11-slim
WORKDIR /app

# Installation des outils système (mktorrent natif, curl, jq)
RUN apt-get update && apt-get install -y \
    mktorrent \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie des fichiers buildés et du code source
COPY --from=builder /app/dist ./dist
COPY main.py manifest.json ./

# Copie du dossier scripts pour les tests E2E et automation
COPY scripts/ ./scripts/
RUN chmod +x scripts/*.sh || true

# Configuration de l'environnement
RUN mkdir -p /config /data/series /data/movies /data/torrents
ENV CONFIG_PATH=/config/config.json
ENV FLASK_APP=main.py

EXPOSE 5000

# Lancement
CMD ["python", "main.py"]