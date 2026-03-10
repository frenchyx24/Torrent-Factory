FROM python:3.11-slim

# Installation de mktorrent et outils essentiels
RUN apt-get update && apt-get install -y \
    mktorrent \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie tout le projet
COPY . .

# Préparation des dossiers avec permissions correctes
RUN mkdir -p dist config data/series data/movies data/torrents/series data/torrents/movies \
    && chmod -R 777 /app

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]