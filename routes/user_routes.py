from flask import Blueprint, request, jsonify
import logging
from models import Utilisateur, Favoris, Recette, Collection
from utils.decorators import token_required
from app import db

logger = logging.getLogger(__name__)

user_bp = Blueprint('users', __name__)

@user_bp.route('/<int:user_id>/favorites', methods=['GET'])
@token_required
def get_user_favorites(current_user, user_id):
    """Récupérer les favoris d'un utilisateur"""
    if current_user.ID_USER != user_id:
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    try:
        favorites = db.session.query(Favoris, Recette).join(
            Recette, Favoris.ID_RECETTE == Recette.ID_RECETTE
        ).filter(Favoris.ID_USER == user_id).all()
        
        return jsonify([{
            'ID_RECETTE': recette.ID_RECETTE,
            'TITRE': recette.TITRE,
            'DESCRIPTION': recette.DESCRIPTION,
            'IMAGE': recette.IMAGE,
            'DATE_AJOUT': favorite.DATE_AJOUT.isoformat()
        } for favorite, recette in favorites])
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des favoris: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des favoris'}), 500

@user_bp.route('/<int:user_id>/collections', methods=['GET'])
@token_required
def get_user_collections(current_user, user_id):
    """Récupérer les collections d'un utilisateur"""
    if current_user.ID_USER != user_id:
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    try:
        from models import CollectionRecette
        
        collections = Collection.query.filter_by(ID_USER=user_id).all()
        
        collections_data = []
        for collection in collections:
            # Compter le nombre de recettes dans la collection
            nb_recettes = CollectionRecette.query.filter_by(ID_COLLECTION=collection.ID_COLLECTION).count()
            
            collections_data.append({
                'ID_COLLECTION': collection.ID_COLLECTION,
                'NOM_COLLECTION': collection.NOM_COLLECTION,
                'DESCRIPTION': collection.DESCRIPTION,
                'DATE_CREATION': collection.DATE_CREATION.isoformat(),
                'nb_recettes': nb_recettes
            })
        
        return jsonify(collections_data)
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des collections: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement des collections'}), 500

@user_bp.route('/<int:user_id>/collections', methods=['POST'])
@token_required
def create_collection(current_user, user_id):
    """Créer une nouvelle collection"""
    if current_user.ID_USER != user_id:
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    try:
        data = request.get_json()
        
        if not data.get('nom_collection'):
            return jsonify({'message': 'Le nom de la collection est requis'}), 400
        
        collection = Collection(
            ID_USER=user_id,
            NOM_COLLECTION=data['nom_collection'],
            DESCRIPTION=data.get('description', '')
        )
        
        db.session.add(collection)
        db.session.commit()
        
        return jsonify({
            'message': 'Collection créée avec succès',
            'collection': {
                'ID_COLLECTION': collection.ID_COLLECTION,
                'NOM_COLLECTION': collection.NOM_COLLECTION,
                'DESCRIPTION': collection.DESCRIPTION,
                'DATE_CREATION': collection.DATE_CREATION.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création de la collection: {str(e)}")
        return jsonify({'message': 'Erreur lors de la création de la collection'}), 500

@user_bp.route('/<int:user_id>/profile', methods=['GET'])
@token_required
def get_user_profile(current_user, user_id):
    """Récupérer le profil d'un utilisateur"""
    try:
        user = Utilisateur.query.get(user_id)
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Si c'est son propre profil, retourner toutes les infos
        if current_user.ID_USER == user_id:
            return jsonify(user.to_dict())
        
        # Sinon, retourner seulement les infos publiques
        return jsonify({
            'id': user.ID_USER,
            'username': user.USERNAME,
            'bio': user.BIO,
            'avatar': user.AVATAR,
            'date_inscription': user.DATE_INSCRIPTION.isoformat() if user.DATE_INSCRIPTION else None
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement du profil: {str(e)}")
        return jsonify({'message': 'Erreur lors du chargement du profil'}), 500

@user_bp.route('/<int:user_id>/profile', methods=['PUT'])
@token_required
def update_user_profile(current_user, user_id):
    """Mettre à jour le profil d'un utilisateur"""
    if current_user.ID_USER != user_id:
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    try:
        data = request.get_json()
        
        user = Utilisateur.query.get(user_id)
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Mettre à jour les champs autorisés
        if 'username' in data:
            # Vérifier que le nom d'utilisateur n'est pas déjà pris
            existing = Utilisateur.query.filter(
                Utilisateur.USERNAME == data['username'],
                Utilisateur.ID_USER != user_id
            ).first()
            if existing:
                return jsonify({'message': 'Ce nom d\'utilisateur est déjà pris'}), 400
            user.USERNAME = data['username']
        if 'email' in data:
            user.EMAIL = data['email']
        if 'bio' in data:
            user.BIO = data['bio']
        
        if 'regime_alimentaire' in data:
            if isinstance(data['regime_alimentaire'], list):
                user.REGIME_ALIMENTAIRE = ','.join(data['regime_alimentaire'])
            else:
                user.REGIME_ALIMENTAIRE = data['regime_alimentaire']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profil mis à jour avec succès',
            'user': user.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour du profil: {str(e)}")
        return jsonify({'message': 'Erreur lors de la mise à jour du profil'}), 500
