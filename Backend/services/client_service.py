from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from Backend.models import Clients as Client, BonsDeLivraison
from Backend.schemas import ClientCreate, ClientUpdate


def create_client(db: Session, payload: ClientCreate):
    """
    Transactional Creation Pattern:
    Creates a new client entity with uniqueness validation and rollback safety.
    """
    try:
        entity = Client(**payload.model_dump())
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    except IntegrityError:
        db.rollback()
        # [REDACTED]: Detailed constraint mapping & audit logging
        raise HTTPException(status_code=400, detail="Client uniqueness constraint violated.")


def get_all_clients(db: Session):
    """
    Read Optimization Pattern:
    Returns a serialized list of clients ordered for consistent API output.
    """
    records = db.query(Client).order_by(Client.nom_client).all()
    return [
        {"id": r.id_client, "name": r.nom_client, "tax_id": r.matricule_fiscal}
        for r in records
    ]


def get_client(db: Session, client_id: int):
    """
    Safe Retrieval Pattern:
    Fetches a single entity by identifier with null-safe behavior.
    """
    return db.query(Client).filter(Client.id_client == client_id).first()


def update_client(db: Session, client_id: int, payload: ClientUpdate):
    """
    Partial Update Strategy:
    Applies dynamic field patching while preserving transactional integrity.
    """
    entity = db.query(Client).filter(Client.id_client == client_id).first()
    if not entity:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entity, field, value)

    try:
        db.commit()
        db.refresh(entity)
        return entity

    except IntegrityError:
        db.rollback()
        # [REDACTED]: Conflict resolution & validation rules
        raise HTTPException(status_code=400, detail="Update conflict detected.")


def delete_client(db: Session, client_id: int):
    """
    Safe Deletion Guard:
    Prevents removal of entities linked to transactional records.
    """
    entity = db.query(Client).filter(Client.id_client == client_id).first()
    if not entity:
        return None

    linked_records = db.query(BonsDeLivraison).filter(
        BonsDeLivraison.id_client == client_id
    ).first()

    if linked_records:
        raise HTTPException(
            status_code=400,
            detail="Deletion denied: linked transactional history found."
        )

    db.delete(entity)
    db.commit()
    return entity


def search_clients(db: Session, keyword: str):
    """
    Flexible Search Pattern:
    Implements case-insensitive filtering for large datasets.
    """
    return db.query(Client).filter(Client.nom_client.ilike(f"%{keyword}%")).all()