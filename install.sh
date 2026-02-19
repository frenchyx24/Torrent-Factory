#!/bin/bash

echo "⚡ Installation de Torrent Factory..."

# Vérification de Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Erreur: Python3 n'est pas installé."
    exit 1
fi

# Clonage du dépôt si on n'est pas déjà dedans
if [ ! -d ".git" ]; then
    git clone https://github.com/${GITHUB_USER:-votre-nom}/torrent-factory.git
    cd torrent-factory
fi

# Installation des dépendances
echo "📦 Installation des dépendances Python..."
pip install -r requirements.txt

# Message de succès
echo "✅ Installation terminée !"
echo "🚀 Pour lancer Torrent Factory, tapez : python3 main.py"