# Étape 1 : Build du frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# On s'assure que le build se lance proprement
RUN npm run build

# Étape 2 : Image finale
FROM python:3.11-slim
WORKDIR /app

# Installation de mktorrent (dépendance système critique)
RUN apt-get update && apt-get install -y mktorrent && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du build frontend
COPY --from=frontend-builder /app/dist ./dist

# Copie du code backend
COPY main.py manifest.json ./

# Création des dossiers nécessaires
RUN mkdir -p /config /data/series /data/movies /data/torrents

EXPOSE 5000

ENV FLASK_APP=main.py
ENV CONFIG_PATH=/config/config.json

CMD ["python", "main.py"]