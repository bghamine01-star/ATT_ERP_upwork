import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

# Récupérer l'URL depuis l'environnement, avec une valeur par défaut pour la sécurité
DATABASE_URL = os.getenv("DATABASE_URL")

# Petit test de sécurité : arrêter l'app si l'URL est manquante
if DATABASE_URL is None:
    raise ValueError("La variable d'environnement DATABASE_URL n'est pas configurée !")

# Création de l'engine et de la session
engine = create_engine(
    DATABASE_URL, 
    pool_recycle=300,  # Recrée la connexion toutes les 5 min
    pool_pre_ping=True # Vérifie si la connexion est vivante avant de l'utiliser
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fonction pour récupérer une session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()