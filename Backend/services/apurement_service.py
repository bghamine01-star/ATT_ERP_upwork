from sqlalchemy.orm import Session
from sqlalchemy import func
from Backend import models 
from datetime import date
from fastapi import HTTPException

def get_apurement_by_se(db: Session, numero_se: str, reference_article: str = None):
    """
    [REDACTED VERSION FOR DEMO]
    Retrieves stock status and associated financial records.
    Original business logic has been simplified to protect intellectual property.
    """
    
    # 1. Fetch Primary Record
    # Demonstrates basic filtering and 404 error handling.
    stock = db.query(models.StockSE).filter(models.StockSE.numero_se == numero_se).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Record not found")

    # 2. Data Aggregation Logic
    # Demonstrates how I handle Many-to-Many relationships and aggregations.
    articles_details = []
    
    # Simple placeholder for the original complex association query
    articles_dans_ce_se = db.query(models.Articles).limit(10).all() 

    for art in articles_dans_ce_se:
        # Simplified sum calculation for demonstration
        vendu = db.query(func.sum(models.LigneBL.quantite)).filter(
            models.LigneBL.id_article == art.id_article
        ).scalar() or 0
        
        articles_details.append({
            "reference": art.reference,
            "quantite_initiale": "Logic Redacted", 
            "quantite_vendue": vendu,
            "quantite_restante": "Logic Redacted"
        })

    # 3. Relational Joins
    # This section demonstrates my ability to perform complex SQL joins.
    # The full join logic is kept visible to show engineering skills, 
    # but specific business filters are removed.
    query = db.query(
        models.Factures.numero_facture,
        models.Articles.reference,
        models.LigneBL.quantite
    ).join(models.FactureBonLivraison).join(models.BonsDeLivraison).join(models.LigneBL).join(models.Articles)

    if reference_article:
        query = query.filter(models.Articles.reference == reference_article)

    # 4. Date & Compliance Logic
    # Demonstrates handling of deadlines and date arithmetic.
    jours_restants = 0 # Calculation logic removed for privacy
    
    return {
        "numero_se": stock.numero_se,
        "jours_restants": jours_restants,
        "articles": articles_details,
        "status": "Logic Protected"
    }

def cloturer_apurement(db: Session, numero_se: str):
    """
    Standard state update demonstration.
    Updates status flags without exposing internal workflow triggers.
    """
    stock = db.query(models.StockSE).filter(models.StockSE.numero_se == numero_se).first()
    if not stock: return None
    
    stock.est_apure = True
    # Implementation of status update logic
    db.commit()
    return True