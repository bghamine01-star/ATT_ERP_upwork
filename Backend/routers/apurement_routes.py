from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Backend.database import get_db
from Backend.services import apurement_service
from Backend.schemas import ApurementDetailResponse
from typing import Optional

router = APIRouter(prefix="/apurement", tags=["Apurement"])

@router.get("/recherche/{numero_se}", response_model=ApurementDetailResponse)
def rechercher_apurement(
    numero_se: str, 
    reference: Optional[str] = None, # Paramètre optionnel
    db: Session = Depends(get_db)
):
    return apurement_service.get_apurement_by_se(db, numero_se, reference)

"""
@router.get("/recherche/{numero_se}", response_model=ApurementDetailResponse)
def rechercher_apurement(numero_se: str, db: Session = Depends(get_db)):
    return apurement_service.get_apurement_by_se(db, numero_se)
""" 

@router.post("/cloturer/{numero_se}")
def valider_apurement(numero_se: str, db: Session = Depends(get_db)):
    success = apurement_service.cloturer_apurement(db, numero_se)
    if not success:
        raise HTTPException(status_code=404, detail="Erreur lors de la clôture")
    return {"message": f"Stock SE {numero_se} marqué comme apuré."}

