from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import os
from functools import wraps
import jwt
from sqlalchemy import func, desc, and_, or_
import json

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/recette_cuisine'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'

# Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)

# Modèles de base de données
class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'
    
    ID_USER = db.Column(db.Integer, primary_key=True, autoincrement=True)
    USERNAME = db.Column(db.Text, nullable=False)
    EMAIL = db.Column(db.Text)
    MOT_DE_PASSE = db.Column(db.Text, nullable=False)
    DATE_INSCRIPTION = db.Column(db.DateTime, default=datetime.utcnow)
    DERNIERE_CONNEXION = db.Column(db.DateTime)
    AVATAR = db.Column(db.String(255))
    BIO = db.Column(db.Text)
    REGIME_ALIMENTAIRE = db.Column(db.String(255))
    IS_ADMIN = db.Column(db.Boolean, default=False)

class Categorie(db.Model):
    __tablename__ = 'categorie'
    
    ID_CATEGORIE = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NOM_CATEGORIE = db.Column(db.Text, nullable=False)

class Recette(db.Model):
    __tablename__ = 'recette'
    
    ID_RECETTE = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_CATEGORIE = db.Column(db.Integer, db.ForeignKey('categorie.ID_CATEGORIE'), nullable=False)
    ID_USER = db.Column(db.Integer, db.ForeignKey('utilisateur.ID_USER'), nullable=False)
    TITRE = db.Column(db.Text, nullable=False)
    DESCRIPTION = db.Column(db.Text)
    INGREDIENTS = db.Column(db.Text, nullable=False)
    INSTRUCTIONS = db.Column(db.Text, nullable=False)
    IMAGE = db.Column(db.Text)
    DATE_CREATION = db.Column(db.Date, default=datetime.utcnow)
    temps_preparation = db.Column(db.Integer)
    temps_cuisson = db.Column(db.Integer)
    difficulte = db.Column(db.Enum('Facile', 'Moyen', 'Difficile'), default='Facile')
    calories = db.Column(db.Integer)
    proteines = db.Column(db.Numeric(5, 2))
    glucides = db.Column(db.Numeric(5, 2))
    lipides = db.Column(db.Numeric(5, 2))
    regime_alimentaire = db.Column(db.String(255))
    
    # Relations
    categorie = db.relationship('Categorie', backref='recettes')
    utilisateur = db.relationship('Utilisateur', backref='recettes')

class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    
    ID_INGREDIENT = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NOM_INGREDIENT = db.Column(db.String(100), nullable=False, unique=True)

class RecetteIngredient(db.Model):
    __tablename__ = 'recette_ingredient'
    
    ID_RECETTE = db.Column(db.Integer, db.ForeignKey('recette.ID_RECETTE'), primary_key=True)
    ID_INGREDIENT = db.Column(db.Integer, db.ForeignKey('ingredient.ID_INGREDIENT'), primary_key=True)
    QUANTITE = db.Column(db.Numeric(6, 2))
    UNITE = db.Column(db.String(20))

class Note(db.Model):
    __tablename__ = 'note'
    
    ID_NOTE = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_RECETTE = db.Column(db.Integer, db.ForeignKey('recette.ID_RECETTE'), nullable=False)
    ID_USER = db.Column(db.Integer, db.ForeignKey('utilisateur.ID_USER'), nullable=False)
    NOTE = db.Column(db.Integer, nullable=False)
    DATE_NOTE = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('ID_RECETTE', 'ID_USER'),)

class Commentaire(db.Model):
    __tablename__ = 'commentaire'
    
    ID_COMMENTAIRE = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_RECETTE = db.Column(db.Integer, db.ForeignKey('recette.ID_RECETTE'), nullable=False)
    ID_USER = db.Column(db.Integer, db.ForeignKey('utilisateur.ID_USER'), nullable=False)
    CONTENU = db.Column(db.Text, nullable=False)
    DATE_COMMENTAIRE = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    utilisateur = db.relationship('Utilisateur', backref='commentaires')

class Favoris(db.Model):
    __tablename__ = 'favoris'
    
    ID_USER = db.Column(db.Integer, db.ForeignKey('utilisateur.ID_USER'), primary_key=True)
    ID_RECETTE = db.Column(db.Integer, db.ForeignKey('recette.ID_RECETTE'), primary_key=True)
    DATE_AJOUT = db.Column(db.DateTime, default=datetime.utcnow)

class Collection(db.Model):
    __tablename__ = 'collection'
    
    ID_COLLECTION = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_USER = db.Column(db.Integer, db.ForeignKey('utilisateur.ID_USER'), nullable=False)
    NOM_COLLECTION = db.Column(db.String(100), nullable=False)
    DESCRIPTION = db.Column(db.Text)
    DATE_CREATION = db.Column(db.DateTime, default=datetime.utcnow)

class CollectionRecette(db.Model):
    __tablename__ = 'collection_recette'
    
    ID_COLLECTION = db.Column(db.Integer, db.ForeignKey('collection.ID_COLLECTION'), primary_key=True)
    ID_RECETTE = db.Column(db.Integer, db.ForeignKey('recette.ID_RECETTE'), primary_key=True)
    DATE_AJOUT = db.Column(db.DateTime, default=datetime.utcnow)
    ORDRE = db.Column(db.Integer)

class HistoriqueConsultation(db.Model):
    __tablename__ = 'historique_consultation'
    
    ID_HISTORIQUE = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_USER = db.Column(db.Integer, db.ForeignKey('utilisateur.ID_USER'))
    ID_RECETTE = db.Column(db.Integer, db.ForeignKey('recette.ID_RECETTE'), nullable=False)
    DATE_CONSULTATION = db.Column(db.DateTime, default=datetime.utcnow)

class HistoriqueRecherche(db.Model):
    __tablename__ = 'historique_recherche'
    
    ID_HISTORIQUE = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_USER = db.Column(db.Integer, db.ForeignKey('utilisateur.ID_USER'))
    TERME_RECHERCHE = db.Column(db.String(255), nullable=False)
    DATE_RECHERCHE = db.Column(db.DateTime, default=datetime.utcnow)

# Décorateurs d'authentification
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = Utilisateur.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'Utilisateur non trouvé'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = Utilisateur.query.get(data['user_id'])
            if not current_user or not current_user.IS_ADMIN:
                return jsonify({'message': 'Accès administrateur requis'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# Routes d'authentification
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = Utilisateur.query.filter_by(EMAIL=data['email']).first()
        if existing_user:
            return jsonify({'message': 'Cet email est déjà utilisé'}), 400
        
        # Hasher le mot de passe
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        # Créer le nouvel utilisateur
        new_user = Utilisateur(
            USERNAME=data['username'],
            EMAIL=data['email'],
            MOT_DE_PASSE=hashed_password,
            BIO=data.get('bio', ''),
            REGIME_ALIMENTAIRE=','.join(data.get('dietaryRestrictions', []))
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'Compte créé avec succès'}), 201
    
    except Exception as e:
        return jsonify({'message': 'Erreur lors de la création du compte'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
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
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user.ID_USER,
                    'username': user.USERNAME,
                    'email': user.EMAIL,
                    'is_admin': user.IS_ADMIN
                }
            }), 200
        
        return jsonify({'message': 'Email ou mot de passe incorrect'}), 401
    
    except Exception as e:
        return jsonify({'message': 'Erreur lors de la connexion'}), 500

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({
        'id': current_user.ID_USER,
        'username': current_user.USERNAME,
        'email': current_user.EMAIL,
        'bio': current_user.BIO,
        'is_admin': current_user.IS_ADMIN,
        'regime_alimentaire': current_user.REGIME_ALIMENTAIRE.split(',') if current_user.REGIME_ALIMENTAIRE else []
    })

# Routes pour les catégories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Categorie.query.all()
    return jsonify([{
        'ID_CATEGORIE': cat.ID_CATEGORIE,
        'NOM_CATEGORIE': cat.NOM_CATEGORIE
    } for cat in categories])

# Routes pour les ingrédients
@app.route('/api/ingredients', methods=['GET'])
def get_ingredients():
    ingredients = Ingredient.query.all()
    return jsonify([{
        'ID_INGREDIENT': ing.ID_INGREDIENT,
        'NOM_INGREDIENT': ing.NOM_INGREDIENT
    } for ing in ingredients])

# Routes pour les recettes
@app.route('/api/recipes', methods=['GET'])
def get_recipes():
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
            func.avg(Note.NOTE).label('note_moyenne'),
            func.count(Note.ID_NOTE).label('nombre_notes')
        ).join(
            Utilisateur, Recette.ID_USER == Utilisateur.ID_USER
        ).outerjoin(
            Note, Recette.ID_RECETTE == Note.ID_RECETTE
        ).group_by(Recette.ID_RECETTE)
        
        # Filtres
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
            recipes_data.append({
                'ID_RECETTE': recipe.ID_RECETTE,
                'TITRE': recipe.TITRE,
                'DESCRIPTION': recipe.DESCRIPTION,
                'IMAGE': recipe.IMAGE,
                'temps_preparation': recipe.temps_preparation,
                'temps_cuisson': recipe.temps_cuisson,
                'difficulte': recipe.difficulte,
                'regime_alimentaire': recipe.regime_alimentaire,
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
        return jsonify({'message': 'Erreur lors du chargement des recettes'}), 500

@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    try:
        # Enregistrer la consultation
        token = request.headers.get('Authorization')
        user_id = None
        if token:
            try:
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
        
        # Récupérer la recette avec les informations de l'utilisateur et les notes
        recipe_data = db.session.query(
            Recette,
            Utilisateur.USERNAME,
            func.avg(Note.NOTE).label('note_moyenne'),
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
            'regime_alimentaire': recipe.regime_alimentaire,
            'calories': recipe.calories,
            'proteines': float(recipe.proteines) if recipe.proteines else 0,
            'glucides': float(recipe.glucides) if recipe.glucides else 0,
            'lipides': float(recipe.lipides) if recipe.lipides else 0,
            'USERNAME': username,
            'note_moyenne': float(note_moyenne) if note_moyenne else 0,
            'nombre_notes': nombre_notes
        })
    
    except Exception as e:
        return jsonify({'message': 'Erreur lors du chargement de la recette'}), 500

# Routes pour les favoris
@app.route('/api/recipes/<int:recipe_id>/favorite', methods=['POST'])
@token_required
def add_favorite(current_user, recipe_id):
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
        return jsonify({'message': 'Erreur lors de l\'ajout aux favoris'}), 500

@app.route('/api/recipes/<int:recipe_id>/favorite', methods=['DELETE'])
@token_required
def remove_favorite(current_user, recipe_id):
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
        return jsonify({'message': 'Erreur lors de la suppression des favoris'}), 500

@app.route('/api/users/<int:user_id>/favorites', methods=['GET'])
@token_required
def get_user_favorites(current_user, user_id):
    if current_user.ID_USER != user_id:
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    favorites = db.session.query(Favoris, Recette).join(
        Recette, Favoris.ID_RECETTE == Recette.ID_RECETTE
    ).filter(Favoris.ID_USER == user_id).all()
    
    return jsonify([{
        'ID_RECETTE': recette.ID_RECETTE,
        'TITRE': recette.TITRE,
        'DATE_AJOUT': favorite.DATE_AJOUT.isoformat()
    } for favorite, recette in favorites])

# Routes pour les notes et commentaires
@app.route('/api/recipes/<int:recipe_id>/rate', methods=['POST'])
@token_required
def rate_recipe(current_user, recipe_id):
    try:
        data = request.get_json()
        rating = data['rating']
        
        if not 1 <= rating <= 5:
            return jsonify({'message': 'La note doit être entre 1 et 5'}), 400
        
        # Vérifier si l'utilisateur a déjà noté cette recette
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
        return jsonify({'message': 'Erreur lors de l\'enregistrement de la note'}), 500

@app.route('/api/recipes/<int:recipe_id>/comment', methods=['POST'])
@token_required
def add_comment(current_user, recipe_id):
    try:
        data = request.get_json()
        content = data['content']
        
        if not content.strip():
            return jsonify({'message': 'Le commentaire ne peut pas être vide'}), 400
        
        comment = Commentaire(
            ID_USER=current_user.ID_USER,
            ID_RECETTE=recipe_id,
            CONTENU=content
        )
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({'message': 'Commentaire ajouté'}), 201
    
    except Exception as e:
        return jsonify({'message': 'Erreur lors de l\'ajout du commentaire'}), 500

@app.route('/api/recipes/<int:recipe_id>/comments', methods=['GET'])
def get_recipe_comments(recipe_id):
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

@app.route('/api/recipes/<int:recipe_id>/ratings', methods=['GET'])
def get_recipe_ratings(recipe_id):
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

# Routes d'administration
@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def get_admin_stats(current_user):
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
        
        # Recettes les plus populaires
        popular_recipes = db.session.query(
            Recette.TITRE,
            func.count(HistoriqueConsultation.ID_HISTORIQUE).label('consultations')
        ).join(
            HistoriqueConsultation, Recette.ID_RECETTE == HistoriqueConsultation.ID_RECETTE
        ).group_by(Recette.ID_RECETTE).order_by(
            desc('consultations')
        ).limit(10).all()
        
        # Recettes les mieux notées
        top_rated_recipes = db.session.query(
            Recette.TITRE,
            func.avg(Note.NOTE).label('note_moyenne'),
            func.count(Note.ID_NOTE).label('nombre_notes')
        ).join(
            Note, Recette.ID_RECETTE == Note.ID_RECETTE
        ).group_by(Recette.ID_RECETTE).having(
            func.count(Note.ID_NOTE) >= 5
        ).order_by(
            desc('note_moyenne')
        ).limit(10).all()
        
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
                {'title': title, 'consultations': consultations}
                for title, consultations in popular_recipes
            ],
            'top_rated_recipes': [
                {
                    'title': title,
                    'average_rating': float(note_moyenne),
                    'total_ratings': nombre_notes
                }
                for title, note_moyenne, nombre_notes in top_rated_recipes
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
        return jsonify({'message': 'Erreur lors du chargement des statistiques'}), 500

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_all_users(current_user):
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
        return jsonify({'message': 'Erreur lors du chargement des utilisateurs'}), 500

@app.route('/api/admin/users/<int:user_id>/toggle-admin', methods=['PUT'])
@admin_required
def toggle_user_admin(current_user, user_id):
    try:
        user = Utilisateur.query.get(user_id)
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        user.IS_ADMIN = not user.IS_ADMIN
        db.session.commit()
        
        return jsonify({
            'message': f'Statut administrateur {"activé" if user.IS_ADMIN else "désactivé"}',
            'is_admin': user.IS_ADMIN
        })
    
    except Exception as e:
        return jsonify({'message': 'Erreur lors de la modification du statut'}), 500

# Route pour l'analyse nutritionnelle avec IA (simulation)
@app.route('/api/nutrition/analyze', methods=['POST'])
def analyze_nutrition():
    try:
        data = request.get_json()
        ingredients = data.get('ingredients', '')
        portions = data.get('portions', 4)
        
        # Simulation d'analyse nutritionnelle
        # Dans un vrai projet, vous utiliseriez une API d'IA ou une base de données nutritionnelle
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
            ]
        }
        
        return jsonify(mock_analysis)
    
    except Exception as e:
        return jsonify({'message': 'Erreur lors de l\'analyse nutritionnelle'}), 500

# Initialisation de la base de données
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Créer un utilisateur admin par défaut
    admin = Utilisateur.query.filter_by(EMAIL='admin@omarmit.com').first()
    if not admin:
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = Utilisateur(
            USERNAME='Admin',
            EMAIL='admin@omarmit.com',
            MOT_DE_PASSE=hashed_password,
            IS_ADMIN=True
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
