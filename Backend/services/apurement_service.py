from sqlalchemy.orm import Session
from sqlalchemy import func
from Backend import models
from datetime import date
from fastapi import HTTPException

def get_apurement_by_se(db: Session, numero_se: str, reference_article: str = None):
    # 1. Récupérer le stock SE
    stock = db.query(models.StockSE).filter(models.StockSE.numero_se == numero_se).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Numéro SE non trouvé")

    # 2. Calcul des articles
    articles_details = []
    articles_dans_ce_se = db.execute(
        models.association_table.select().where(models.association_table.c.stock_se_id == stock.id_se)
    ).fetchall()

    for row in articles_dans_ce_se:
        art = db.query(models.Articles).get(row.article_id)
        vendu = db.query(func.sum(models.LigneBL.quantite)).filter(
            models.LigneBL.stock_se_id == stock.id_se,
            models.LigneBL.id_article == row.article_id
        ).scalar() or 0
        
        articles_details.append({
            "reference": art.reference,
            "nom_article": art.nom_article,
            "quantite_initiale": row.quantite_dans_stock + vendu,
            "quantite_vendue": vendu,
            "quantite_restante": row.quantite_dans_stock
        })

    # 3. Récupérer les factures liées (avec FILTRE OPTIONNEL)
    query = db.query(
        models.Factures.numero_facture,
        models.Factures.date_facture,
        models.Articles.reference,
        models.LigneBL.quantite
    ).join(models.FactureBonLivraison, models.Factures.id_facture == models.FactureBonLivraison.id_facture)\
     .join(models.BonsDeLivraison, models.FactureBonLivraison.id_bl == models.BonsDeLivraison.id_bl)\
     .join(models.LigneBL, models.BonsDeLivraison.id_bl == models.LigneBL.id_bl)\
     .join(models.Articles, models.LigneBL.id_article == models.Articles.id_article)\
     .filter(models.LigneBL.stock_se_id == stock.id_se)

    # AJOUT DU FILTRE PAR RÉFÉRENCE SI FOURNIE
    if reference_article:
        query = query.filter(models.Articles.reference == reference_article)

    factures_query = query.all()

    factures_details = [
        {
            "numero_facture": f[0], 
            "date_facture": f[1], 
            "article_reference": f[2], 
            "quantite_art_concerne": f[3]
        }
        for f in factures_query
    ]

    # 4. Calcul de l'échéance
    apurement_info = db.query(models.Apurement).filter(models.Apurement.id_se == stock.id_se).first()
    if not apurement_info:
        raise HTTPException(status_code=404, detail="Détails d'apurement introuvables")

    jours_restants = (apurement_info.date_echeance_actuelle - date.today()).days

    return {
        "numero_se": stock.numero_se,
        "date_importation": stock.date_importation,
        "date_echeance": apurement_info.date_echeance_actuelle,
        "jours_restants": jours_restants,
        "est_apure": stock.est_apure,
        "articles": articles_details,
        "factures": factures_details
    }


def cloturer_apurement(db: Session, numero_se: str):
    stock = db.query(models.StockSE).filter(models.StockSE.numero_se == numero_se).first()
    if not stock: return None
    
    stock.est_apure = True
    apurement = db.query(models.Apurement).filter(models.Apurement.id_se == stock.id_se).first()
    if apurement:
        apurement.statut = "Apuré"
        apurement.date_cloture = date.today()
    
    db.commit()
    return True