from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Import de vos modèles
from Backend.models import Base 

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Objet de configuration Alembic
config = context.config

# Setup du logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Support de l'autogenerate
target_metadata = Base.metadata

# Récupérer l'environnement (dev/test) depuis la commande alembic
environment = config.get_main_option("ALEMBIC_ENV")

def get_database_url():
    """
    Récupère l'URL dynamiquement sans rien écrire en dur.
    """
    if environment == "test":
        url = os.getenv("TEST_DATABASE_URL")
    else:
        # Par défaut (dev ou prod), on utilise la DATABASE_URL principale
        url = os.getenv("DATABASE_URL")
    
    if not url:
        raise ValueError(f"L'URL pour l'environnement '{environment}' est introuvable dans les variables d'environnement.")
    
    return url

def run_migrations_offline() -> None:
    """Mode offline."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Mode online."""
    # On crée une config de moteur SQL à la volée avec l'URL dynamique
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=get_database_url(),
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()