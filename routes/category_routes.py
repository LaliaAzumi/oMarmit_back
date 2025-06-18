from flask import Blueprint, jsonify
import logging
from models import Categorie

logger = logging.getLogger(__name__)

category_bp = Blueprint('categories', __name__)

@category_bp.route('', methods=['GET'])
def get_categories():
    """Récupérer toutes les catégories"""
    try:
        categories = Categorie.query.all()
        return jsonify([{
            'ID_CATEGORIE': cat.ID_CATEGORIE,
            'NOM_CATEGORIE': cat.NOM_CATEGORIE
        } for cat in categories])
    except Exception as e:
        logger.error(f"Erreur lors du chargement des catégories: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des catégories'}), 500

@category_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Récupérer une catégorie spécifique"""
    try:
        category = Categorie.query.get(category_id)
        if not category:
            return jsonify({'message': 'Catégorie non trouvée'}), 404
        
        return jsonify({
            'ID_CATEGORIE': category.ID_CATEGORIE,
            'NOM_CATEGORIE': category.NOM_CATEGORIE
        })
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la catégorie: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement de la catégorie'}), 500

@category_bp.route('/<int:category_id>/recipes', methods=['GET'])
def get_category_recipes(category_id):
    """Récupérer les recettes d'une catégorie"""
    try:
        from models import Recette, Utilisateur, Note
        from sqlalchemy import func
        from app import db
        
        # Vérifier que la catégorie existe
        category = Categorie.query.get(category_id)
        if not category:
            return jsonify({'message': 'Catégorie non trouvée'}), 404
        
        # Récupérer les recettes de cette catégorie
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
            Recette.ID_CATEGORIE == category_id
        ).group_by(Recette.ID_RECETTE).all()
        
        recipes_data = []
        for recipe, username, note_moyenne, nombre_notes in recipes:
            regime_list = []
            if recipe.regime_alimentaire:
                regime_list = [r.strip() for r in recipe.regime_alimentaire.split(',') if r.strip()]
            
            recipes_data.append({
                'ID_RECETTE': recipe.ID_RECETTE,
                'TITRE': recipe.TITRE,
                'DESCRIPTION': recipe.DESCRIPTION,
                'IMAGE': recipe.IMAGE,
                'temps_preparation': recipe.temps_preparation,
                'temps_cuisson': recipe.temps_cuisson,
                'difficulte': recipe.difficulte,
                'regime_alimentaire': ','.join(regime_list),
                'calories': recipe.calories,
                'USERNAME': username,
                'note_moyenne': float(note_moyenne) if note_moyenne else 0,
                'nombre_notes': nombre_notes
            })
        
        return jsonify({
            'category': {
                'ID_CATEGORIE': category.ID_CATEGORIE,
                'NOM_CATEGORIE': category.NOM_CATEGORIE
            },
            'recipes': recipes_data,
            'total_recipes': len(recipes_data)
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des recettes de la catégorie: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des recettes'}), 500
