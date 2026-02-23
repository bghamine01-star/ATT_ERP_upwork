import bcrypt
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from Backend.schemas import *
from Backend.models import Utilisateurs, RoleEnum
from Backend.config import *
from fastapi import HTTPException

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_user(db: Session, user: UtilisateurCreate):
    hashed_password = hash_password(user.mot_de_passe)
    db_user = Utilisateurs(
        nom=user.nom,
        role=user.role,
        mot_de_passe=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_nom(db: Session, nom: str):
    return db.query(Utilisateurs).filter(Utilisateurs.nom == nom).first()

def authenticate_user(db: Session, nom: str, mot_de_passe: str):
    db_user = get_user_by_nom(db, nom=nom)
    if not db_user or not verify_password(mot_de_passe, db_user.mot_de_passe):
        return None
    return db_user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def delete_user(db: Session, nom: str):
    db_user = get_user_by_nom(db, nom=nom)
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    db.delete(db_user)
    db.commit()
    return {"message": "Utilisateur supprimé avec succès"}

def is_gerant(user: Utilisateurs):
    return user.role == RoleEnum.gerant

def get_user_by_role(db: Session, role: RoleEnum):
    return db.query(Utilisateurs).filter(Utilisateurs.role == role).first()

# Backend/services/user_service.py

def create_initial_gerant_if_none(db: Session):
    # On vérifie s'il existe déjà un gérant
    gerant = get_user_by_role(db, role=RoleEnum.gerant)
    
    if not gerant:
        # On récupère les identifiants depuis l'environnement (Azure ou .env)
        # Si rien n'est configuré, on met des valeurs par défaut temporaires
        admin_nom = os.getenv("FIRST_GERANT_NOM")
        admin_pass = os.getenv("FIRST_GERANT_PASS")
        
        first_gerant = UtilisateurCreate(
            nom=admin_nom,
            mot_de_passe=admin_pass,
            role=RoleEnum.gerant
        )
        create_user(db, first_gerant)
        print(f"🚀 [INIT] Compte gérant initial créé : {admin_nom}")
    else:
        print("✅ [INIT] Le gérant existe déjà, aucune action requise.")