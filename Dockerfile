FROM python:3.11-slim

# Installation de mktorrent (l'outil stable pour créer des torrents)
RUN apt-get update \
    && apt-get install -y --no-install-recommends mktorrent ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code et limiter les permissions au besoin
COPY . .

# Création de la structure de dossiers utilisées en runtime
RUN mkdir -p dist config data/series data/movies data/torrents/series data/torrents/movies \
    && chmod -R 755 config data dist || true

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

# Créer un utilisateur non-root pour exécuter l'application
RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app \
    && chown -R app:app /app /config /data || true

USER app

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]