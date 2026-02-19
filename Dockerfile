# Stage 1: Build React Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Python Backend & Final Image
FROM python:3.11-slim
WORKDIR /app

# Installation des dépendances système pour FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du build frontend et du script backend
COPY --from=frontend-builder /app/dist ./dist
COPY main.py .

# Variables d'environnement
ENV TF_CONFIG_DIR=/config
EXPOSE 5000

CMD ["python", "main.py"]