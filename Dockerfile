FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système pour py3createtorrent
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du script unique
COPY main.py .

# Dossier de config par défaut pour Docker
ENV TF_CONFIG_DIR=/config
VOLUME /config

EXPOSE 5000

CMD ["python", "main.py"]