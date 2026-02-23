from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from fastapi import HTTPException
from Backend.models import (
    Factures, HistoriqueVentesAgregees, BonsDeLivraison,
    LigneBL, Articles, PrixAchat, FactureBonLivraison, Clients as Client
)


def populate_sales_history(db: Session):
    """
    Analytical Aggregation Workflow:
    Pre-computes monthly financial metrics and stores them in a dedicated history table
    for high-performance dashboard retrieval.
    """
    try:
        years = db.query(extract('year', Factures.date_facture)).distinct().all()
        if not years:
            return

        db.query(HistoriqueVentesAgregees).delete()

        for (year,) in years:
            monthly_data = db.query(
                extract('month', Factures.date_facture).label('month'),
                func.sum(Factures.montant_net_dt).label('revenue'),
                func.sum(
                    # [REDACTED]: Proprietary margin computation formula
                    LigneBL.quantite
                ).label('gross_metric')
            ).join(
                FactureBonLivraison, Factures.id_facture == FactureBonLivraison.id_facture
            ).join(
                BonsDeLivraison, FactureBonLivraison.id_bl == BonsDeLivraison.id_bl
            ).join(
                LigneBL, BonsDeLivraison.id_bl == LigneBL.id_bl
            ).filter(
                extract('year', Factures.date_facture) == year
            ).group_by(
                extract('month', Factures.date_facture)
            ).all()

            for row in monthly_data:
                db.add(HistoriqueVentesAgregees(
                    annee=year,
                    mois=int(row.month),
                    chiffre_affaire=row.revenue or 0.0,
                    marge_brute=row.gross_metric or 0.0
                ))

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to populate analytical history.")


def get_yearly_kpis(db: Session, year: int):
    """
    KPI Computation Pattern:
    Returns aggregated yearly revenue, margin proxy, and average transaction value.
    """
    totals = db.query(
        func.sum(HistoriqueVentesAgregees.chiffre_affaire),
        func.sum(HistoriqueVentesAgregees.marge_brute)
    ).filter(HistoriqueVentesAgregees.annee == year).one_or_none()

    revenue = totals[0] if totals and totals[0] else 0.0
    margin = totals[1] if totals and totals[1] else 0.0

    invoices = db.query(func.count(Factures.id_facture)).filter(
        extract('year', Factures.date_facture) == year
    ).scalar() or 0

    avg_cart = revenue / invoices if invoices else 0.0

    return {
        "year": year,
        "revenue": revenue,
        "gross_margin": margin,
        "average_cart": avg_cart
    }


def get_monthly_kpis(db: Session, year: int):
    """
    Time-Series Retrieval Pattern:
    Provides ordered monthly financial indicators for dashboards.
    """
    rows = db.query(
        HistoriqueVentesAgregees.mois,
        HistoriqueVentesAgregees.chiffre_affaire,
        HistoriqueVentesAgregees.marge_brute
    ).filter(
        HistoriqueVentesAgregees.annee == year
    ).order_by(
        HistoriqueVentesAgregees.mois
    ).all()

    return [
        {"month": r.mois, "revenue": r.chiffre_affaire, "gross_margin": r.marge_brute}
        for r in rows
    ]


def get_client_profitability(db: Session, year: int):
    """
    Client Profitability Ranking:
    Aggregates profitability indicators per client and sorts by performance.
    """
    results = db.query(
        Client.id_client,
        Client.nom_client,
        func.sum(
            # [REDACTED]: Confidential profitability calculation
            LigneBL.quantite
        ).label("profit_metric")
    ).join(
        BonsDeLivraison, Client.id_client == BonsDeLivraison.id_client
    ).join(
        LigneBL, BonsDeLivraison.id_bl == LigneBL.id_bl
    ).filter(
        extract('year', BonsDeLivraison.date_bl) == year
    ).group_by(
        Client.id_client, Client.nom_client
    ).order_by(
        func.sum(LigneBL.quantite).desc()
    ).all()

    return [
        {
            "client_id": r.id_client,
            "client_name": r.nom_client,
            "profitability": float(r.profit_metric or 0.0)
        }
        for r in results
    ]


def get_client_monthly_profitability(db: Session, client_id: int, year: int, month: int):
    """
    Scoped Profitability Query:
    Returns profitability metrics for a single client on a specific period.
    """
    client = db.query(Client).filter(Client.id_client == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    metric = db.query(
        func.sum(
            # [REDACTED]: Proprietary financial computation
            LigneBL.quantite
        )
    ).join(
        BonsDeLivraison, LigneBL.id_bl == BonsDeLivraison.id_bl
    ).filter(
        BonsDeLivraison.id_client == client_id,
        extract('year', BonsDeLivraison.date_bl) == year,
        extract('month', BonsDeLivraison.date_bl) == month
    ).scalar() or 0.0

    return [{
        "client_id": client_id,
        "client_name": client.nom_client,
        "year": year,
        "month": month,
        "profitability": metric
    }]


def get_top_selling_items(db: Session, year: int, month: int):
    """
    Top-N Analytics Pattern:
    Retrieves best-performing items based on aggregated sales volume.
    """
    rows = db.query(
        Articles.id_article,
        Articles.nom_article,
        func.sum(LigneBL.quantite).label('volume')
    ).join(
        LigneBL, Articles.id_article == LigneBL.id_article
    ).join(
        BonsDeLivraison, LigneBL.id_bl == BonsDeLivraison.id_bl
    ).filter(
        extract('year', BonsDeLivraison.date_bl) == year,
        extract('month', BonsDeLivraison.date_bl) == month
    ).group_by(
        Articles.id_article, Articles.nom_article
    ).order_by(
        func.sum(LigneBL.quantite).desc()
    ).limit(5).all()

    return [
        {"item_id": r.id_article, "item_name": r.nom_article, "volume": int(r.volume)}
        for r in rows
    ]