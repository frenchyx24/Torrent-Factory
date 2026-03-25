# --- Stage 1: Build Frontend ---
FROM node:20-slim AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
# Forçage des variables pour éviter les échecs de build silencieux
ENV CI=true
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build

# --- Stage 2: Final Image ---
FROM python:3.11-slim
WORKDIR /app

# Installation des outils système nécessaires
RUN apt-get update && apt-get install -y \
    mktorrent \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie des fichiers buildés et du code source
COPY --from=builder /app/dist ./dist
COPY main.py manifest.json ./

# Préparation de l'environnement
RUN mkdir -p /config /data/series /data/movies /data/torrents
ENV CONFIG_PATH=/config/config.json
ENV FLASK_APP=main.py

EXPOSE 5000

# Lancement de l'application
CMD ["python", "main.py"]