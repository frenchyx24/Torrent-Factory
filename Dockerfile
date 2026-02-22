FROM python:3.11-slim

# Installation de mktorrent (l'outil le plus stable pour créer des torrents)
RUN apt-get update && apt-get install -y \
    mktorrent \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Création de la structure de dossiers
RUN mkdir -p dist config data/series data/movies data/torrents/series data/torrents/movies
RUN chmod -R 777 config data

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]