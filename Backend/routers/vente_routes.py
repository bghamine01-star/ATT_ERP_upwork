from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Backend.database import get_db
from Backend.schemas import CreerVenteSchema, BonDeLivraisonSchema, BLResponseItem, BLGroupedResponse, BLFilterParams
from fastapi import Query
from Backend.services import ventes_service
from Backend import models
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import joinedload
from typing import Optional, Union, List
from pydantic import BaseModel, Field

# Standardisation : on utilise un préfixe commun pour le routeur
router = APIRouter(prefix="/ventes", tags=["ventes"])


class BLFilterParams(BaseModel):
    annee: int = Field(..., ge=2000)
    mois: Optional[int] = Field(None, ge=1, le=12)
    client_id: Optional[int] = None
    group_by_client: Optional[bool] = False

@router.post("/", response_model=BonDeLivraisonSchema)
def creer_nouvelle_vente(vente_data: CreerVenteSchema, db: Session = Depends(get_db)):
    try:
        bon_livraison = ventes_service.creer_vente(db, vente_data)
        return bon_livraison
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
@router.get("/bons-de-livraison/filter", response_model=Union[List[BLResponseItem], BLGroupedResponse])
def get_bons_livraison_filtres(
    annee: int = Query(..., ge=2000),
    mois: Optional[int] = Query(None, ge=1, le=12),
    client_id: Optional[int] = None,
    group_by_client: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    # Pass the parameters directly to the service
    return ventes_service.get_bons_livraison_formattes_direct(
        db=db,
        annee=annee,
        mois=mois,
        client_id=client_id,
        group_by_client=group_by_client
    )

@router.get("/bons-de-livraison/{bon_livraison_id}", response_model=BonDeLivraisonSchema)
def lire_bon_livraison(bon_livraison_id: int, db: Session = Depends(get_db)):
    bon_livraison = ventes_service.get_bon_livraison(db, bon_livraison_id)
    if not bon_livraison:
        raise HTTPException(status_code=404, detail="Bon de livraison non trouvé")
    return bon_livraison

@router.delete("/bons-de-livraison/{id_bl}", status_code=status.HTTP_200_OK)
def delete_bl(id_bl: int, db: Session = Depends(get_db)):
    try:
        ventes_service.supprimer_bon_livraison(db, id_bl)
        return {"message": "Bon de livraison supprimé et stock restauré avec succès"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur inattendue est survenue: {e}")

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import joinedload

@router.get("/bons-de-livraison/{numero_bl}/pdf")
def get_bon_livraison_pdf(numero_bl: str, db: Session = Depends(get_db)):
    # 1. Récupération du BL par son numéro
    bl = db.query(models.BonsDeLivraison).filter(models.BonsDeLivraison.numero_bl == numero_bl).first()
    if not bl:
        raise HTTPException(status_code=404, detail="Bon de livraison non trouvé")
    
    # 2. Récupération des lignes avec chargement de l'article lié
    lignes = db.query(models.LigneBL).options(
        joinedload(models.LigneBL.article)
    ).filter(models.LigneBL.id_bl == bl.id_bl).all()

    # 3. Récupération du client
    client = db.query(models.Clients).filter(models.Clients.id_client == bl.id_client).first()
    
    # 4. Chemin du logo
    logo_path = ""
    
    # 5. Génération
    pdf_file = ventes_service.generate_bl_pdf(bl, lignes, client, logo_path)
    
    return StreamingResponse(
        pdf_file, 
        media_type="application/pdf", 
        headers={
            "Content-Disposition": f"inline; filename=bon_livraison_{numero_bl}.pdf"
        }
    )
    

@router.get("/bons-de-livraison/{numero_bl}/csv")
def get_bon_livraison_csv(numero_bl: str, db: Session = Depends(get_db)):
    bl = db.query(models.BonsDeLivraison).filter(models.BonsDeLivraison.numero_bl == numero_bl).first()
    if not bl:
        raise HTTPException(status_code=404, detail="Bon de livraison non trouvé")
    
    lignes = db.query(models.LigneBL).options(
        joinedload(models.LigneBL.article)
    ).filter(models.LigneBL.id_bl == bl.id_bl).all()

    client = db.query(models.Clients).filter(models.Clients.id_client == bl.id_client).first()
    
    # Appel du service corrigé
    csv_file = ventes_service.generate_bl_csv(bl, lignes, client)
    
    return StreamingResponse(
        csv_file, 
        media_type="text/csv; charset=utf-8", 
        headers={
            "Content-Disposition": f"attachment; filename=BL_{numero_bl}.csv"
        }
    )