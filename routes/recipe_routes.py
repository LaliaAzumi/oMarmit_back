from flask import Blueprint, request, jsonify
from datetime import datetime
import jwt
import logging
from models import (Recette, Utilisateur, Note, Commentaire, Favoris, 
                   HistoriqueConsultation, HistoriqueRecherche, Categorie)
from sqlalchemy import func, desc, and_, or_
from utils.decorators import token_required
from app import db

logger = logging.getLogger(__name__)

recipe_bp = Blueprint('recipes', __name__)

@recipe_bp.route('', methods=['GET'])
def get_recipes():
    """Récupérer les recettes avec filtres et pagination"""
    try:
        # Paramètres de requête
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 12))
        search_query = request.args.get('q', '')
        category = request.args.get('category', '')
        ingredients = request.args.get('ingredients', '')
        max_prep_time = request.args.get('maxPrepTime', '')
        difficulty = request.args.get('difficulty', '')
        diet = request.args.get('diet', '')
        min_rating = request.args.get('minRating', '')
        max_calories = request.args.get('maxCalories', '')
        
        # Enregistrer la recherche dans l'historique
        if search_query:
            token = request.headers.get('Authorization')
            if token:
                try:
                    from app import app
                    if token.startswith('Bearer '):
                        token = token[7:]
                    data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                    user_id = data['user_id']
                    
                    historique = HistoriqueRecherche(
                        ID_USER=user_id,
                        TERME_RECHERCHE=search_query
                    )
                    db.session.add(historique)
                    db.session.commit()
                except:
                    pass
        
        # Construction de la requête
        query = db.session.query(
            Recette,
            Utilisateur.USERNAME,
            func.coalesce(func.avg(Note.NOTE), 0).label('note_moyenne'),
            func.count(Note.ID_NOTE).label('nombre_notes')
        ).join(
            Utilisateur, Recette.ID_USER == Utilisateur.ID_USER
        ).outerjoin(
            Note, Recette.ID_RECETTE == Note.ID_RECETTE
        ).group_by(Recette.ID_RECETTE)
        
        # Application des filtres
        if search_query:
            query = query.filter(
                or_(
                    Recette.TITRE.contains(search_query),
                    Recette.DESCRIPTION.contains(search_query),
                    Recette.INGREDIENTS.contains(search_query)
                )
            )
        
        if category:
            query = query.join(Categorie).filter(Categorie.NOM_CATEGORIE == category)
        
        if max_prep_time:
            query = query.filter(Recette.temps_preparation <= int(max_prep_time))
        
        if difficulty and difficulty != 'all':
            query = query.filter(Recette.difficulte == difficulty)
        
        if diet:
            diet_filters = diet.split(',')
            for diet_filter in diet_filters:
                query = query.filter(Recette.regime_alimentaire.contains(diet_filter.strip()))
        
        if max_calories:
            query = query.filter(Recette.calories <= int(max_calories))
        
        if min_rating:
            query = query.having(func.avg(Note.NOTE) >= float(min_rating))
        
        # Pagination
        total_recipes = query.count()
        recipes = query.offset((page - 1) * limit).limit(limit).all()
        
        # Formatage des résultats
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
            'recipes': recipes_data,
            'currentPage': page,
            'totalPages': (total_recipes + limit - 1) // limit,
            'totalRecipes': total_recipes
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des recettes: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des recettes'}), 500

@recipe_bp.route('/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Récupérer une recette spécifique"""
    try:
        # Enregistrer la consultation
        token = request.headers.get('Authorization')
        user_id = None
        if token:
            try:
                from app import app
                if token.startswith('Bearer '):
                    token = token[7:]
                data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                user_id = data['user_id']
                
                consultation = HistoriqueConsultation(
                    ID_USER=user_id,
                    ID_RECETTE=recipe_id
                )
                db.session.add(consultation)
                db.session.commit()
            except:
                pass
        
        # Récupérer la recette
        recipe_data = db.session.query(
            Recette,
            Utilisateur.USERNAME,
            func.coalesce(func.avg(Note.NOTE), 0).label('note_moyenne'),
            func.count(Note.ID_NOTE).label('nombre_notes')
        ).join(
            Utilisateur, Recette.ID_USER == Utilisateur.ID_USER
        ).outerjoin(
            Note, Recette.ID_RECETTE == Note.ID_RECETTE
        ).filter(
            Recette.ID_RECETTE == recipe_id
        ).group_by(Recette.ID_RECETTE).first()
        
        if not recipe_data:
            return jsonify({'message': 'Recette non trouvée'}), 404
        
        recipe, username, note_moyenne, nombre_notes = recipe_data
        
        regime_list = []
        if recipe.regime_alimentaire:
            regime_list = [r.strip() for r in recipe.regime_alimentaire.split(',') if r.strip()]
        
        return jsonify({
            'ID_RECETTE': recipe.ID_RECETTE,
            'TITRE': recipe.TITRE,
            'DESCRIPTION': recipe.DESCRIPTION,
            'INGREDIENTS': recipe.INGREDIENTS,
            'INSTRUCTIONS': recipe.INSTRUCTIONS,
            'IMAGE': recipe.IMAGE,
            'temps_preparation': recipe.temps_preparation,
            'temps_cuisson': recipe.temps_cuisson,
            'difficulte': recipe.difficulte,
            'regime_alimentaire': ','.join(regime_list),
            'calories': recipe.calories,
            'proteines': float(recipe.proteines) if recipe.proteines else 0,
            'glucides': float(recipe.glucides) if recipe.glucides else 0,
            'lipides': float(recipe.lipides) if recipe.lipides else 0,
            'USERNAME': username,
            'note_moyenne': float(note_moyenne) if note_moyenne else 0,
            'nombre_notes': nombre_notes
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la recette {recipe_id}: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement de la recette'}), 500

@recipe_bp.route('/<int:recipe_id>/favorite', methods=['POST'])
@token_required
def add_favorite(current_user, recipe_id):
    """Ajouter une recette aux favoris"""
    try:
        existing_favorite = Favoris.query.filter_by(
            ID_USER=current_user.ID_USER,
            ID_RECETTE=recipe_id
        ).first()
        
        if existing_favorite:
            return jsonify({'message': 'Déjà dans les favoris'}), 400
        
        favorite = Favoris(
            ID_USER=current_user.ID_USER,
            ID_RECETTE=recipe_id
        )
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({'message': 'Ajouté aux favoris'}), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'ajout aux favoris: {str(e)}")
        return jsonify({'message': 'Erreur lors de l\'ajout aux favoris'}), 500

@recipe_bp.route('/<int:recipe_id>/favorite', methods=['DELETE'])
@token_required
def remove_favorite(current_user, recipe_id):
    """Retirer une recette des favoris"""
    try:
        favorite = Favoris.query.filter_by(
            ID_USER=current_user.ID_USER,
            ID_RECETTE=recipe_id
        ).first()
        
        if not favorite:
            return jsonify({'message': 'Pas dans les favoris'}), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({'message': 'Retiré des favoris'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la suppression des favoris: {str(e)}")
        return jsonify({'message': 'Erreur lors de la suppression des favoris'}), 500

@recipe_bp.route('/<int:recipe_id>/rate', methods=['POST'])
@token_required
def rate_recipe(current_user, recipe_id):
    """Noter une recette"""
    try:
        data = request.get_json()
        rating = data.get('rating')
        
        if not rating or not 1 <= rating <= 5:
            return jsonify({'message': 'La note doit être entre 1 et 5'}), 400
        
        existing_rating = Note.query.filter_by(
            ID_USER=current_user.ID_USER,
            ID_RECETTE=recipe_id
        ).first()
        
        if existing_rating:
            existing_rating.NOTE = rating
            existing_rating.DATE_NOTE = datetime.utcnow()
        else:
            new_rating = Note(
                ID_USER=current_user.ID_USER,
                ID_RECETTE=recipe_id,
                NOTE=rating
            )
            db.session.add(new_rating)
        
        db.session.commit()
        return jsonify({'message': 'Note enregistrée'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'enregistrement de la note: {str(e)}")
        return jsonify({'message': 'Erreur lors de l\'enregistrement de la note'}), 500

@recipe_bp.route('/<int:recipe_id>/comment', methods=['POST'])
@token_required
def add_comment(current_user, recipe_id):
    """Ajouter un commentaire à une recette"""
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content or not content.strip():
            return jsonify({'message': 'Le commentaire ne peut pas être vide'}), 400
        
        comment = Commentaire(
            ID_USER=current_user.ID_USER,
            ID_RECETTE=recipe_id,
            CONTENU=content.strip()
        )
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({'message': 'Commentaire ajouté'}), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'ajout du commentaire: {str(e)}")
        return jsonify({'message': 'Erreur lors de l\'ajout du commentaire'}), 500

@recipe_bp.route('/<int:recipe_id>/comments', methods=['GET'])
def get_recipe_comments(recipe_id):
    """Récupérer les commentaires d'une recette"""
    try:
        comments = db.session.query(Commentaire, Utilisateur.USERNAME).join(
            Utilisateur, Commentaire.ID_USER == Utilisateur.ID_USER
        ).filter(Commentaire.ID_RECETTE == recipe_id).order_by(
            desc(Commentaire.DATE_COMMENTAIRE)
        ).all()
        
        return jsonify([{
            'ID_COMMENTAIRE': comment.ID_COMMENTAIRE,
            'CONTENU': comment.CONTENU,
            'DATE_COMMENTAIRE': comment.DATE_COMMENTAIRE.isoformat(),
            'USERNAME': username
        } for comment, username in comments])
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des commentaires: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des commentaires'}), 500

@recipe_bp.route('/<int:recipe_id>/ratings', methods=['GET'])
def get_recipe_ratings(recipe_id):
    """Récupérer les notes d'une recette"""
    try:
        ratings = db.session.query(Note, Utilisateur.USERNAME).join(
            Utilisateur, Note.ID_USER == Utilisateur.ID_USER
        ).filter(Note.ID_RECETTE == recipe_id).order_by(
            desc(Note.DATE_NOTE)
        ).all()
        
        return jsonify([{
            'ID_NOTE': rating.ID_NOTE,
            'NOTE': rating.NOTE,
            'DATE_NOTE': rating.DATE_NOTE.isoformat(),
            'USERNAME': username
        } for rating, username in ratings])
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des notes: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des notes'}), 500
