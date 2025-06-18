from flask import Blueprint, jsonify, request
import logging
from models import Ingredient
from utils.decorators import admin_required
from app import db

logger = logging.getLogger(__name__)

ingredient_bp = Blueprint('ingredients', __name__)

@ingredient_bp.route('', methods=['GET'])
def get_ingredients():
    """Récupérer tous les ingrédients"""
    try:
        search = request.args.get('search', '')
        
        query = Ingredient.query
        if search:
            query = query.filter(Ingredient.NOM_INGREDIENT.contains(search))
        
        ingredients = query.order_by(Ingredient.NOM_INGREDIENT).all()
        
        return jsonify([{
            'ID_INGREDIENT': ing.ID_INGREDIENT,
            'NOM_INGREDIENT': ing.NOM_INGREDIENT
        } for ing in ingredients])
    except Exception as e:
        logger.error(f"Erreur lors du chargement des ingrédients: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des ingrédients'}), 500

@ingredient_bp.route('/<int:ingredient_id>', methods=['GET'])
def get_ingredient(ingredient_id):
    """Récupérer un ingrédient spécifique"""
    try:
        ingredient = Ingredient.query.get(ingredient_id)
        if not ingredient:
            return jsonify({'message': 'Ingrédient non trouvé'}), 404
        
        return jsonify({
            'ID_INGREDIENT': ingredient.ID_INGREDIENT,
            'NOM_INGREDIENT': ingredient.NOM_INGREDIENT
        })
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'ingrédient: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement de l\'ingrédient'}), 500

@ingredient_bp.route('', methods=['POST'])
@admin_required
def create_ingredient(current_user):
    """Créer un nouvel ingrédient (admin seulement)"""
    try:
        data = request.get_json()
        
        if not data.get('nom_ingredient'):
            return jsonify({'message': 'Le nom de l\'ingrédient est requis'}), 400
        
        # Vérifier si l'ingrédient existe déjà
        existing = Ingredient.query.filter_by(NOM_INGREDIENT=data['nom_ingredient']).first()
        if existing:
            return jsonify({'message': 'Cet ingrédient existe déjà'}), 400
        
        ingredient = Ingredient(NOM_INGREDIENT=data['nom_ingredient'])
        db.session.add(ingredient)
        db.session.commit()
        
        logger.info(f"Nouvel ingrédient créé: {data['nom_ingredient']}")
        
        return jsonify({
            'message': 'Ingrédient créé avec succès',
            'ingredient': {
                'ID_INGREDIENT': ingredient.ID_INGREDIENT,
                'NOM_INGREDIENT': ingredient.NOM_INGREDIENT
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création de l'ingrédient: {str(e)}")
        return jsonify({'message': 'Erreur lors de la création de l\'ingrédient'}), 500

@ingredient_bp.route('/<int:ingredient_id>/recipes', methods=['GET'])
def get_ingredient_recipes(ingredient_id):
    """Récupérer les recettes contenant un ingrédient"""
    try:
        from models import Recette, Utilisateur, Note
        from sqlalchemy import func
        from app import db
        
        # Vérifier que l'ingrédient existe
        ingredient = Ingredient.query.get(ingredient_id)
        if not ingredient:
            return jsonify({'message': 'Ingrédient non trouvé'}), 404
        
        # Rechercher les recettes contenant cet ingrédient dans le texte
        recipes = db.session.query(
            Recette,
            Utilisateur.USERNAME,
            func.coalesce(func.avg(Note.NOTE), 0).label('note_moyenne'),
            func.count(Note.ID_NOTE).label('nombre_notes')
        ).join(
            Utilisateur, Recette.ID_USER == Utilisateur.ID_USER
        ).outerjoin(
            Note, Recette.ID_RECETTE == Note.ID_RECETTE
        ).filter(
            Recette.INGREDIENTS.contains(ingredient.NOM_INGREDIENT)
        ).group_by(Recette.ID_RECETTE).all()
        
        recipes_data = []
        for recipe, username, note_moyenne, nombre_notes in recipes:
            recipes_data.append({
                'ID_RECETTE': recipe.ID_RECETTE,
                'TITRE': recipe.TITRE,
                'DESCRIPTION': recipe.DESCRIPTION,
                'IMAGE': recipe.IMAGE,
                'USERNAME': username,
                'note_moyenne': float(note_moyenne) if note_moyenne else 0,
                'nombre_notes': nombre_notes
            })
        
        return jsonify({
            'ingredient': {
                'ID_INGREDIENT': ingredient.ID_INGREDIENT,
                'NOM_INGREDIENT': ingredient.NOM_INGREDIENT
            },
            'recipes': recipes_data,
            'total_recipes': len(recipes_data)
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des recettes avec l'ingrédient: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des recettes'}), 500
