from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from models import (Utilisateur, Recette, Commentaire, Note, HistoriqueConsultation, 
                   HistoriqueRecherche, Categorie)
from sqlalchemy import func, desc, and_, text
from utils.decorators import admin_required
from app import db

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_admin_stats(current_user):
    """Récupérer les statistiques d'administration"""
    try:
        # Statistiques générales
        total_users = Utilisateur.query.count()
        total_recipes = Recette.query.count()
        total_comments = Commentaire.query.count()
        total_ratings = Note.query.count()
        
        # Utilisateurs actifs (connectés dans les 30 derniers jours)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = Utilisateur.query.filter(
            Utilisateur.DERNIERE_CONNEXION >= thirty_days_ago
        ).count()
        
        # Nouvelles inscriptions (7 derniers jours)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        new_users = Utilisateur.query.filter(
            Utilisateur.DATE_INSCRIPTION >= seven_days_ago
        ).count()
        
        # Consultations totales
        total_consultations = HistoriqueConsultation.query.count()
        
        # Consultations par jour (7 derniers jours)
        consultations_by_day = []
        for i in range(7):
            day = datetime.utcnow() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = HistoriqueConsultation.query.filter(
                and_(
                    HistoriqueConsultation.DATE_CONSULTATION >= day_start,
                    HistoriqueConsultation.DATE_CONSULTATION < day_end
                )
            ).count()
            
            consultations_by_day.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'consultations': count
            })
        
        # Recettes populaires (avec le plus de consultations)
        popular_recipes_query = db.session.query(
            Recette.TITRE,
            func.count(HistoriqueConsultation.ID_HISTORIQUE).label('consultations')
        ).join(
            HistoriqueConsultation, Recette.ID_RECETTE == HistoriqueConsultation.ID_RECETTE
        ).group_by(Recette.ID_RECETTE).order_by(
            desc('consultations')
        ).limit(10).all()
        
        # Recettes les mieux notées
        top_rated_query = db.session.query(
            Recette.TITRE,
            func.avg(Note.NOTE).label('note_moyenne'),
            func.count(Note.ID_NOTE).label('nombre_notes')
        ).join(
            Note, Recette.ID_RECETTE == Note.ID_RECETTE
        ).group_by(Recette.ID_RECETTE).having(
            func.count(Note.ID_NOTE) >= 5
        ).order_by(desc('note_moyenne')).limit(10).all()
        
        # Termes de recherche populaires
        popular_searches = db.session.query(
            HistoriqueRecherche.TERME_RECHERCHE,
            func.count(HistoriqueRecherche.ID_HISTORIQUE).label('count')
        ).group_by(HistoriqueRecherche.TERME_RECHERCHE).order_by(
            desc('count')
        ).limit(10).all()
        
        # Répartition par catégorie
        categories_stats = db.session.query(
            Categorie.NOM_CATEGORIE,
            func.count(Recette.ID_RECETTE).label('count')
        ).join(
            Recette, Categorie.ID_CATEGORIE == Recette.ID_CATEGORIE
        ).group_by(Categorie.ID_CATEGORIE).all()
        
        return jsonify({
            'general_stats': {
                'total_users': total_users,
                'total_recipes': total_recipes,
                'total_comments': total_comments,
                'total_ratings': total_ratings,
                'active_users': active_users,
                'new_users': new_users,
                'total_consultations': total_consultations
            },
            'consultations_by_day': consultations_by_day,
            'popular_recipes': [
                {'title': titre, 'consultations': consultations}
                for titre, consultations in popular_recipes_query
            ],
            'top_rated_recipes': [
                {
                    'title': titre,
                    'average_rating': float(note_moyenne) if note_moyenne else 0,
                    'total_ratings': nombre_notes
                }
                for titre, note_moyenne, nombre_notes in top_rated_query
            ],
            'popular_searches': [
                {'term': terme, 'count': count}
                for terme, count in popular_searches
            ],
            'categories_stats': [
                {'category': nom, 'count': count}
                for nom, count in categories_stats
            ]
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des statistiques: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des statistiques'}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users(current_user):
    """Récupérer tous les utilisateurs (pagination)"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        users = Utilisateur.query.offset((page - 1) * limit).limit(limit).all()
        total_users = Utilisateur.query.count()
        
        users_data = []
        for user in users:
            # Compter les recettes de l'utilisateur
            recipe_count = Recette.query.filter_by(ID_USER=user.ID_USER).count()
            
            users_data.append({
                'ID_USER': user.ID_USER,
                'USERNAME': user.USERNAME,
                'EMAIL': user.EMAIL,
                'DATE_INSCRIPTION': user.DATE_INSCRIPTION.isoformat() if user.DATE_INSCRIPTION else None,
                'DERNIERE_CONNEXION': user.DERNIERE_CONNEXION.isoformat() if user.DERNIERE_CONNEXION else None,
                'IS_ADMIN': user.IS_ADMIN,
                'recipe_count': recipe_count
            })
        
        return jsonify({
            'users': users_data,
            'total_users': total_users,
            'current_page': page,
            'total_pages': (total_users + limit - 1) // limit
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des utilisateurs: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des utilisateurs'}), 500

@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['PUT'])
@admin_required
def toggle_user_admin(current_user, user_id):
    """Basculer le statut administrateur d'un utilisateur"""
    try:
        user = Utilisateur.query.get(user_id)
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        if user.ID_USER == current_user.ID_USER:
            return jsonify({'message': 'Vous ne pouvez pas modifier votre propre statut'}), 400
        
        user.IS_ADMIN = not user.IS_ADMIN
        db.session.commit()
        
        logger.info(f"Statut admin modifié pour {user.USERNAME}: {user.IS_ADMIN}")
        
        return jsonify({
            'message': f'Statut administrateur {"activé" if user.IS_ADMIN else "désactivé"}',
            'is_admin': user.IS_ADMIN
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la modification du statut: {str(e)}")
        return jsonify({'message': 'Erreur lors de la modification du statut'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, user_id):
    """Supprimer un utilisateur (avec toutes ses données)"""
    try:
        user = Utilisateur.query.get(user_id)
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        if user.ID_USER == current_user.ID_USER:
            return jsonify({'message': 'Vous ne pouvez pas supprimer votre propre compte'}), 400
        
        # Supprimer toutes les données liées à l'utilisateur
        # (les contraintes de clé étrangère s'en chargeront automatiquement)
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"Utilisateur supprimé: {user.USERNAME}")
        
        return jsonify({'message': 'Utilisateur supprimé avec succès'})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la suppression de l'utilisateur: {str(e)}")
        return jsonify({'message': 'Erreur lors de la suppression de l\'utilisateur'}), 500

@admin_bp.route('/recipes', methods=['GET'])
@admin_required
def get_all_recipes_admin(current_user):
    """Récupérer toutes les recettes pour l'administration"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        recipes = db.session.query(
            Recette,
            Utilisateur.USERNAME,
            func.count(Note.ID_NOTE).label('nombre_notes'),
            func.count(Commentaire.ID_COMMENTAIRE).label('nombre_commentaires')
        ).join(
            Utilisateur, Recette.ID_USER == Utilisateur.ID_USER
        ).outerjoin(
            Note, Recette.ID_RECETTE == Note.ID_RECETTE
        ).outerjoin(
            Commentaire, Recette.ID_RECETTE == Commentaire.ID_RECETTE
        ).group_by(Recette.ID_RECETTE).offset((page - 1) * limit).limit(limit).all()
        
        total_recipes = Recette.query.count()
        
        recipes_data = []
        for recipe, username, nombre_notes, nombre_commentaires in recipes:
            recipes_data.append({
                'ID_RECETTE': recipe.ID_RECETTE,
                'TITRE': recipe.TITRE,
                'USERNAME': username,
                'DATE_CREATION': recipe.DATE_CREATION.isoformat() if recipe.DATE_CREATION else None,
                'nombre_notes': nombre_notes,
                'nombre_commentaires': nombre_commentaires
            })
        
        return jsonify({
            'recipes': recipes_data,
            'total_recipes': total_recipes,
            'current_page': page,
            'total_pages': (total_recipes + limit - 1) // limit
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des recettes admin: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des recettes'}), 500
