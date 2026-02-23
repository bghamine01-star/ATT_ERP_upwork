import os
from dotenv import load_dotenv

load_dotenv()

# On définit les variables directement au lieu d'utiliser une classe
SECRET_KEY = os.getenv("SECRET_KEY", "une-valeur-par-defaut-non-securisee")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))