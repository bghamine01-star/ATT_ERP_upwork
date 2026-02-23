import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from Backend.database import get_db
from Backend.services import dashboard_service
from Backend.routers import user_routes
from Backend import schemas

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(user_routes.gerant_only)],
    responses={404: {"description": "Not found"}}
)

@router.get("/populate")
def populate_data_route(db: Session = Depends(get_db)):
    dashboard_service.populate_historique_ventes(db)
    return {"message": "Historique des ventes agrégé et mis à jour."}

@router.get("/yearly-revenue", response_model=schemas.YearlyRevenue)
def get_yearly_revenue_route(annee: int, db: Session = Depends(get_db)):
    return dashboard_service.get_yearly_revenue(db, annee)

@router.get("/monthly-revenue/{annee}", response_model=List[schemas.MonthlyRevenue])
def get_monthly_revenue_route(annee: int, db: Session = Depends(get_db)):
    return dashboard_service.get_monthly_revenue(db, annee)

@router.get("/client-profitability", response_model=List[schemas.ClientProfitability])
def get_client_profitability_route(annee: int, db: Session = Depends(get_db)):
    return dashboard_service.get_client_profitability_by_year(db, annee)
    
@router.get("/client-monthly-profitability", response_model=List[Dict[str, Any]])
def get_client_monthly_profitability_route(
    id_client: int = Query(...),
    annee: int = Query(...),
    mois: int = Query(...),
    db: Session = Depends(get_db)
):
    return dashboard_service.get_client_monthly_profitability(db, id_client, annee, mois)


@router.get("/top-articles-monthly", response_model=List[Dict[str, Any]])
def get_top_articles_monthly_route(
    annee: int = Query(...),
    mois: int = Query(...),
    db: Session = Depends(get_db)
):
    """
    Route API pour obtenir le Top 5 des articles les plus vendus pour un mois donné.
    """
    return dashboard_service.get_top_selling_articles_monthly(db, annee, mois)
