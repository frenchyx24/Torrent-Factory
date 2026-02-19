# --- Stage 1: Build Frontend ---
FROM node:20 AS builder
WORKDIR /app

# Installation des dépendances avec force pour React 19
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copie du reste et build
COPY . .
# CI=false empêche le build de planter pour de simples warnings
RUN CI=false npm run build

# --- Stage 2: Final Image ---
FROM python:3.11-slim
WORKDIR /app

# Installation de ffmpeg pour la détection des langues
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de l'application et du build React
COPY main.py .
COPY --from=builder /app/dist ./dist

# Configuration des volumes et ports
ENV TF_CONFIG_DIR=/config
VOLUME /config /data/series /data/movies /data/torrents
EXPOSE 5000

CMD ["python", "main.py"]