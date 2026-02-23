import bcrypt
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.models import Utilisateurs, RoleEnum
from Backend.schemas import UtilisateurCreate
from Backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    """
    Secure Hashing Utility:
    Applies salted hashing to protect user credentials.
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """
    Credential Verification Pattern:
    Compares raw password with stored hash.
    """
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_user(db: Session, payload: UtilisateurCreate):
    """
    User Creation Workflow:
    Stores a new user with encrypted credentials and role assignment.
    """
    user = Utilisateurs(
        nom=payload.nom,
        role=payload.role,
        mot_de_passe=hash_password(payload.mot_de_passe)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str):
    """
    Authentication Pipeline:
    Validates credentials and returns user entity if authorized.
    """
    user = db.query(Utilisateurs).filter(Utilisateurs.nom == username).first()
    if not user or not verify_password(password, user.mot_de_passe):
        return None
    return user


def create_access_token(data: dict):
    """
    JWT Issuance Strategy:
    Generates a signed access token with expiration claims.
    """
    payload = data.copy()
    payload.update({"exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)})
    
    # [REDACTED]: custom claims / scopes logic
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def delete_user(db: Session, username: str):
    """
    Safe Deletion Pattern:
    Removes a user entity with existence validation.
    """
    user = db.query(Utilisateurs).filter(Utilisateurs.nom == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"status": "deleted"}


def is_manager(user: Utilisateurs):
    """
    Role-Based Access Check:
    Verifies if the user has elevated management privileges.
    """
    return user.role == RoleEnum.gerant


def ensure_initial_admin(db: Session):
    """
    Bootstrap Security Routine:
    Ensures a default administrative account exists at system initialization.
    """
    admin = db.query(Utilisateurs).filter(Utilisateurs.role == RoleEnum.gerant).first()

    if not admin:
        # [REDACTED]: environment-based secure credential provisioning
        initial_admin = UtilisateurCreate(
            nom="admin",
            mot_de_passe="secure-temp-password",
            role=RoleEnum.gerant
        )
        create_user(db, initial_admin)