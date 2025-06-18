from app import app, db, Categorie, Ingredient, Recette, Utilisateur
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def seed_database():
    with app.app_context():
        # Créer les tables
        db.create_all()
        
        # Ajouter des catégories
        categories = [
            'Plats principaux',
            'Entrées',
            'Desserts',
            'Soupes',
            'Salades',
            'Boissons',
            'Petit-déjeuner',
            'Apéritifs'
        ]
        
        for cat_name in categories:
            if not Categorie.query.filter_by(NOM_CATEGORIE=cat_name).first():
                category = Categorie(NOM_CATEGORIE=cat_name)
                db.session.add(category)
        
        # Ajouter des ingrédients
        ingredients = [
            'Tomate', 'Oignon', 'Ail', 'Basilic', 'Parmesan', 'Œuf', 'Farine',
            'Beurre', 'Lait', 'Sucre', 'Sel', 'Poivre', 'Huile d\'olive',
            'Pomme de terre', 'Carotte', 'Courgette', 'Poivron', 'Champignon',
            'Poulet', 'Bœuf', 'Porc', 'Saumon', 'Thon', 'Crevettes',
            'Riz', 'Pâtes', 'Pain', 'Fromage', 'Yaourt', 'Crème fraîche'
        ]
        
        for ing_name in ingredients:
            if not Ingredient.query.filter_by(NOM_INGREDIENT=ing_name).first():
                ingredient = Ingredient(NOM_INGREDIENT=ing_name)
                db.session.add(ingredient)
        
        # Créer un utilisateur de test
        if not Utilisateur.query.filter_by(EMAIL='test@example.com').first():
            hashed_password = bcrypt.generate_password_hash('password123').decode('utf-8')
            test_user = Utilisateur(
                USERNAME='TestUser',
                EMAIL='test@example.com',
                MOT_DE_PASSE=hashed_password,
                BIO='Utilisateur de test pour les recettes'
            )
            db.session.add(test_user)
        
        # Ajouter quelques recettes d'exemple
        if not Recette.query.first():
            user = Utilisateur.query.filter_by(EMAIL='test@example.com').first()
            category = Categorie.query.filter_by(NOM_CATEGORIE='Plats principaux').first()
            
            if user and category:
                recettes_exemple = [
                    {
                        'TITRE': 'Spaghetti Carbonara',
                        'DESCRIPTION': 'Un classique italien avec des œufs, du parmesan et des lardons',
                        'INGREDIENTS': '''400g de spaghetti
200g de lardons
4 œufs
100g de parmesan râpé
Poivre noir
Sel''',
                        'INSTRUCTIONS': '''1. Faire cuire les spaghetti dans l'eau bouillante salée
2. Faire revenir les lardons dans une poêle
3. Battre les œufs avec le parmesan
4. Mélanger les pâtes chaudes avec les lardons
5. Ajouter le mélange œufs-parmesan hors du feu
6. Servir immédiatement avec du poivre''',
                        'temps_preparation': 15,
                        'temps_cuisson': 20,
                        'difficulte': 'Facile',
                        'calories': 450,
                        'proteines': 25.5,
                        'glucides': 55.2,
                        'lipides': 18.3
                    },
                    {
                        'TITRE': 'Salade César',
                        'DESCRIPTION': 'Salade fraîche avec croûtons, parmesan et sauce césar',
                        'INGREDIENTS': '''1 salade romaine
100g de parmesan
2 tranches de pain
2 œufs
2 gousses d'ail
Huile d'olive
Citron
Anchois''',
                        'INSTRUCTIONS': '''1. Laver et couper la salade
2. Préparer les croûtons au four
3. Faire la sauce césar
4. Mélanger tous les ingrédients
5. Servir frais''',
                        'temps_preparation': 20,
                        'temps_cuisson': 10,
                        'difficulte': 'Facile',
                        'regime_alimentaire': 'Végétarien',
                        'calories': 320,
                        'proteines': 15.2,
                        'glucides': 25.1,
                        'lipides': 20.5
                    }
                ]
                
                for recette_data in recettes_exemple:
                    recette = Recette(
                        ID_CATEGORIE=category.ID_CATEGORIE,
                        ID_USER=user.ID_USER,
                        **recette_data
                    )
                    db.session.add(recette)
        
        db.session.commit()
        print("Base de données initialisée avec succès!")

if __name__ == '__main__':
    seed_database()
