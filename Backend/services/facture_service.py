# facture_service.py
from datetime import date
from sqlalchemy.orm import Session
from decimal import Decimal
from Backend.models import (
    BonsDeLivraison,
    LigneBL,
    Factures,
    Clients,
    TauxDeChangeMensuel,
    FactureBonLivraison
)
from fastapi import HTTPException
from num2words import num2words
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from Backend import schemas

def number_to_words(amount: float, currency_name: str = "dinar", cent_name: str = "millimes") -> str:
    # On arrondit d'abord à 3 décimales pour éviter les résidus binaires (ex: 0.60999999)
    amount = round(amount, 3)
    
    entiere = int(amount)
    
    if cent_name.lower() == "millimes":
        # Extraction précise des 3 chiffres après la virgule
        decimales = int(round((amount - entiere) * 1000))
        format_chiffre = f"{decimales:03d}"
    else:
        # Pour l'euro, on reste sur 2 chiffres
        decimales = int(round((amount - entiere) * 100))
        format_chiffre = f"{decimales:02d}"

    lettres_entiere = num2words(entiere, lang='fr')
    
    if decimales > 0:
        return f"{lettres_entiere} {currency_name} et {format_chiffre} {cent_name}"
    else:
        return f"{lettres_entiere} {currency_name}"

from sqlalchemy.orm import joinedload
from sqlalchemy import not_, func
from sqlalchemy.orm import Session, joinedload

import calendar
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from Backend import models


def generer_facture_client_manuelle(db: Session, request_data: schemas.FactureGenerationRequest):

    id_client = request_data.id_client
    mois = request_data.mois
    annee = request_data.annee
    num_facture = request_data.numero_facture_manuel
    remise_globale_pct = Decimal(str(request_data.remise_globale_facture or 0))

    # 1. Calcul de la période
    dernier_jour = calendar.monthrange(annee, mois)[1]
    date_debut_periode = date(annee, mois, 1)
    date_fin_periode = date(annee, mois, dernier_jour)

    # 2. Récupération des BL non facturés
    bls_non_factures = (
        db.query(models.BonsDeLivraison)
        .outerjoin(models.FactureBonLivraison)
        .filter(
            models.BonsDeLivraison.id_client == id_client,
            models.BonsDeLivraison.date_bl.between(date_debut_periode, date_fin_periode),
            models.FactureBonLivraison.id_facture == None
        ).all()
    )

    if not bls_non_factures:
        raise ValueError("Aucun bon de livraison à facturer pour cette période.")

    # 3. Récupération du Taux de Change
    taux_obj = db.query(models.TauxDeChangeMensuel).filter_by(mois=mois, annee=annee).first()
    if not taux_obj:
        raise ValueError(f"Taux de change non configuré pour {mois}/{annee}")
    taux_conversion = Decimal(str(taux_obj.taux))

    # 4. Préparation des constantes de précision
    D2 = Decimal('0.01')  # Pour arrondir à 2 chiffres (Euro)
    D3 = Decimal('0.001') # Pour arrondir à 3 chiffres (Dinar Tunisien)

    # 4. Calcul des montants par ligne
    id_bls = [bl.id_bl for bl in bls_non_factures]
    lignes = (
        db.query(models.LigneBL)
        .options(joinedload(models.LigneBL.article), joinedload(models.LigneBL.stock_se))
        .filter(models.LigneBL.id_bl.in_(id_bls))
        .all()
    )

    total_apres_remises_articles_euro = Decimal('0.00')

    for ligne in lignes:
        brut_ligne_euro = Decimal(str(ligne.prix_total_ligne))
        remise_art_pct = Decimal(str(ligne.remise or 0))
        
        # --- CALCUL CRITIQUE : NET LIGNE ---
        # On calcule le prix de la ligne après remise article (du BL)
        net_ligne_euro = (brut_ligne_euro * (1 - (remise_art_pct / Decimal('100')))).quantize(D2)
        
        # Cumul pour le montant total de la facture
        total_apres_remises_articles_euro += net_ligne_euro

    # --- 5. Application de la REMISE GLOBALE ---
    reduction_globale = (total_apres_remises_articles_euro * (remise_globale_pct / Decimal('100'))).quantize(D2)
    
    montant_net_final_euro = total_apres_remises_articles_euro - reduction_globale
    
    # --- CALCUL DT AVEC 3 DÉCIMALES ---
    # Ici, on multiplie par le taux et on force l'arrondi à 0.001 pour ne pas perdre les 4 millimes
    montant_net_final_dt = (montant_net_final_euro * taux_conversion).quantize(D3)
    montant_total_dt = (total_apres_remises_articles_euro * taux_conversion).quantize(D3)

    # --- 6. SE et Finalisation ---
    numeros_se_uniques = sorted({l.stock_se.numero_se for l in lignes if l.stock_se})
    numeros_se_str = ", ".join(numeros_se_uniques)

    # --- 7. Création de la Facture avec valeurs quantisées ---
    nouvelle_facture = models.Factures(
        numero_facture=num_facture,
        date_facture=date_fin_periode,
        id_client=id_client,
        
        # Montant Total = Somme des lignes après remises articles (Sous-total)
        montant_total_euro=total_apres_remises_articles_euro.quantize(D2),
        montant_total_dt=montant_total_dt,
        
        # Remise Globale (Pied de facture)
        remise_pourcentage=remise_globale_pct,
        
        # Montant Net Final
        montant_net_euro=montant_net_final_euro.quantize(D2),
        montant_net_dt=montant_net_final_dt, # Contiendra bien 132.924 par exemple
        
        taux_conversion=taux_conversion,
        total_en_lettre_euro=number_to_words(float(montant_net_final_euro), "euro", "centimes"),
        total_en_lettre_dt=number_to_words(float(montant_net_final_dt), "dinar", "millimes"),
        
        numeros_se=numeros_se_str,
        poid_en_kg=Decimal(str(request_data.poids_total or 0)),
        incoterm=request_data.incoterm
    )

    db.add(nouvelle_facture)
    db.flush()
    
    for bl in bls_non_factures:
        db.add(models.FactureBonLivraison(id_facture=nouvelle_facture.id_facture, id_bl=bl.id_bl))

    db.commit()
    db.refresh(nouvelle_facture)
    return nouvelle_facture


import csv
import io
from decimal import Decimal

def generate_facture_csv(facture, lignes):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    # 1. EN-TÊTE DE LA FACTURE
    writer.writerow(["NUMERO FACTURE", facture.numero_facture])
    writer.writerow(["DATE", facture.date_facture.strftime("%d/%m/%Y")])
    writer.writerow(["CLIENT", facture.client.nom_client])
    writer.writerow(["TAUX DE CHANGE", f"{float(facture.taux_conversion):.4f}"])
    writer.writerow([])  # Ligne vide

    # 2. TABLEAU DES ARTICLES
    # Note : On utilise les noms et prix archivés
    writer.writerow([
        "Référence", "Désignation", "N° SE", "Quantité", 
        "PU HT (EUR)", "Remise Art. (%)", "Total Ligne HT (EUR)", "Total Ligne HT (DT)"
    ])

    taux = Decimal(str(facture.taux_conversion))

    for ligne in lignes:
        #nom_art = getattr(ligne, 'nom_article_archive', None) or (ligne.article.nom_article if ligne.article else "N/A")
        cat_art = getattr(ligne, 'categorie_archive', None) or (ligne.article.categorie if ligne.article else "N/A")
        num_se = ligne.stock_se.numero_se if ligne.stock_se else "N/A"
        pu_euro = Decimal(str(ligne.prix_unitaire))
        qte = Decimal(str(ligne.quantite))
        remise_art = Decimal(str(ligne.remise or 0))
        
        # Calcul du net par ligne (déjà fait dans le backend, mais on recalcule pour le CSV)
        total_ligne_euro = (pu_euro * qte * (1 - (remise_art / Decimal('100'))))
        total_ligne_dt = total_ligne_euro * taux

        writer.writerow([
            ligne.article.reference if ligne.article else "N/A",
            cat_art,
            num_se,
            int(qte),
            f"{float(pu_euro):.2f}",
            f"{float(remise_art):.2f}",
            f"{float(total_ligne_euro):.2f}",
            f"{float(total_ligne_dt):.3f}" # 3 décimales pour le DT
        ])

    # 3. BLOC DES TOTAUX (PIED DE PAGE)
    writer.writerow([])
    writer.writerow(["", "", "", "", "", "TOTAL HT (EUR)", f"{float(facture.montant_total_euro):.2f}"])
    
    if facture.remise_pourcentage and facture.remise_pourcentage > 0:
        writer.writerow(["", "", "", "", "", f"REMISE GLOBALE ({facture.remise_pourcentage}%)", 
                         f"-{float(facture.montant_total_euro - facture.montant_net_euro):.2f}"])
    
    writer.writerow(["", "", "", "", "", "NET A PAYER (EUR)", f"{float(facture.montant_net_euro):.2f}"])
    writer.writerow(["", "", "", "", "", "NET A PAYER (DT)", f"{float(facture.montant_net_dt):.3f}"])

    # 4. ENCODAGE ET BOM
    content = output.getvalue()
    return io.BytesIO(b'\xef\xbb\xbf' + content.encode("utf-8"))


def modifier_taux_change(db: Session, mois: int, annee: int, nouveau_taux: Decimal):
    taux_existant = db.query(TauxDeChangeMensuel).filter_by(mois=mois, annee=annee).first()
    if not taux_existant:
        raise HTTPException(status_code=404, detail="Le taux de change pour ce mois n'existe pas.")

    taux_existant.taux = nouveau_taux
    db.commit()
    return {"message": "Taux de change modifié avec succès."}


import calendar
from datetime import date

def get_clients_avec_bl_non_factures(db: Session, mois: int, annee: int):
    # 1. Définir strictement le début et la fin du mois choisi
    date_debut = date(annee, mois, 1)
    dernier_jour = calendar.monthrange(annee, mois)[1]
    date_fin = date(annee, mois, dernier_jour)

    # 2. Sous-requête pour exclure les BL déjà liés à une facture
    sous_requete_bls_factures = db.query(models.FactureBonLivraison.id_bl)

    # 3. Requête : Clients ayant des BL entre le 1er et le 31 du mois ET non facturés
    clients = db.query(models.Clients).join(models.BonsDeLivraison).filter(
        models.BonsDeLivraison.date_bl >= date_debut,
        models.BonsDeLivraison.date_bl <= date_fin,
        ~models.BonsDeLivraison.id_bl.in_(sous_requete_bls_factures)
    ).distinct().all()

    return clients

def modifier_taux_change(db: Session, mois: int, annee: int, nouveau_taux: Decimal):
    taux_existant = db.query(TauxDeChangeMensuel).filter_by(mois=mois, annee=annee).first()
    if not taux_existant:
        raise HTTPException(status_code=404, detail="Le taux de change pour ce mois n'existe pas.")

    taux_existant.taux = nouveau_taux
    db.commit()
    return {"message": "Taux de change modifié avec succès."}


