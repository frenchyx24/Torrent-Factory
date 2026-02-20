# Étape 1 : Construction du frontend React
FROM node:20-slim AS build-frontend
WORKDIR /app

# Installation des outils de build si nécessaire
RUN apt-get update && apt-get install -y python3 make g++ && rm -rf /var/lib/apt/lists/*

COPY package*.json ./
# Utilisation de --legacy-peer-deps pour éviter les conflits React 18/19
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build

# Étape 2 : Backend Python et exécution
FROM python:3.11-slim
WORKDIR /app

# Installation des dépendances système (FFmpeg pour l'analyse audio)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du build frontend et du code backend
COPY --from=build-frontend /app/dist ./dist
COPY main.py .

# Création des dossiers de données
RUN mkdir -p /config /data/series /data/movies /data/torrents/series /data/torrents/movies

EXPOSE 5000
CMD ["python", "main.py"]