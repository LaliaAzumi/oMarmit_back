from app import app, db, Categorie, Ingredient, Recette, Utilisateur, Note, Commentaire, Favoris, Collection
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import random

bcrypt = Bcrypt()

def seed_database():
    """Insère des données d'exemple dans la base de données"""
    with app.app_context():
        print("🌱 Insertion des données d'exemple...")
        
        # Ajouter des catégories
        categories_data = [
            'Plats principaux',
            'Entrées', 
            'Desserts',
            'Soupes',
            'Salades',
            'Boissons',
            'Petit-déjeuner',
            'Apéritifs',
            'Sauces',
            'Pains et viennoiseries'
        ]
        
        for nom in categories_data:
            if not Categorie.query.filter_by(NOM_CATEGORIE=nom).first():
                category = Categorie(NOM_CATEGORIE=nom)
                db.session.add(category)
        
        # Ajouter des ingrédients
        ingredients_data = [
            'Tomate', 'Oignon', 'Ail', 'Basilic', 'Parmesan', 'Œuf', 'Farine',
            'Beurre', 'Lait', 'Sucre', 'Sel', 'Poivre', 'Huile d\'olive',
            'Pomme de terre', 'Carotte', 'Courgette', 'Poivron', 'Champignon',
            'Poulet', 'Bœuf', 'Porc', 'Saumon', 'Thon', 'Crevettes',
            'Riz', 'Pâtes', 'Pain', 'Fromage', 'Yaourt', 'Crème fraîche'
        ]
        
        for nom in ingredients_data:
            if not Ingredient.query.filter_by(NOM_INGREDIENT=nom).first():
                ingredient = Ingredient(NOM_INGREDIENT=nom)
                db.session.add(ingredient)
        
        # Créer des utilisateurs de test
        users_data = [
            ('TestUser1', 'test1@example.com', 'password123', 'Passionné de cuisine française', 'Végétarien'),
            ('TestUser2', 'test2@example.com', 'password123', 'Amateur de pâtisserie', 'Sans gluten'),
            ('ChefMario', 'mario@example.com', 'password123', 'Chef italien spécialisé dans les pâtes', ''),
            ('BoulangereAnne', 'anne@example.com', 'password123', 'Boulangère artisanale', 'Végétarien'),
            ('CuisinerPaul', 'paul@example.com', 'password123', 'Cuisinier amateur qui aime expérimenter', 'Paleo')
        ]
        
        for username, email, password, bio, regime in users_data:
            if not Utilisateur.query.filter_by(EMAIL=email).first():
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                user = Utilisateur(
                    USERNAME=username,
                    EMAIL=email,
                    MOT_DE_PASSE=hashed_password,
                    BIO=bio,
                    REGIME_ALIMENTAIRE=regime
                )
                db.session.add(user)
        
        db.session.commit()
        
        # Ajouter des recettes d'exemple
        recettes_data = [
            {
                'titre': 'Spaghetti Carbonara Authentique',
                'description': 'La vraie recette italienne de la carbonara, sans crème !',
                'ingredients': '''400g de spaghetti
200g de guanciale (ou pancetta)
4 œufs entiers
100g de pecorino romano râpé
Poivre noir fraîchement moulu
Sel''',
                'instructions': '''1. Faire bouillir une grande casserole d'eau salée
2. Couper le guanciale en petits dés et le faire revenir à feu moyen
3. Battre les œufs avec le pecorino et beaucoup de poivre
4. Cuire les spaghetti al dente
5. Réserver un verre d'eau de cuisson des pâtes
6. Mélanger les pâtes chaudes avec le guanciale
7. Ajouter le mélange œufs-fromage hors du feu en remuant vivement
8. Ajouter l'eau de cuisson si nécessaire pour la crémosité
9. Servir immédiatement avec du poivre et du pecorino''',
                'categorie': 'Plats principaux',
                'temps_prep': 15,
                'temps_cuisson': 15,
                'difficulte': 'Moyen',
                'calories': 520,
                'proteines': 28.5,
                'glucides': 58.2,
                'lipides': 22.3,
                'regime': ''
            },
            {
                'titre': 'Salade César Maison',
                'description': 'Une salade césar fraîche avec sa sauce authentique',
                'ingredients': '''2 cœurs de romaine
100g de parmesan
4 tranches de pain de mie
2 gousses d'ail
6 filets d'anchois
2 jaunes d'œufs
Jus de 2 citrons
150ml d'huile d'olive
Worcestershire sauce
Moutarde de Dijon''',
                'instructions': '''1. Préparer les croûtons à l'ail au four
2. Laver et essorer la salade
3. Préparer la sauce en émulsionnant les jaunes d'œufs
4. Ajouter l'huile d'olive en filet
5. Incorporer les anchois, l'ail, le citron
6. Assaisonner avec Worcestershire et moutarde
7. Mélanger la salade avec la sauce
8. Ajouter les croûtons et le parmesan
9. Servir immédiatement''',
                'categorie': 'Salades',
                'temps_prep': 25,
                'temps_cuisson': 10,
                'difficulte': 'Facile',
                'calories': 380,
                'proteines': 18.2,
                'glucides': 28.1,
                'lipides': 24.5,
                'regime': 'Végétarien'
            },
            {
                'titre': 'Tarte Tatin aux Pommes',
                'description': 'La célèbre tarte renversée aux pommes caramélisées',
                'ingredients': '''250g de pâte brisée
8 pommes Granny Smith
150g de sucre
80g de beurre
1 pincée de sel
Cannelle (optionnel)''',
                'instructions': '''1. Éplucher et couper les pommes en quartiers
2. Faire un caramel avec le sucre dans un moule
3. Ajouter le beurre au caramel
4. Disposer les pommes en rosace
5. Recouvrir de pâte brisée
6. Rentrer les bords à l'intérieur
7. Cuire 25 minutes à 200°C
8. Laisser reposer 5 minutes
9. Démouler en retournant rapidement''',
                'categorie': 'Desserts',
                'temps_prep': 30,
                'temps_cuisson': 25,
                'difficulte': 'Moyen',
                'calories': 320,
                'proteines': 4.2,
                'glucides': 52.8,
                'lipides': 12.1,
                'regime': 'Végétarien'
            },
            {
                'titre': 'Soupe de Potiron au Lait de Coco',
                'description': 'Une soupe onctueuse et parfumée pour l\'automne',
                'ingredients': '''1kg de potiron
400ml de lait de coco
1 oignon
2 gousses d'ail
1 morceau de gingembre frais
1 cube de bouillon de légumes
Huile d'olive
Sel, poivre
Graines de courge pour la garniture''',
                'instructions': '''1. Éplucher et couper le potiron en cubes
2. Faire revenir l'oignon et l'ail
3. Ajouter le potiron et le gingembre
4. Couvrir d'eau et ajouter le bouillon
5. Cuire 20 minutes jusqu'à tendreté
6. Mixer finement
7. Ajouter le lait de coco
8. Rectifier l'assaisonnement
9. Servir avec les graines de courge grillées''',
                'categorie': 'Soupes',
                'temps_prep': 15,
                'temps_cuisson': 25,
                'difficulte': 'Facile',
                'calories': 180,
                'proteines': 4.5,
                'glucides': 15.2,
                'lipides': 12.8,
                'regime': 'Végétalien,Sans gluten'
            },
            {
                'titre': 'Pancakes Moelleux',
                'description': 'Des pancakes américains parfaits pour le petit-déjeuner',
                'ingredients': '''250g de farine
2 œufs
300ml de lait
2 cuillères à soupe de sucre
1 cuillère à café de levure chimique
1 pincée de sel
50g de beurre fondu
Sirop d'érable pour servir''',
                'instructions': '''1. Mélanger les ingrédients secs
2. Battre les œufs avec le lait
3. Incorporer le mélange liquide aux ingrédients secs
4. Ajouter le beurre fondu
5. Laisser reposer 10 minutes
6. Cuire dans une poêle chaude
7. Retourner quand des bulles se forment
8. Servir chaud avec le sirop d'érable''',
                'categorie': 'Petit-déjeuner',
                'temps_prep': 15,
                'temps_cuisson': 20,
                'difficulte': 'Facile',
                'calories': 280,
                'proteines': 8.5,
                'glucides': 42.3,
                'lipides': 9.2,
                'regime': 'Végétarien'
            }
        ]
        
        users = Utilisateur.query.all()
        
        for recette_data in recettes_data:
            categorie = Categorie.query.filter_by(NOM_CATEGORIE=recette_data['categorie']).first()
            user = random.choice(users)
            
            if categorie and not Recette.query.filter_by(TITRE=recette_data['titre']).first():
                recette = Recette(
                    ID_CATEGORIE=categorie.ID_CATEGORIE,
                    ID_USER=user.ID_USER,
                    TITRE=recette_data['titre'],
                    DESCRIPTION=recette_data['description'],
                    INGREDIENTS=recette_data['ingredients'],
                    INSTRUCTIONS=recette_data['instructions'],
                    temps_preparation=recette_data['temps_prep'],
                    temps_cuisson=recette_data['temps_cuisson'],
                    difficulte=recette_data['difficulte'],
                    calories=recette_data['calories'],
                    proteines=recette_data['proteines'],
                    glucides=recette_data['glucides'],
                    lipides=recette_data['lipides'],
                    regime_alimentaire=recette_data['regime']
                )
                db.session.add(recette)
        
        db.session.commit()
        
        # Ajouter des notes et commentaires
        recettes = Recette.query.all()
        
        for recette in recettes:
            # Ajouter des notes aléatoires
            for user in random.sample(users, random.randint(2, 5)):
                if not Note.query.filter_by(ID_RECETTE=recette.ID_RECETTE, ID_USER=user.ID_USER).first():
                    note = Note(
                        ID_RECETTE=recette.ID_RECETTE,
                        ID_USER=user.ID_USER,
                        NOTE=random.randint(3, 5),
                        DATE_NOTE=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    db.session.add(note)
            
            # Ajouter des commentaires
            commentaires_exemples = [
                "Excellente recette ! Très facile à réaliser.",
                "Délicieux, toute la famille a adoré !",
                "Parfait, je recommande vivement.",
                "Très bon, j'ai juste ajouté un peu plus d'épices.",
                "Recette testée et approuvée !",
                "Simple et efficace, merci pour le partage.",
                "Un régal, je referai cette recette."
            ]
            
            for user in random.sample(users, random.randint(1, 3)):
                commentaire = Commentaire(
                    ID_RECETTE=recette.ID_RECETTE,
                    ID_USER=user.ID_USER,
                    CONTENU=random.choice(commentaires_exemples),
                    DATE_COMMENTAIRE=datetime.utcnow() - timedelta(days=random.randint(1, 20))
                )
                db.session.add(commentaire)
            
            # Ajouter aux favoris
            for user in random.sample(users, random.randint(0, 2)):
                if not Favoris.query.filter_by(ID_USER=user.ID_USER, ID_RECETTE=recette.ID_RECETTE).first():
                    favori = Favoris(
                        ID_USER=user.ID_USER,
                        ID_RECETTE=recette.ID_RECETTE,
                        DATE_AJOUT=datetime.utcnow() - timedelta(days=random.randint(1, 15))
                    )
                    db.session.add(favori)
        
        # Créer quelques collections d'exemple
        for user in users[:3]:
            collection = Collection(
                ID_USER=user.ID_USER,
                NOM_COLLECTION=f"Mes recettes favorites - {user.USERNAME}",
                DESCRIPTION="Collection de mes recettes préférées"
            )
            db.session.add(collection)
        
        db.session.commit()
        
        print("✅ Données d'exemple insérées avec succès!")
        
        # Afficher un résumé
        print(f"📊 Résumé:")
        print(f"   👥 Utilisateurs: {Utilisateur.query.count()}")
        print(f"   🍽️  Recettes: {Recette.query.count()}")
        print(f"   📂 Catégories: {Categorie.query.count()}")
        print(f"   🥕 Ingrédients: {Ingredient.query.count()}")
        print(f"   ⭐ Notes: {Note.query.count()}")
        print(f"   💬 Commentaires: {Commentaire.query.count()}")
        print(f"   ❤️  Favoris: {Favoris.query.count()}")
        print(f"   📚 Collections: {Collection.query.count()}")

if __name__ == '__main__':
    seed_database()
