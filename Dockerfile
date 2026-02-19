# Étape 1 : Build du Frontend React
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Étape 2 : Backend Python
FROM python:3.11-slim
WORKDIR /app

# Installation des dépendances système (ffmpeg pour l'analyse audio)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copie des fichiers nécessaires
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du backend et du frontend buildé
COPY main.py .
COPY --from=frontend-builder /app/dist ./dist

# Variables d'environnement
ENV TF_CONFIG_DIR=/config
EXPOSE 5000

CMD ["python", "main.py"]