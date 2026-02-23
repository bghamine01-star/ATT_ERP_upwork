from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from Backend.database import get_db
from Backend.services import facture_service
from pydantic import BaseModel, Field
from typing import Optional
from Backend.models import TauxDeChangeMensuel, Factures
from Backend.schemas import TauxRequest, FactureGenerationRequest, TauxUpdateRequest, FactureResponse
from decimal import Decimal
from datetime import datetime, date
from Backend.services import facture_pdf_service
from fastapi.responses import Response
from typing import List
from fastapi.responses import Response, StreamingResponse
import calendar
from Backend.models import FactureBonLivraison, BonsDeLivraison, LigneBL

router = APIRouter(
    prefix="/factures",
    tags=["Factures"]
)


@router.post("/ajouter")
def ajouter_taux_mensuel(data: TauxRequest, db: Session = Depends(get_db)):
    # Vérifie que le taux n'est pas déjà défini pour ce mois
    existant = db.query(TauxDeChangeMensuel).filter_by(mois=data.mois, annee=data.annee).first()
    if existant:
        raise HTTPException(status_code=400, detail="Un taux de change est déjà défini pour ce mois.")

    taux = TauxDeChangeMensuel(
        mois=data.mois,
        annee=data.annee,
        taux=data.taux,
        devise=data.devise
    )

    db.add(taux)
    db.commit()
    return {"message": "Taux de change enregistré avec succès."}


@router.put("/modifier_taux")
def modifier_taux_mensuel(data: TauxUpdateRequest, db: Session = Depends(get_db)):
    taux_existant = db.query(TauxDeChangeMensuel).filter_by(mois=data.mois, annee=data.annee).first()
    if not taux_existant:
        raise HTTPException(status_code=404, detail="Le taux de change pour ce mois n'existe pas.")

    taux_existant.taux = data.nouveau_taux
    db.commit()
    return {"message": "Taux de change modifié avec succès."}


from Backend.schemas import FactureGenerationRequest # Assure-toi que ce schéma est à jour

@router.post("/generer")
def generer_facture(request: FactureGenerationRequest, db: Session = Depends(get_db)):
    try:
        # On appelle le nouveau service avec les données manuelles
        facture = facture_service.generer_facture_client_manuelle(db, request)
        
        return {
            "status": "success",
            "facture_id": facture.id_facture,
            "numero": facture.numero_facture
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except ValueError as e:
        # Pour intercepter les erreurs de taux de change manquant par exemple
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

from io import BytesIO
@router.get("/pdf/{facture_id}")
def get_facture_pdf(facture_id: int, db: Session = Depends(get_db)):
    # 1. Génération du contenu PDF via le service
    # On s'attend à ce que le service retourne les bytes du PDF
    pdf_content = facture_pdf_service.generer_facture_pdf(db, facture_id)
    
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    # 2. Utilisation d'un buffer mémoire pour le streaming
    # FPDF.output(dest='S') retourne une chaîne de caractères (latin-1) 
    # ou des bytes selon la version. On s'assure d'envoyer des bytes.
    if isinstance(pdf_content, str):
        pdf_bytes = pdf_content.encode('latin-1')
    else:
        pdf_bytes = pdf_content

    # 3. Retour du fichier via StreamingResponse
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=facture_{facture_id}.pdf"
        }
    )

@router.get("/clients-non-factures/")
def afficher_clients_non_factures(mois: int, annee: int, db: Session = Depends(get_db)):
    return facture_service.get_clients_avec_bl_non_factures(db, mois, annee)

@router.get("/all", response_model=List[FactureResponse])
def get_all_factures(mois: int, annee: int, db: Session = Depends(get_db)):
    # Filtrer par mois et année pour optimiser les performances
    date_debut = date(annee, mois, 1)
    dernier_jour = calendar.monthrange(annee, mois)[1]
    date_fin = date(annee, mois, dernier_jour)

    factures = db.query(Factures).filter(
        Factures.date_facture.between(date_debut, date_fin)
    ).all()
    
    return [
        {
            "id_facture": f.id_facture,
            "numero_facture": f.numero_facture,
            "date_facture": f.date_facture,
            "client_nom": f.client.nom_client,
            "montant_net_dt": float(f.montant_net_dt)
        }
        for f in factures
    ]

@router.get("/{id_facture}/csv")
def get_facture_csv(id_facture: int, db: Session = Depends(get_db)):
    # 1. Récupérer la facture
    facture = db.query(Factures).filter(Factures.id_facture == id_facture).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    # 2. Récupérer toutes les lignes associées via les BL
    # On passe par la table de liaison FactureBonLivraison
    lignes = (
        db.query(LigneBL)
        .options(
            joinedload(LigneBL.article),
            joinedload(LigneBL.stock_se) # Crucial pour le N° SE
        )
        .join(BonsDeLivraison)
        .join(FactureBonLivraison)
        .filter(FactureBonLivraison.id_facture == id_facture)
        .all()
    )

    # 3. Générer le fichier
    csv_file = facture_service.generate_facture_csv(facture, lignes)
    
    filename = f"Facture_{facture.numero_facture or id_facture}.csv"
    
    return StreamingResponse(
        csv_file, 
        media_type="text/csv; charset=utf-8", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    
@router.delete("/all")
def delete_all_factures(db: Session = Depends(get_db)):
    try:
        # Supprimer toutes les lignes de la table Factures
        num_deleted = db.query(Factures).delete()
        db.commit()
        return {"message": f"{num_deleted} factures ont été supprimées avec succès."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression des factures: {str(e)}")