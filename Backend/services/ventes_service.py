import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io
from num2words import num2words
from reportlab.lib.utils import simpleSplit # Pour le retour à la ligne

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from datetime import date
from typing import Optional, Dict, List
from collections import defaultdict
from Backend import models

# =========================================================
# Récupérer un bon de livraison (version sécurisée client)
# =========================================================
def get_bon_livraison_secure(db: Session, bon_livraison_id: int):
    bl = (
        db.query(models.BonsDeLivraison)
        .options(joinedload(models.BonsDeLivraison.client))
        .filter(models.BonsDeLivraison.id_bl == bon_livraison_id)
        .first()
    )

    if not bl:
        raise HTTPException(status_code=404, detail="Bon de livraison non trouvé")

    return {
        "id": bl.id_bl,
        "numero": bl.numero_bl,
        "date": bl.date_bl.isoformat(),
        "total": float(bl.total_a_payer),
        "client": bl.client.nom_client if bl.client else None,
        "est_facture": bl.facture_associee is not None
    }


# =========================================================
# Liste des BL (filtrée & sécurisée)
# =========================================================
def get_bons_livraison_secure(
    db: Session,
    annee: int,
    mois: Optional[int] = None,
    client_id: Optional[int] = None,
    group_by_client: Optional[bool] = False
):
    try:
        date_debut = date(annee, mois if mois else 1, 1)
        if mois:
            if mois == 12:
                date_fin = date(annee + 1, 1, 1)
            else:
                date_fin = date(annee, mois + 1, 1)
        else:
            date_fin = date(annee + 1, 1, 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Paramètres de date invalides")

    query = (
        db.query(models.BonsDeLivraison)
        .options(
            joinedload(models.BonsDeLivraison.client),
            joinedload(models.BonsDeLivraison.facture_associee)
        )
        .filter(
            models.BonsDeLivraison.date_bl >= date_debut,
            models.BonsDeLivraison.date_bl < date_fin
        )
    )

    if client_id:
        query = query.filter(models.BonsDeLivraison.id_client == client_id)

    bons = query.order_by(models.BonsDeLivraison.date_bl.desc()).all()

    results = [
        {
            "id": bl.id_bl,
            "numero": bl.numero_bl,
            "date": bl.date_bl.isoformat(),
            "total": float(bl.total_a_payer),
            "client": bl.client.nom_client if bl.client else None,
            "est_facture": bl.facture_associee is not None
        }
        for bl in bons
    ]

    if group_by_client:
        grouped: Dict[str, List[dict]] = defaultdict(list)
        for item in results:
            grouped[item["client"]].append(item)
        return dict(grouped)

    return results


# =========================================================
# Suppression sécurisée (sans logique exposée)
# =========================================================
def supprimer_bon_livraison_secure(db: Session, id_bl: int):
    bl = db.query(models.BonsDeLivraison).filter(models.BonsDeLivraison.id_bl == id_bl).first()

    if not bl:
        raise HTTPException(status_code=404, detail="Bon de livraison introuvable")

    if bl.facture_associee:
        raise HTTPException(
            status_code=400,
            detail="Suppression impossible : BL déjà facturé"
        )

    db.delete(bl)
    db.commit()

    return {"message": "Bon de livraison supprimé"}


# =========================================================
# Liste simple par mois (ultra minimale)
# =========================================================
def get_bons_livraison_mois_secure(db: Session, annee: int, mois: int):
    try:
        date_debut = date(annee, mois, 1)
        if mois == 12:
            date_fin = date(annee + 1, 1, 1)
        else:
            date_fin = date(annee, mois + 1, 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Date invalide")

    bons = (
        db.query(models.BonsDeLivraison)
        .options(joinedload(models.BonsDeLivraison.client))
        .filter(
            models.BonsDeLivraison.date_bl >= date_debut,
            models.BonsDeLivraison.date_bl < date_fin
        )
        .order_by(models.BonsDeLivraison.date_bl.desc())
        .all()
    )

    return [
        {
            "id": bl.id_bl,
            "numero": bl.numero_bl,
            "date": bl.date_bl.isoformat(),
            "total": float(bl.total_a_payer),
            "client": bl.client.nom_client if bl.client else None
        }
        for bl in bons
    ]

def generate_bl_pdf(bl, lignes, client, image_template_path=""):
    pass

