# user_route.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from Backend.services import user_service as utilisateur_service
from Backend.schemas import UtilisateurCreate, UtilisateurLogin, Token, Utilisateur, RoleEnum, TokenData
from Backend.database import get_db
from Backend.models import RoleEnum, Utilisateurs
from Backend.config import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

router = APIRouter(tags=["users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")



def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        nom: str = payload.get("sub")
        role: str = payload.get("role")
        if nom is None or role is None:
            raise credentials_exception
        token_data = TokenData(nom=nom, role=role)
    except JWTError:
        raise credentials_exception
    user = utilisateur_service.get_user_by_nom(db, nom=token_data.nom)
    if user is None:
        raise credentials_exception
    return user

def gerant_only(current_user: Utilisateur = Depends(get_current_user)):
    if current_user.role != RoleEnum.gerant:
        raise HTTPException(status_code=403, detail="Accès interdit. Seul le gérant peut effectuer cette action")
    return current_user


@router.post("/first_gerant/", response_model=None)
def create_first_gerant(db: Session = Depends(get_db)):
    # Vérifie si un gérant existe déjà
    gerant = utilisateur_service.get_user_by_role(db, role=RoleEnum.gerant)
    if gerant:
        raise HTTPException(status_code=400, detail="Un gérant existe déjà")

    # Crée le premier gérant
    first_gerant = UtilisateurCreate(
        nom="admin",  # Vous pouvez changer le nom
        mot_de_passe="bk",  # N'oubliez pas de changer le mot de passe
        role=RoleEnum.gerant,
    )
    utilisateur_service.create_user(db, first_gerant)
    return {"message": "Premier gérant créé avec succès"}



@router.post("/users/", response_model=None, dependencies=[Depends(gerant_only)])
def create_user(user: UtilisateurCreate, db: Session = Depends(get_db)):
    db_user = utilisateur_service.create_user(db, user)
    return {"message": "Utilisateur créé avec succès"}

@router.post("/token/", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = utilisateur_service.authenticate_user(db, form_data.username, form_data.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Nom ou mot de passe incorrect")
    
    user_role = db_user.role.value # Get the string value from the Enum
    access_token = utilisateur_service.create_access_token(data={"sub": db_user.nom, "role": user_role})
    return {"access_token": access_token, "token_type": "bearer", "user_role": user_role}

@router.delete("/users/{nom}", response_model=None, dependencies=[Depends(gerant_only)])
def delete_user(nom: str, db: Session = Depends(get_db)):
    return utilisateur_service.delete_user(db, nom)

@router.get("/users/me/", response_model=Utilisateur)
def read_users_me(current_user: Utilisateur = Depends(get_current_user)):
    return current_user 

@router.get("/users/", response_model=list[Utilisateur], dependencies=[Depends(gerant_only)])
def list_users(db: Session = Depends(get_db)):
    return db.query(Utilisateurs).all()