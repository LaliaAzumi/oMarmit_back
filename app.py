from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
from functools import wraps
import jwt
from sqlalchemy import func, desc, and_, or_, text
import json
import logging
from werkzeug.utils import secure_filename

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost/recette_cuisine')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
CORS(app, supports_credentials=True, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# Import des modèles
from models import *

# Import des routes (blueprints)
from routes.auth_routes import auth_bp
from routes.recipe_routes import recipe_bp
from routes.category_routes import category_bp
from routes.ingredient_routes import ingredient_bp
from routes.admin_routes import admin_bp
from routes.user_routes import user_bp
from routes.nutrition_routes import nutrition_bp

# Enregistrement des blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(recipe_bp, url_prefix='/api/recipes')
app.register_blueprint(category_bp, url_prefix='/api/categories')
app.register_blueprint(ingredient_bp, url_prefix='/api/ingredients')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(nutrition_bp, url_prefix='/api/nutrition')



# Gestionnaire d'erreurs globaux
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Ressource non trouvée'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'message': 'Erreur interne du serveur'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'message': 'Requête invalide'}), 400

# Route de santé pour vérifier le statut de l'API
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# Initialisation de la base de données
def init_db():
    """Initialise la base de données avec les tables et données par défaut"""
    try:
        # Créer un utilisateur admin par défaut s'il n'existe pas
        admin = Utilisateur.query.filter_by(EMAIL='admin@omarmit.com').first()
        if not admin:
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = Utilisateur(
                USERNAME='Admin',
                EMAIL='admin@omarmit.com',
                MOT_DE_PASSE=hashed_password,
                IS_ADMIN=True,
                BIO='Administrateur du site Ô\'Marmit'
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Utilisateur admin créé avec succès")
        
        logger.info("Base de données initialisée avec succès")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Démarrage du serveur Flask sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
