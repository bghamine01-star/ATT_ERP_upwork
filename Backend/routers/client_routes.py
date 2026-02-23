from fastapi import FastAPI, Depends, HTTPException, status, Response, APIRouter
from sqlalchemy.orm import Session
from Backend.database import get_db
from sqlalchemy.sql import text 
from Backend.models import Base  
from Backend.database import engine
from Backend.schemas import ClientCreate, ClientUpdate, ClientResponse
from Backend.services import client_service
import Backend.schemas as schemas
from Backend.routers import user_routes
from typing import List
import logging
"""                                        CLIENTS                                        """
logger = logging.getLogger(__name__)
router = APIRouter(tags=["clients"])


# Ajouter un client
@router.post("/clients/", response_model=schemas.ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(client: schemas.ClientCreate, response: Response, db: Session = Depends(get_db)):
    try:
        db_client = client_service.create_client(db, client)
        response.headers["Location"] = f"/clients/{db_client.id_client}"
        return db_client
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/clients/search", response_model=List[schemas.ClientResponse])
def search_clients(q: str, db: Session = Depends(get_db)):
    """Route pour l'autocomplétion des clients."""
    if len(q) < 3: # On commence à chercher à partir de 3 ou 4 lettres
        return []
    return client_service.search_clients_by_name(db, q)

# Lire tous les clients
@router.get("/clients/", response_model=list[schemas.ClientResponse])
def get_clients(db: Session = Depends(get_db)): # On enlève skip et limit
    return client_service.get_all_clients_v2(db)

# Lire un client par ID
@router.get("/clients/{client_id}", response_model=schemas.ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = client_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return client


# Mettre à jour un client
@router.put("/clients/{client_id}", response_model=schemas.ClientResponse, dependencies=[Depends(user_routes.gerant_only)])
def update_client(client_id: int, client_data: schemas.ClientUpdate, db: Session = Depends(get_db)):
    try:
        client = client_service.update_client(db, client_id, client_data)
        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        return client
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    try:
        client = client_service.delete_client(db, client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        
        return {"message": "Client supprimé avec succès"}
        
    except ValueError as e:
        # Renvoie l'erreur métier à l'utilisateur (ex: "Impossible de supprimer...")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue")

@router.get(
    "/all", 
    response_model=List[schemas.ClientResponse],
    status_code=status.HTTP_200_OK
)
def get_all_clients(db: Session = Depends(get_db)):
    """
    Récupère la liste de tous les clients.
    """
    logger.info("Tentative de récupération de la liste complète des clients.")
    
    clients = client_service.get_all_clients(db)
    
    # Vérifier si la liste de clients est vide
    if not clients:
        logger.warning("Aucun client trouvé dans la base de données.")
        return []
        
    logger.info(f"{len(clients)} clients trouvés, renvoi de la liste.")
    return clients

