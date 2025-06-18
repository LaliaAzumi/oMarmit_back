#!/bin/bash

echo "🚀 Démarrage du backend Flask pour Ô'Marmit..."

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages colorés
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Créer un environnement virtuel s'il n'existe pas
if [ ! -d "venv" ]; then
    print_status "Création de l'environnement virtuel..."
    python3 -m venv venv
    print_success "Environnement virtuel créé"
fi

# Activer l'environnement virtuel
print_status "Activation de l'environnement virtuel..."
source venv/bin/activate

# Mettre à jour pip
print_status "Mise à jour de pip..."
pip install --upgrade pip

# Installer les dépendances
print_status "Installation des dépendances Python..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dépendances installées"
else
    print_error "Fichier requirements.txt non trouvé"
    exit 1
fi

# Vérifier si MySQL est accessible
print_status "Vérification de la connexion MySQL..."
python3 -c "
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password=''
    )
    print('✅ Connexion MySQL réussie')
    conn.close()
except Exception as e:
    print(f'❌ Erreur de connexion MySQL: {e}')
    print('Veuillez vérifier que MySQL est démarré et que les identifiants sont corrects')
"

# Configurer les variables d'environnement si le fichier .env n'existe pas
if [ ! -f ".env" ]; then
    print_status "Création du fichier .env..."
    cat > .env << EOL
# Configuration de la base de données
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=recette_cuisine

# Configuration Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=jwt-secret-string

# Configuration du serveur
PORT=5000
EOL
    print_success "Fichier .env créé"
fi

# Charger les variables d'environnement
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Initialiser la base de données avec le script SQL fourni
print_status "Initialisation de la base de données avec votre structure..."
mysql -h localhost -u root -ppassword < ../scripts/database-setup.sql 2>/dev/null || {
    print_warning "Erreur lors de l'exécution du script SQL. La base existe peut-être déjà."
}

# Exécuter le script de seed si demandé
if [ "$1" = "--seed" ]; then
    print_status "Insertion des données d'exemple..."
    python3 seed_data.py
fi

# Créer le dossier uploads s'il n'existe pas
if [ ! -d "uploads" ]; then
    mkdir uploads
    print_status "Dossier uploads créé"
fi

# Afficher les informations de démarrage
print_success "Configuration terminée!"
echo ""
echo "📋 Informations de connexion:"
echo "   🌐 URL API: http://localhost:${PORT:-5000}/api"
echo "   👤 Admin: admin@omarmit.com / admin123"
echo "   🧪 Test: test1@example.com / password123"
echo ""

# Démarrer le serveur Flask
print_status "Démarrage du serveur Flask..."
echo "🔥 Serveur démarré sur http://localhost:${PORT:-5000}"
echo "📊 Panneau admin: http://:3000/admin"
echo ""
echo "Pour arrêter le serveur, appuyez sur Ctrl+C"
echo ""

python3 app.py
