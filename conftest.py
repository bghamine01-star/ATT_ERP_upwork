import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Backend.database import get_db
from main import app  # Assurez-vous que c'est le bon chemin vers votre instance FastAPI
from Backend.models import Base # Force le chargement de tous les modèles dans Base.metadata
from Backend.models import *
from sqlalchemy import text
import os
from dotenv import load_dotenv
# Charger les variables du .env
load_dotenv()

print("Configuration du conftest.py pour les tests PostgreSQL...")

# Récupérer l'URL depuis l'environnement
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise ValueError("TEST_DATABASE_URL est manquante dans le fichier .env")

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    
    with engine.begin() as conn:
        # On active l'extension pour les index GIN / trgm
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(engine):
    """Crée une session isolée pour chaque fonction de test."""
    connection = engine.connect()
    # On utilise une transaction pour pouvoir faire un rollback total à la fin du test
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback() # Annule tout ce qui a été fait (ajout de clients, etc.)
    connection.close()

@pytest.fixture(autouse=True)
def override_get_db(db_session):
    """
    Remplace automatiquement la dépendance get_db de FastAPI par la session de test.
    Le 'autouse=True' signifie que ce remplacement se fait pour tous les tests.
    """
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass # La fermeture est gérée par la fixture db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    # On nettoie après les tests pour ne pas polluer l'application réelle
    app.dependency_overrides.clear()