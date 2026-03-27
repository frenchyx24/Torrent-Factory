# Étape 1 : Construction du Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Étape 2 : Image Finale
FROM python:3.11-slim
WORKDIR /app

# Installation des outils natifs : mktorrent pour les torrents, mediainfo pour les NFO
RUN apt-get update && apt-get install -y \
    mktorrent \
    mediainfo \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend-builder /app/dist ./dist

RUN mkdir -p /data/series /data/movies /data/torrents/series /data/torrents/movies /config

EXPOSE 5000
CMD ["python", "main.py"]