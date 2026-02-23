from sqlalchemy.orm import Session
from Backend.models import Clients as Client, BonsDeLivraison
from Backend.schemas import ClientCreate, ClientUpdate
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

# Ajouter un client
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

def create_client(db: Session, client_data: ClientCreate):
    try:
        new_client = Client(**client_data.model_dump())
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        return new_client
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        # On analyse le message d'erreur renvoyé par PostgreSQL
        if "code_client" in error_msg:
            detail = "Ce code client est déjà utilisé."
        elif "email" in error_msg:
            detail = "Cette adresse email est déjà utilisée."
        elif "matricule_fiscal" in error_msg:
            detail = "Ce matricule fiscal est déjà utilisé."
        else:
            detail = "Une contrainte d'unicité a été violée."
            
        raise HTTPException(status_code=400, detail=detail)

# Lire tous les clients
def get_all_clients_v2(db: Session):
    return db.query(Client).all() # On enlève .offset() et .limit()

def get_all_clients(db: Session):
    """
    Récupère tous les clients de la base de données.
    """
    logger.info("Récupération de tous les clients...")
    try:
        clients = db.query(Client).order_by(Client.nom_client).all()
        # Assurez-vous que les objets sont convertis en un format sérialisable
        return [{"id_client": c.id_client, "nom_client": c.nom_client, "matricule_fiscal": c.matricule_fiscal} for c in clients]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clients : {e}")
        return []
    
# Lire un client par ID
def get_client(db: Session, client_id: int):
    return db.query(Client).filter(Client.id_client == client_id).first()

# Mettre à jour un client
def update_client(db: Session, client_id: int, client_data: ClientUpdate):
    db_client = db.query(Client).filter(Client.id_client == client_id).first()
    if not db_client:
        return None  # Client non trouvé

    for key, value in client_data.model_dump(exclude_unset=True).items():
        setattr(db_client, key, value)

    try:
        db.commit()
        db.refresh(db_client)
        return db_client
    except IntegrityError as e:
        db.rollback()
        if "contrainte unique" in str(e).lower():
            raise ValueError("Un client avec cet email ou ce code existe déjà.")
        else:
            raise ValueError("Erreur lors de la mise à jour du client.")

# Supprimer un client
def delete_client(db: Session, client_id: int):
    db_client = db.query(Client).filter(Client.id_client == client_id).first()
    
    if not db_client:
        return None

    # VÉRIFICATION : Le client a-t-il des ventes (BL) associées ?
    # On suppose que votre modèle Client a une relation ou qu'on interroge la table BL
    vente_existante = db.query(BonsDeLivraison).filter(BonsDeLivraison.id_client == client_id).first()
    
    if vente_existante:
        # On lève une exception spécifique que le router pourra capturer
        raise ValueError("Impossible de supprimer : ce client possède un historique de ventes (BL).")

    db.delete(db_client)
    db.commit()
    return db_client


def search_clients_by_name(db: Session, query: str):
    """Recherche les clients dont le nom contient la chaîne query."""
    return db.query(Client).filter(Client.nom_client.ilike(f"%{query}%")).all()