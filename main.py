from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import text 
from contextlib import asynccontextmanager
from Backend.database import get_db, engine
from Backend.models import Base
from Backend.services.dashboard_service import populate_historique_ventes

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from Backend.routers import (
    user_routes,
    client_routes,
    articles_routes,
    vente_routes,
    facture_routes,
    dashboard_routes,
    apurement_routes
)

# main.py

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import text 
from contextlib import asynccontextmanager

# --- IMPORTATION DE VOTRE CONFIGURATION DATABASE ---
from Backend.database import get_db, engine, SessionLocal

# --- IMPORTATION DES SERVICES ---
from Backend.services.user_service import create_initial_gerant_if_none
from Backend.services.dashboard_service import populate_historique_ventes

# --- AUTRES IMPORTS (Scheduler, etc.) ---
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# ... vos autres imports de routes ...

# -----------------
# Configuration de l'automatisation avec APScheduler
# -----------------
scheduler = BackgroundScheduler()

# Fonction pour obtenir une session de DB pour le scheduler
def get_db_for_scheduler():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

# Tâche planifiée
def scheduled_data_aggregation():
    print("Déclenchement de l'agrégation des données du tableau de bord...")
    try:
        db_gen = get_db_for_scheduler()
        db = next(db_gen)
        populate_historique_ventes(db)
        print("Agrégation des données terminée avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'exécution de la tâche d'agrégation : {e}")
    finally:
        db.close()

# Fonction de gestion du cycle de vie de l'application
# main.py (suite)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Action au démarrage : Initialisation de la base
    print("🚀 Démarrage de l'application...")
    
    # On crée une session manuelle juste pour l'initialisation
    db = SessionLocal() 
    try:
        # On appelle la fonction de création du gérant
        create_initial_gerant_if_none(db)
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation du gérant : {e}")
    finally:
        db.close()

    # 2. Configuration du scheduler
    scheduler.add_job(
        scheduled_data_aggregation, 
        CronTrigger(hour=0, minute=0),
        id='populate_historique_ventes',
        replace_existing=True
    )
    scheduler.start()
    
    yield  # L'application tourne
    
    # 3. Action à la fermeture
    scheduler.shutdown()

# -----------------
# Initialisation de l'application FastAPI
# -----------------

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from sqlalchemy.orm import Session
from Backend.database import SessionLocal # Votre import de session

import logging

# Configuration des logs pour suivre l'exécution
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(lifespan=lifespan)



# Point de terminaison de test
@app.get("/")
def read_root(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"message": "✅ Connexion réussie à PostgreSQL"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Erreur de connexion : {str(e)}")

# Inclusion des routeurs
app.include_router(user_routes.router)
app.include_router(client_routes.router)
app.include_router(articles_routes.router)
app.include_router(vente_routes.router)
app.include_router(facture_routes.router)
app.include_router(apurement_routes.router)
app.include_router(dashboard_routes.router)
