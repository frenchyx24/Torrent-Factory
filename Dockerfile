# Étape 1 : Build du Frontend (React)
FROM node:20 AS frontend-builder
WORKDIR /app
COPY package*.json ./
# Utilisation de legacy-peer-deps pour éviter les conflits de versions React 19/Shadcn
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# Étape 2 : Runtime Backend (Python)
FROM python:3.11-slim
WORKDIR /app

# Installation des dépendances système pour FFmpeg et le réseau
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des packages Python requis par votre script V38
RUN pip install --no-cache-dir flask py3createtorrent static-ffmpeg

# Copie de la logique backend
COPY main.py .

# Copie du build frontend depuis l'étape 1
COPY --from=frontend-builder /app/dist ./dist

# Variables d'environnement pour votre script
ENV TF_CONFIG_DIR=/config
EXPOSE 5000

# Lancement du serveur
CMD ["python", "main.py"]