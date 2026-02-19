# Étape 1 : Construction du Frontend (React/Vite)
FROM node:20-slim AS frontend-builder
WORKDIR /app-frontend
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Étape 2 : Image finale (Python)
FROM python:3.11-slim
WORKDIR /app

# Installation des dépendances système nécessaires (ex: ffprobe pour l'analyse audio)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers du backend
COPY main.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copie du build du frontend depuis l'étape précédente
COPY --from=frontend-builder /app-frontend/dist ./dist

# Variables d'environnement
ENV FLASK_ENV=production
ENV TF_CONFIG_DIR=/config

# Port exposé
EXPOSE 5000

# Lancement de l'application
CMD ["python", "main.py"]