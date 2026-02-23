from sqlalchemy.orm import Session
from sqlalchemy import insert, delete, update, func
from Backend import models, schemas
from fastapi import HTTPException
from datetime import timedelta
from typing import List

def create_stock_se_with_articles(db: Session, stock_se_data: schemas.StockSECreateWithArticlesSchema):
    """
    Complex Transactional Workflow:
    Creates a new stock batch, initializes compliance tracking, and handles 
    Upsert (Update or Insert) logic for associated items.
    """
    if not stock_se_data.articles:
        raise ValueError("At least one article must be associated with this stock.")
    
    try:
        # 1. Primary Record Creation (Atomic Operation)
        db_stock_se = models.StockSE(
            numero_se=stock_se_data.numero_se,
            date_importation=stock_se_data.date_importation,
            quantite_totale=0,
            est_apure=False
        )
        db.add(db_stock_se)
        db.flush() # Flush to get the ID for relationships

        # 2. Compliance Tracker Initialization
        # Logic: Automatically sets a 1-year regulatory deadline.
        echeance = db_stock_se.date_importation + timedelta(days=365)
        db_apurement = models.Apurement(
            id_se=db_stock_se.id_se,
            date_echeance_actuelle=echeance,
            statut="En cours"
        )
        db.add(db_apurement)

        # 3. Dynamic Inventory Upsert Logic
        for article_data in stock_se_data.articles:
            # Check if article exists globally by reference
            db_article = db.query(models.Articles).filter(
                models.Articles.reference == article_data.reference
            ).first()

            if db_article:
                # [SECURITY REDACTED]: Logic for updating existing global inventory metrics
                db_article.quantite_disponible += article_data.quantite_dans_stock
                article_id = db_article.id_article
            else:
                # Global Creation of a new inventory item
                db_article = models.Articles(
                    reference=article_data.reference,
                    quantite_disponible=article_data.quantite_dans_stock
                )
                db.add(db_article)
                db.flush()
                article_id = db_article.id_article

            # Association Logic: Handles many-to-many relationship with batch-specific quantities
            # [REDACTED]: Specific association check and conditional Insert/Update
            pass 

        db.commit()
        return db_stock_se

    except Exception as e:
        db.rollback() # Ensure data consistency on failure
        raise e

def delete_stock_se_safely(db: Session, id_se: int):
    """
    Safety-First Deletion Pattern:
    Prevents deletion of records that have linked sales data (Delivery Notes).
    """
    # 1. Foreign Key Constraint Simulation
    # Prevents deleting a batch if sales (LigneBL) are already registered.
    existe_vente = db.query(models.LigneBL).filter(models.LigneBL.stock_se_id == id_se).first()
    
    if existe_vente:
        raise HTTPException(
            status_code=400, 
            detail="Deletion denied: Associated sales records found."
        )

    try:
        # 2. Inventory Restoration Logic
        # Before deletion, the quantities are deducted from global stock.
        # [REDACTED]: Iterative stock correction logic
        
        # 3. Cascaded Cleanup (Manual cleanup of related business entities)
        db.query(models.Apurement).filter(models.Apurement.id_se == id_se).delete()
        
        # 4. Final Record Removal
        db.query(models.StockSE).filter(models.StockSE.id_se == id_se).delete()

        db.commit()
        return {"status": "success"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transactional error during deletion")

def search_articles_optimized(db: Session, reference: str = None, designation: str = None, limit: int = 100):
    """
    Performance Optimized Search:
    Implements case-insensitive filtering and pagination to handle large datasets.
    """
    query = db.query(models.Articles)

    if reference:
        query = query.filter(models.Articles.reference.ilike(f"%{reference}%"))
    
    # Execution with safety limit to prevent memory overflow
    articles = query.limit(limit).all()
    
    # Transformation to DTO (Data Transfer Object) for API response
    return [{"id": a.id_article, "ref": a.reference} for a in articles] # Simplified for demo

def update_bulk_prix_achat(db: Session, updates: List[schemas.BulkPrixAchatUpdate]):
    """
    Bulk Processing Pattern:
    Processes multiple updates in a single database transaction for maximum performance.
    """
    try:
        for item in updates:
            # Atomic logic applied to each item
            pass # [REDACTED]: Detailed update/create logic
        
        db.commit() # One single commit for the entire batch
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise e