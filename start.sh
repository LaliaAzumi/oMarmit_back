#!/bin/bash

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base de données avec des données d'exemple
python seed_data.py

# Démarrer le serveur Flask
python run.py
