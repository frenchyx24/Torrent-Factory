FROM python:3.11

# Installation de quelques outils de base au cas où
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Mise à jour des outils de gestion de paquets
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Création de la structure de dossiers
RUN mkdir -p dist config data/series data/movies data/torrents/series data/torrents/movies
RUN chmod -R 777 config data

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]