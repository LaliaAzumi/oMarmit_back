from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import jwt
import logging
from models import Utilisateur
from app import db, bcrypt
from utils.decorators import token_required

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Inscription d'un nouvel utilisateur"""
    try:
        data = request.get_json()
        
        # Validation des données
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Tous les champs obligatoires doivent être remplis'}), 400
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = Utilisateur.query.filter(
            (Utilisateur.EMAIL == data['email']) | 
            (Utilisateur.USERNAME == data['username'])
        ).first()
        
        if existing_user:
            if existing_user.EMAIL == data['email']:
                return jsonify({'message': 'Cet email est déjà utilisé'}), 400
            else:
                return jsonify({'message': 'Ce nom d\'utilisateur est déjà pris'}), 400
        
        # Hasher le mot de passe
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        # Préparer les régimes alimentaires
        regime_str = ''
        if data.get('dietaryRestrictions'):
            regime_str = ','.join(data['dietaryRestrictions'])
        
        # Créer le nouvel utilisateur
        new_user = Utilisateur(
            USERNAME=data['username'],
            EMAIL=data['email'],
            MOT_DE_PASSE=hashed_password,
            BIO=data.get('bio', ''),
            REGIME_ALIMENTAIRE=regime_str
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"Nouvel utilisateur créé: {data['username']} ({data['email']})")
        return jsonify({'message': 'Compte créé avec succès'}), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création du compte: {str(e)}")
        return jsonify({'message': 'Erreur lors de la création du compte'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Connexion d'un utilisateur"""
    try:
        from app import app
        
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email et mot de passe requis'}), 400
        
        user = Utilisateur.query.filter_by(EMAIL=data['email']).first()
        
        if user and bcrypt.check_password_hash(user.MOT_DE_PASSE, data['password']):
            # Mettre à jour la dernière connexion
            user.DERNIERE_CONNEXION = datetime.utcnow()
            db.session.commit()
            
            # Créer le token JWT
            token = jwt.encode({
                'user_id': user.ID_USER,
                'exp': datetime.utcnow() + timedelta(days=7)
            }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
            
            logger.info(f"Connexion réussie pour: {user.USERNAME}")
            
            return jsonify({
                'token': token,
                'user': user.to_dict()
            }), 200
        
        return jsonify({'message': 'Email ou mot de passe incorrect'}), 401
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la connexion: {str(e)}")
        return jsonify({'message': 'Erreur lors de la connexion'}), 500

import logging

logger = logging.getLogger(__name__)

nutrition_bp = Blueprint('nutrition', __name__)

@nutrition_bp.route('/analyze', methods=['POST'])
def analyze_nutrition():
    """Analyser les valeurs nutritionnelles d'une recette (simulation IA)"""
    try:
        data = request.get_json()
        ingredients = data.get('ingredients', '')
        portions = data.get('portions', 4)
        
        # Simulation d'analyse nutritionnelle avec IA
        # Dans un vrai projet, vous utiliseriez une API comme OpenAI ou une base de données nutritionnelle
        mock_analysis = {
            'vitamins': [
                {'name': 'Vitamine C', 'amount': f'{15 * portions / 4:.1f}mg'},
                {'name': 'Vitamine A', 'amount': f'{200 * portions / 4:.0f}μg'},
                {'name': 'Fer', 'amount': f'{2.5 * portions / 4:.1f}mg'},
                {'name': 'Calcium', 'amount': f'{120 * portions / 4:.0f}mg'}
            ],
            'health_score': 8.5,
            'recommendations': [
                'Riche en fibres alimentaires',
                'Source de protéines complètes',
                'Faible en sodium'
            ],
            'allergens': [
                'Peut contenir des traces de gluten',
                'Contient des produits laitiers'
            ],
            'dietary_info': {
                'vegetarian': 'oui' if 'viande' not in ingredients.lower() else 'non',
                'vegan': 'oui' if all(x not in ingredients.lower() for x in ['viande', 'œuf', 'lait', 'fromage']) else 'non',
                'gluten_free': 'non' if 'farine' in ingredients.lower() else 'possible'
            }
        }
        
        return jsonify(mock_analysis)
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse nutritionnelle: {str(e)}")
        return jsonify({'message': 'Erreur lors de l\'analyse nutritionnelle'}), 500

@nutrition_bp.route('/suggestions', methods=['POST'])
def get_nutrition_suggestions():
    """Obtenir des suggestions nutritionnelles basées sur les préférences"""
    try:
        data = request.get_json()
        user_preferences = data.get('preferences', [])
        current_recipe = data.get('recipe_ingredients', '')
        
        # Simulation de suggestions nutritionnelles
        suggestions = {
            'improvements': [
                'Ajouter des légumes verts pour plus de vitamines',
                'Réduire la quantité de sel pour une meilleure santé cardiovasculaire',
                'Incorporer des graines pour plus d\'oméga-3'
            ],
            'substitutions': [
                {'original': 'Beurre', 'substitute': 'Huile d\'olive', 'benefit': 'Moins de graisses saturées'},
                {'original': 'Sucre blanc', 'substitute': 'Miel', 'benefit': 'Index glycémique plus bas'},
                {'original': 'Farine blanche', 'substitute': 'Farine complète', 'benefit': 'Plus de fibres'}
            ],
            'additions': [
                {'ingredient': 'Épinards', 'benefit': 'Riche en fer et vitamines'},
                {'ingredient': 'Graines de chia', 'benefit': 'Source d\'oméga-3 et fibres'},
                {'ingredient': 'Curcuma', 'benefit': 'Propriétés anti-inflammatoires'}
            ]
        }
        
        return jsonify(suggestions)
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération des suggestions: {str(e)}")
        return jsonify({'message': 'Erreur lors de la génération des suggestions'}), 500
        

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Récupérer les informations de l'utilisateur connecté"""
    return jsonify(current_user.to_dict())

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """Déconnexion (côté client principalement)"""
    return jsonify({'message': 'Déconnexion réussie'}), 200
