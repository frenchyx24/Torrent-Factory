FROM python:3.11-slim

# Installation exhaustive des outils de build et dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Mise à jour des outils de base de Python AVANT d'installer les requirements
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Préparation de l'environnement
RUN mkdir -p dist config data/series data/movies data/torrents/series data/torrents/movies
RUN chmod -R 777 config data

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]