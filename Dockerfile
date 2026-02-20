# Étape 1 : Build du Frontend (React)
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Étape 2 : Runtime Backend (Python)
FROM python:3.11-slim
WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask py3createtorrent static-ffmpeg

# Copie du code backend
COPY main.py .

# Copie du build frontend depuis l'étape 1 vers le dossier 'dist'
COPY --from=frontend-builder /app/dist ./dist

# Ports et Volumes
EXPOSE 5000
VOLUME ["/config", "/data"]

CMD ["python", "main.py"]