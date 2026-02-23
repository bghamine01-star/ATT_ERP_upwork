from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from Backend.models import (
    Factures, HistoriqueVentesAgregees, BonsDeLivraison, 
    LigneBL, Articles, PrixAchat, FactureBonLivraison
)
from Backend.models import Clients as Client
from Backend.schemas import ClientProfitability, ClientMonthlyProfitability
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def populate_historique_ventes(db: Session):
    """
    Agrège les données de vente et de marge brute par année et par mois pour toutes les années
    et les stocke dans la table HistoriqueVentesAgregees pour une récupération rapide.
    """
    try:
        # Trouver toutes les années uniques avec des factures
        years_with_data = db.query(extract('year', Factures.date_facture)).distinct().all()
        years_to_process = [year[0] for year in years_with_data]
        
        # S'il n'y a pas de données, sortir
        if not years_to_process:
            logger.info("Aucune donnée de facture trouvée à agréger.")
            return

        # Supprimer toutes les entrées existantes avant de les recréer
        db.query(HistoriqueVentesAgregees).delete()

        for year in years_to_process:
            # Agrégation des ventes par mois et par année
            ventes_mensuelles = db.query(
                extract('month', Factures.date_facture).label('mois'),
                func.sum(Factures.montant_net_dt).label('chiffre_affaire'),
                func.sum(
                    (Articles.prix_vente - PrixAchat.prix_achat) * LigneBL.quantite
                ).label('marge_brute')
            ).join(
                FactureBonLivraison, Factures.id_facture == FactureBonLivraison.id_facture
            ).join(
                BonsDeLivraison, FactureBonLivraison.id_bl == BonsDeLivraison.id_bl
            ).join(
                LigneBL, BonsDeLivraison.id_bl == LigneBL.id_bl
            ).join(
                Articles, LigneBL.id_article == Articles.id_article
            ).join(
                PrixAchat, Articles.id_article == PrixAchat.article_id
            ).filter(
                extract('year', Factures.date_facture) == year
            ).group_by(
                extract('month', Factures.date_facture)
            ).all()

            for mois_data in ventes_mensuelles:
                historique = HistoriqueVentesAgregees(
                    annee=year,
                    mois=int(mois_data.mois),
                    chiffre_affaire=mois_data.chiffre_affaire if mois_data.chiffre_affaire is not None else 0.0,
                    marge_brute=mois_data.marge_brute if mois_data.marge_brute is not None else 0.0
                )
                db.add(historique)
        
        db.commit()
        logger.info("Historique des ventes agrégé et mis à jour pour toutes les années.")
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la mise à jour de l'historique des ventes : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur lors de la mise à jour des données.")
    


        
def get_yearly_revenue(db: Session, annee: int):
    result = db.query(
        func.sum(HistoriqueVentesAgregees.chiffre_affaire),
        func.sum(HistoriqueVentesAgregees.marge_brute)
    ).filter(
        HistoriqueVentesAgregees.annee == annee
    ).one_or_none()

    chiffre_affaire = result[0] if result and result[0] is not None else 0.0
    marge_brute = result[1] if result and result[1] is not None else 0.0

    nombre_factures_result = db.query(
        func.count(Factures.id_facture)
    ).filter(
        extract('year', Factures.date_facture) == annee
    ).scalar()
    
    nombre_factures = nombre_factures_result if nombre_factures_result is not None else 0

    panier_moyen = chiffre_affaire / nombre_factures if nombre_factures > 0 else 0.0

    return {
        "annee": annee,
        "total_revenue": chiffre_affaire,
        "total_gross_margin": marge_brute,
        "average_cart": panier_moyen
    }
    
    
    
def get_monthly_revenue(db: Session, annee: int):
    results = db.query(
        HistoriqueVentesAgregees.mois,
        HistoriqueVentesAgregees.chiffre_affaire,
        HistoriqueVentesAgregees.marge_brute
    ).filter(
        HistoriqueVentesAgregees.annee == annee
    ).order_by(
        HistoriqueVentesAgregees.mois
    ).all()
    
    return [{"month": r.mois, "revenue": r.chiffre_affaire, "gross_margin": r.marge_brute} for r in results]


def get_client_profitability_by_year(db: Session, year: int):
    """
    Récupère la marge brute totale par client pour une année donnée en utilisant
    la formule (prix_vente - prix_achat) * quantité.
    """
    results = db.query(
        Client.id_client,
        Client.nom_client,
        func.sum(
            (Articles.prix_vente - PrixAchat.prix_achat) * LigneBL.quantite
        ).label("total_gross_margin")
    ).join(BonsDeLivraison, Client.id_client == BonsDeLivraison.id_client
    ).join(LigneBL, BonsDeLivraison.id_bl == LigneBL.id_bl
    ).join(Articles, LigneBL.id_article == Articles.id_article
    ).join(PrixAchat, Articles.id_article == PrixAchat.article_id
    ).filter(
        extract('year', BonsDeLivraison.date_bl) == year
    ).group_by(
        Client.id_client, Client.nom_client
    ).order_by(
        func.sum(
            (Articles.prix_vente - PrixAchat.prix_achat) * LigneBL.quantite
        ).desc()
    ).all()
    
    return [
        {
            "id_client": row.id_client,
            "client_name": row.nom_client,
            "total_gross_margin": float(row.total_gross_margin) if row.total_gross_margin else 0.0
        } for row in results
    ]

def get_client_monthly_profitability(db: Session, id_client: int, annee: int, mois: int):
    # Log de débogage pour voir les paramètres
    logger.debug(f"Début de la récupération des données de rentabilité mensuelle pour le client {id_client}, année {annee}, mois {mois}")

    # Vérification de l'existence du client
    client = db.query(Client).filter(Client.id_client == id_client).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client avec l'ID {id_client} non trouvé.")

    # Requête pour récupérer les données agrégées
    result = db.query(
        func.sum(
            (Articles.prix_vente - PrixAchat.prix_achat) * LigneBL.quantite
        )
    ).select_from(Factures).join(
        FactureBonLivraison, Factures.id_facture == FactureBonLivraison.id_facture
    ).join(
        BonsDeLivraison, FactureBonLivraison.id_bl == BonsDeLivraison.id_bl
    ).join(
        LigneBL, BonsDeLivraison.id_bl == LigneBL.id_bl
    ).join(
        Articles, LigneBL.id_article == Articles.id_article
    ).join(
        PrixAchat, Articles.id_article == PrixAchat.article_id
    ).filter(
        Factures.id_client == id_client,
        extract('year', Factures.date_facture) == annee,
        extract('month', Factures.date_facture) == mois
    ).scalar()

    # Si aucun résultat, la marge est 0.0
    marge_brute = result if result is not None else 0.0

    return [{
        "id_client": id_client,
        "nom_client": client.nom_client,
        "annee": annee,
        "mois": mois,
        "marge_brute": marge_brute
    }]

def get_top_selling_articles_monthly(db: Session, annee: int, mois: int):
    """
    Récupère le Top 5 des articles les plus vendus (par quantité) pour une année et un mois donnés.
    """
    results = db.query(
        Articles.id_article,
        Articles.nom_article,
        func.sum(LigneBL.quantite).label('total_quantite_vendue')
    ).join(
        LigneBL, Articles.id_article == LigneBL.id_article
    ).join(
        BonsDeLivraison, LigneBL.id_bl == BonsDeLivraison.id_bl
    ).filter(
        extract('year', BonsDeLivraison.date_bl) == annee,
        extract('month', BonsDeLivraison.date_bl) == mois
    ).group_by(
        Articles.id_article, Articles.nom_article
    ).order_by(
        # Trié par quantité vendue en ordre décroissant
        func.sum(LigneBL.quantite).desc()
    ).limit(5).all()

    return [
        {
            "id_article": r.id_article,
            "nom_article": r.nom_article,
            "quantite_vendue": int(r.total_quantite_vendue)
        } for r in results
    ]