# Étape 1 : Construction du Frontend React
FROM node:20-slim AS build-frontend
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Étape 2 : Image finale avec Python
FROM python:3.11-slim
WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .
# Copie du build React vers le dossier dist
COPY --from=build-frontend /app/dist ./dist

# Variables d'environnement pour Torrent Factory
ENV TF_CONFIG_DIR=/config
ENV FLASK_ENV=production

EXPOSE 5000

# Lancement du script
CMD ["python", "main.py"]