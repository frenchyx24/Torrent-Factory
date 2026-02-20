FROM python:3.11-slim

# Installation des dépendances système nécessaires à la compilation de paquets Python
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# On installe les dépendances en premier pour le cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Création forcée de la structure de dossiers pour éviter les crashs Flask
RUN mkdir -p dist config data/series data/movies data/torrents/series data/torrents/movies

# On s'assure que les dossiers sont accessibles
RUN chmod -R 777 config data

EXPOSE 5000

# Lancement avec buffer non-bloquant pour voir les logs immédiatement
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]