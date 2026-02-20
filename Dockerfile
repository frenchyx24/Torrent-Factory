FROM python:3.11-slim

# Dépendances système pour le hachage et Flask
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste de l'application
COPY . .

# On s'assure que le dossier dist existe pour Flask
RUN mkdir -p dist

EXPOSE 5000

# Commande de démarrage
CMD ["python", "main.py"]