import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.host = os.environ.get('DB_HOST', 'localhost')
        self.user = os.environ.get('DB_USER', 'root')
        self.password = os.environ.get('DB_PASSWORD', '')
        self.database = os.environ.get('DB_NAME', 'recette_cuisine')
        self.connection = None

    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            if self.connection.is_connected():
                logger.info("Connexion à MySQL réussie")
                return True
        except Error as e:
            logger.error(f"Erreur de connexion à MySQL: {e}")
            return False

    def disconnect(self):
        """Ferme la connexion à la base de données"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Connexion MySQL fermée")

    def execute_script(self, script_path):
        """Exécute un script SQL depuis un fichier"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            with open(script_path, 'r', encoding='utf-8') as file:
                script = file.read()

            cursor = self.connection.cursor()
            
            # Diviser le script en commandes individuelles
            commands = script.split(';')
            
            for command in commands:
                command = command.strip()
                if command:
                    try:
                        cursor.execute(command)
                        self.connection.commit()
                    except Error as e:
                        if "already exists" not in str(e).lower():
                            logger.warning(f"Erreur lors de l'exécution de la commande: {e}")

            cursor.close()
            logger.info(f"Script {script_path} exécuté avec succès")
            return True

        except Error as e:
            logger.error(f"Erreur lors de l'exécution du script: {e}")
            return False
        except FileNotFoundError:
            logger.error(f"Fichier script non trouvé: {script_path}")
            return False

    def backup_database(self, backup_path=None):
        """Crée une sauvegarde de la base de données"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_recette_cuisine_{timestamp}.sql"

        try:
            import subprocess
            
            command = [
                'mysqldump',
                f'--host={self.host}',
                f'--user={self.user}',
                f'--password={self.password}',
                '--single-transaction',
                '--routines',
                '--triggers',
                self.database
            ]
            
            with open(backup_path, 'w') as backup_file:
                subprocess.run(command, stdout=backup_file, check=True)
            
            logger.info(f"Sauvegarde créée: {backup_path}")
            return backup_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la sauvegarde: {e}")
            return None

    def get_database_stats(self):
        """Retourne les statistiques de la base de données"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor(dictionary=True)
            
            stats = {}
            
            # Taille de la base de données
            cursor.execute("""
                SELECT 
                    table_schema as 'Database',
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as 'Size_MB'
                FROM information_schema.tables 
                WHERE table_schema = %s
                GROUP BY table_schema
            """, (self.database,))
            
            result = cursor.fetchone()
            stats['database_size_mb'] = result['Size_MB'] if result else 0
            
            # Nombre d'enregistrements par table
            tables = ['utilisateur', 'recette', 'commentaire', 'note', 'favoris', 
                     'historique_consultation', 'historique_recherche']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                stats[f'{table}_count'] = result['count']
            
            cursor.close()
            return stats

        except Error as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return None

def setup_database():
    """Configure et initialise la base de données"""
    db_manager = DatabaseManager()
    
    if db_manager.connect():
        # Exécuter le script de configuration
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'database-setup.sql')
        if db_manager.execute_script(script_path):
            logger.info("Base de données configurée avec succès")
        else:
            logger.error("Erreur lors de la configuration de la base de données")
        
        db_manager.disconnect()
    else:
        logger.error("Impossible de se connecter à la base de données")

if __name__ == "__main__":
    setup_database()
