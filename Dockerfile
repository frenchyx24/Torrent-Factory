# --- Étape 1 : Build du Frontend (React) ---
FROM node:20-slim AS build-frontend
WORKDIR /app

# On copie uniquement les fichiers de dépendances d'abord pour le cache
COPY package*.json ./

# Utilisation de --legacy-peer-deps car React 19 est très strict sur les versions
RUN npm install --legacy-peer-deps

# Copie du reste et build
COPY . .
RUN npm run build

# --- Étape 2 : Build du Backend (Python) ---
FROM python:3.11-slim
WORKDIR /app

# Installation de FFmpeg (utile pour FFprobe plus tard)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du script et du build frontend
COPY main.py .
COPY --from=build-frontend /app/dist ./dist

# Configuration
ENV TF_CONFIG_DIR=/config
EXPOSE 5000

CMD ["python", "main.py"]