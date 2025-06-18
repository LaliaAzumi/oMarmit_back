from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Import de l'instance db depuis app.py
from app import db

# Modèles de base de données
class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'
    
    ID_USER = db.Column(db.Integer, primary_key=True, autoincrement=True)
    USERNAME = db.Column(db.Text, nullable=False)
    EMAIL = db.Column(db.Text)
    MOT_DE_PASSE = db.Column(db.Text, nullable=False)
    DATE_INSCRIPTION = db.Column(db.DateTime, default=datetime.utcnow)
    DERNIERE_CONNEXION = db.Column(db.DateTime)
    AVATAR = db.Column(db.String(255), comment='Chemin vers l\'image de profil')
    BIO = db.Column(db.Text, comment='Description de l\'utilisateur')
    REGIME_ALIMENTAIRE = db.Column(db.String(255), comment='Régime alimentaire principal')
    IS_ADMIN = db.Column(db.Boolean, default=False)

    def to_dict(self):
        regime_list = []
        if self.REGIME_ALIMENTAIRE:
            regime_list = [r.strip() for r in self.REGIME_ALIMENTAIRE.split(',') if r.strip()]
        
        return {
            'id': self.ID_USER,
            'username': self.USERNAME,
            'email': self.EMAIL,
            'bio': self.BIO,
            'is_admin': self.IS_ADMIN,
            'regime_alimentaire': regime_list,
            'date_inscription': self.DATE_INSCRIPTION.isoformat() if self.DATE_INSCRIPTION else None,
            'derniere_connexion': self.DERNIERE_CONNEXION.isoformat() if self.DERNIERE_CONNEXION else None,
            'avatar': self.AVATAR
        }

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
    temps_preparation = db.Column(db.Integer, comment='Temps de préparation en minutes')
    temps_cuisson = db.Column(db.Integer, comment='Temps de cuisson en minutes')
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
    QUANTITE = db.Column(db.Numeric(6, 2), comment='Quantité nécessaire')
    UNITE = db.Column(db.String(20), comment='Unité de mesure (g, ml, cuillère à soupe, etc.)')

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
    ORDRE = db.Column(db.Integer, comment='Ordre dans la collection')

class PreferenceUtilisateur(db.Model):
    __tablename__ = 'preference_utilisateur'
    
    ID_USER = db.Column(db.Integer, db.ForeignKey('utilisateur.ID_USER'), primary_key=True)
    PREFERENCE = db.Column(db.String(50), primary_key=True, comment='Type de préférence')
    VALEUR = db.Column(db.String(100), primary_key=True, comment='Valeur de la préférence')
    SCORE = db.Column(db.Integer, default=1, comment='Importance de la préférence')

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
