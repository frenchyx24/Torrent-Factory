# --- Stage 1: Build Frontend ---
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# --- Stage 2: Final Image ---
FROM python:3.11-slim
WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de l'application
COPY main.py .
# On copie le dossier dist généré à l'étape précédente
COPY --from=builder /app/dist ./dist

# Configuration
ENV TF_CONFIG_DIR=/config
VOLUME /config /data/series /data/movies /data/torrents

EXPOSE 5000
CMD ["python", "main.py"]