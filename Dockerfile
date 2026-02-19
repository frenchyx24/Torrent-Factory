FROM python:3.11-slim

# Installation des dépendances système (FFmpeg pour l'analyse audio)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste de l'application
COPY . .

# Exposition du port Flask
EXPOSE 5000

# Commande de lancement
CMD ["python", "main.py"]