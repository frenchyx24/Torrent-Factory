# --- Étape 1 : Build du Frontend (React) ---
FROM node:20-slim AS build-frontend
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# --- Étape 2 : Build du Backend (Python) ---
FROM python:3.11-slim
WORKDIR /app

# Installation des dépendances système (FFmpeg pour FFprobe plus tard)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copie des fichiers Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source Python
COPY main.py .

# Copie du dossier 'dist' généré à l'étape 1 vers le dossier 'dist' de l'image finale
COPY --from=build-frontend /app/dist ./dist

# Configuration des volumes et ports
ENV TF_CONFIG_DIR=/config
EXPOSE 5000

CMD ["python", "main.py"]