# Étape 1 : Construction du Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Étape 2 : Construction du Backend et Image Finale
FROM python:3.11-slim
WORKDIR /app

# Installation de mktorrent et des dépendances système
RUN apt-get update && apt-get install -y \
    mktorrent \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code backend et du frontend construit
COPY . .
COPY --from=frontend-builder /app/dist ./dist

# Création des dossiers de données par défaut
RUN mkdir -p /data/series /data/movies /data/torrents/series /data/torrents/movies /config

EXPOSE 5000

# Lancement de l'application
CMD ["python", "main.py"]