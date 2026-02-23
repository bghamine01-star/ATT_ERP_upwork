from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import joinedload
from Backend import models
from Backend.schemas import CreerVenteSchema, BLFilterParams, BLResponseItem, BLGroupedResponse
from typing import List, Dict, Union
from collections import defaultdict
from dateutil.relativedelta import relativedelta 
from typing import Optional
from pypdf import PdfReader, PdfWriter


from sqlalchemy import func

def generer_numero_sequence(db: Session, prefixe: str, modele):
    # On cherche le dernier numéro de BL par ordre décroissant
    dernier = db.query(modele).order_by(modele.id_bl.desc()).first()
    annee_actuelle = datetime.now().year
    
    if not dernier:
        return f"{prefixe}-{annee_actuelle}-0001"
    
    # On extrait le dernier compteur (on suppose le format PREFIX-ANNEE-XXXX)
    try:
        dernier_num = int(dernier.numero_bl.split('-')[-1])
        nouveau_num = dernier_num + 1
    except (ValueError, IndexError):
        nouveau_num = 1
        
    return f"{prefixe}-{annee_actuelle}-{nouveau_num:04d}"
    
from sqlalchemy.orm import Session
from sqlalchemy import update, and_
from decimal import Decimal
from Backend import models, schemas
from datetime import datetime

def creer_vente(db: Session, vente_data: schemas.CreerVenteSchema):
    
    # --- NOUVELLE CONDITION DE SÉCURITÉ ---
    today = date.today()
    # On définit le premier jour du mois courant (ex: 2026-02-01)
    premier_jour_mois_courant = date(today.year, today.month, 1)
    
    # Si la date du BL est inférieure au 1er jour du mois actuel -> C'est un mois passé
    if vente_data.date_bl < premier_jour_mois_courant:
        raise ValueError(
            f"Impossible de créer un BL pour un mois passé ({vente_data.date_bl.strftime('%m/%Y')}). "
            "La période est clôturée."
        )
    # ---------------------------------------
    
    # 1. Vérification client
    client = db.query(models.Clients).filter(models.Clients.id_client == vente_data.client_id).first()
    if not client:
        raise ValueError("Client non trouvé")
    
    # 2. Sécurisation du Stock (Concurrence)
    references_demandees = [item.reference for item in vente_data.articles]
    
    # Utilisation de with_for_update() pour verrouiller les lignes d'articles
    # Cela empêche une autre transaction de modifier ces stocks simultanément
    articles_query = (
        db.query(models.Articles)
        .filter(models.Articles.reference.in_(references_demandees))
        .with_for_update()
    )
    
    articles_map = {article.reference: article for article in articles_query.all()}
    
    if len(articles_map) != len(references_demandees):
        references_non_trouvees = set(references_demandees) - set(articles_map.keys())
        raise ValueError(f"Articles inexistants : {references_non_trouvees}")
        
    # 3. Vérification unicité BL
    if db.query(models.BonsDeLivraison).filter(models.BonsDeLivraison.numero_bl == vente_data.numero_bl).first():
        raise ValueError(f"Le numéro de BL '{vente_data.numero_bl}' existe déjà.")
    
    # 4. Initialisation BL
    bon_livraison = models.BonsDeLivraison(
        date_bl=vente_data.date_bl,
        numero_bl=vente_data.numero_bl,
        id_client=vente_data.client_id,
        total_a_payer=Decimal('0.00')
    )
    db.add(bon_livraison)
    db.flush()

    total_vente_hors_remise = Decimal('0.00')

    for item in vente_data.articles:
        article = articles_map[item.reference]
        prix_unitaire_actuel = article.prix_vente  # On récupère le prix à l'instant T
        
        if article.quantite_disponible < item.quantite:
            raise ValueError(f"Stock insuffisant pour '{article.reference}'. Dispo: {article.quantite_disponible}")
        
        quantite_restante_a_prelever = item.quantite
        
        # 5. FIFO - Récupération des lots disponibles
        stock_fifo = (
            db.query(
                models.StockSE, 
                models.association_table.c.quantite_dans_stock, 
                models.association_table.c.stock_se_id
            )
            .join(models.association_table, models.StockSE.id_se == models.association_table.c.stock_se_id)
            .filter(models.association_table.c.article_id == article.id_article)
            .filter(models.association_table.c.quantite_dans_stock > 0)
            .order_by(models.StockSE.date_importation.asc())
            .with_for_update(of=models.StockSE) # Verrouille aussi les lots
            .all()
        )

        for stock_se, quantite_en_lot, stock_se_id in stock_fifo:
            if quantite_restante_a_prelever <= 0:
                break
            
            quantite_prelevee = min(quantite_restante_a_prelever, quantite_en_lot)
            quantite_restante_a_prelever -= quantite_prelevee
            
            prix_unitaire = article.prix_vente
            prix_total_ligne = prix_unitaire * Decimal(str(quantite_prelevee))
            total_vente_hors_remise += prix_total_ligne
            
            # Création ligne BL
            ligne_bl = models.LigneBL(
                id_bl=bon_livraison.id_bl,
                id_article=article.id_article,
                quantite=quantite_prelevee,
                prix_unitaire=prix_unitaire_actuel, # ON FIGE LE PRIX ICI
                nom_article_archive=article.nom_article, # ON FIGE LE NOM ICI
                categorie_archive= article.categorie, # ON FIGE LA CATEGORIE ICI
                prix_total_ligne=prix_unitaire_actuel * Decimal(str(quantite_prelevee)),
                stock_se_id=stock_se_id,
                remise=Decimal(str(item.remise))
            )
            db.add(ligne_bl)
            
            # Mise à jour Lot SE (Table associative)
            db.execute(
                update(models.association_table)
                .where(and_(
                    models.association_table.c.article_id == article.id_article,
                    models.association_table.c.stock_se_id == stock_se_id
                ))
                .values(quantite_dans_stock=models.association_table.c.quantite_dans_stock - quantite_prelevee)
            )

            # Mise à jour StockSE parent
            db.execute(
                update(models.StockSE)
                .where(models.StockSE.id_se == stock_se_id)
                .values(quantite_totale=models.StockSE.quantite_totale - quantite_prelevee)
            )

        # 6. Mise à jour globale Article
        article.quantite_disponible -= item.quantite
        
        if quantite_restante_a_prelever > 0:
            raise ValueError(f"Incohérence FIFO : Manque {quantite_restante_a_prelever} unités pour '{article.reference}'.")
            
    # 7. Finalisation
    bon_livraison.total_a_payer = total_vente_hors_remise
    
    try:
        db.commit()
        db.refresh(bon_livraison)
        return bon_livraison
    except Exception as e:
        db.rollback()
        raise e


def get_bon_livraison(db: Session, bon_livraison_id: int):
    return db.query(models.BonsDeLivraison).filter(models.BonsDeLivraison.id_bl == bon_livraison_id).first()

def supprimer_bon_livraison(db: Session, id_bl: int):
    # Vérifie l'existence du BL
    bl = db.query(models.BonsDeLivraison).filter(models.BonsDeLivraison.id_bl == id_bl).first()
    if not bl:
        raise HTTPException(status_code=404, detail="Bon de livraison non trouvé")

    # --- NOUVELLE CONDITION DE SÉCURITÉ ---
    # Vérifie si le BL est déjà associé à une facture
    facture_associee = db.query(models.FactureBonLivraison).filter(models.FactureBonLivraison.id_bl == id_bl).first()
    if facture_associee:
        raise HTTPException(
            status_code=400, 
            detail="Suppression impossible : ce bon de livraison est déjà associé à une facture."
        )
    # ---------------------------------------

    # Récupère toutes les lignes du BL
    lignes_bl = db.query(models.LigneBL).filter(models.LigneBL.id_bl == id_bl).all()

    for ligne in lignes_bl:
        article_id = ligne.id_article
        stock_se_id = ligne.stock_se_id
        quantite = ligne.quantite

        # Remet à jour la quantité disponible dans Articles
        db.execute(
            update(models.Articles)
            .where(models.Articles.id_article == article_id)
            .values(quantite_disponible=models.Articles.quantite_disponible + quantite)
        )

        # Remet à jour la quantité dans StockSE
        db.execute(
            update(models.StockSE)
            .where(models.StockSE.id_se == stock_se_id)
            .values(quantite_totale=models.StockSE.quantite_totale + quantite)
        )

        # Remet à jour la quantité dans la table d'association
        db.execute(
            update(models.association_table)
            .where(
                models.association_table.c.article_id == article_id,
                models.association_table.c.stock_se_id == stock_se_id
            )
            .values(
                quantite_dans_stock=models.association_table.c.quantite_dans_stock + quantite
            )
        )

    # Supprimer les lignes de BL
    db.query(models.LigneBL).filter(models.LigneBL.id_bl == id_bl).delete()

    # Supprimer le BL lui-même
    db.query(models.BonsDeLivraison).filter(models.BonsDeLivraison.id_bl == id_bl).delete()

    db.commit()
    return {"message": "Bon de livraison supprimé et stock restauré avec succès"}





'''    Récupération des bons de livraison du mois'''

def get_bons_livraison_du_mois(db: Session, annee: int, mois: int):
    try:
        date_debut = date(annee, mois, 1)
        if mois == 12:
            date_fin = date(annee + 1, 1, 1)
        else:
            date_fin = date(annee, mois + 1, 1)
    except ValueError:
        raise ValueError("Mois ou année invalide.")

    bons = (
        db.query(models.BonsDeLivraison)
        .options(joinedload(models.BonsDeLivraison.client))
        .filter(models.BonsDeLivraison.date_bl >= date_debut,
                models.BonsDeLivraison.date_bl < date_fin)
        .order_by(models.BonsDeLivraison.date_bl.desc())
        .all()
    )
    return bons



# Fichier : Backend/services/ventes_service.py

def get_bons_livraison_formattes_direct(
    db: Session,
    annee: int,
    mois: Optional[int] = None,
    client_id: Optional[int] = None,
    group_by_client: Optional[bool] = False
):
    try:
        # 1. Gestion des dates pour le filtrage
        date_debut = date(annee, mois if mois else 1, 1)
        if mois:
            date_fin = date_debut + relativedelta(months=1)
        else:
            date_fin = date_debut + relativedelta(years=1)
    
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Erreur de date: {e}")

    # 2. Construction de la requête avec jointures pour la performance
    query = db.query(models.BonsDeLivraison).options(
        joinedload(models.BonsDeLivraison.client),
        joinedload(models.BonsDeLivraison.facture_associee)
    ).filter(
        models.BonsDeLivraison.date_bl >= date_debut,
        models.BonsDeLivraison.date_bl < date_fin
    )

    if client_id:
        query = query.filter(models.BonsDeLivraison.id_client == client_id)

    bons = query.order_by(models.BonsDeLivraison.date_bl.desc()).all()

    # 3. Formatage de la réponse
    results = []
    for bl in bons:
        # Un BL est considéré comme facturé s'il existe une entrée dans la table de liaison
        deja_facture = bl.facture_associee is not None
        
        results.append({
            "id_bl": bl.id_bl,
            "numero_bl": bl.numero_bl,
            "date_bl": bl.date_bl.isoformat(),
            "total_a_payer": float(bl.total_a_payer),
            "client": bl.client.nom_client,
            "est_facture": deja_facture
        })

    # 4. Groupement optionnel par client
    if group_by_client:
        grouped = defaultdict(list)
        for item in results:
            grouped[item["client"]].append(item)
        return dict(grouped)
    
    return results


'''
    Génération du csv pour le bon de livraison  '''
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io
import csv

def generate_bl_csv(bl, lignes, client):
    output = io.StringIO()
    # On force le délimiteur à ';' pour une meilleure compatibilité Excel
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    # En-têtes de document
    writer.writerow(["Bon de Livraison", bl.numero_bl])
    writer.writerow(["Date", bl.date_bl.strftime("%d/%m/%Y")])
    writer.writerow(["Client", f"{client.nom_client}"])
    writer.writerow(["Adresse", f"{client.adresse}"])
    writer.writerow([])  # ligne vide

    # Colonnes du tableau
    # Note : On ajoute la remise par ligne car elle est importante
    writer.writerow(["Référence", "Désignation", "Prix Unitaire (EUR)", "Remise (%)", "Quantité", "Total Ligne (EUR)"])

    # Données des lignes
    for ligne in lignes:
        # On utilise le nom archivé pour la cohérence historique
        cat_art = getattr(ligne, 'categorie_archive', None) or (ligne.article.categorie if ligne.article else "N/A")
        
        writer.writerow([
            ligne.article.reference if ligne.article else "N/A",
            cat_art,
            f"{float(ligne.prix_unitaire):.2f}",
            f"{float(ligne.remise or 0):.2f}",
            ligne.quantite,
            f"{float(ligne.prix_total_ligne):.2f}"
        ])

    # Total global
    writer.writerow([])
    writer.writerow(["", "", "", "", "Total à payer (EUR)", f"{float(bl.total_a_payer):.2f}"])

    # --- CRUCIAL : Ajout du BOM UTF-8 pour Excel ---
    content = output.getvalue()
    # On ajoute le BOM (B'\xef\xbb\xbf') au début du flux binaire
    return io.BytesIO(b'\xef\xbb\xbf' + content.encode("utf-8"))


import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io
from num2words import num2words
from reportlab.lib.utils import simpleSplit # Pour le retour à la ligne

def generate_bl_pdf(bl, lignes, client, image_template_path=""):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    items_per_page = 20 
    total_items = len(lignes)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    total_ht_general = sum(float(l.prix_total_ligne) for l in lignes)

    euros = int(total_ht_general)
    centimes = int(round((total_ht_general - euros) * 100))
    texte_montant = num2words(euros, lang='fr').capitalize() + " euros"
    if centimes > 0:
        texte_montant += " et " + num2words(centimes, lang='fr') + " centimes"

    X_START = 354.3
    X_MAX = 495.0
    MAX_WIDTH = X_MAX - X_START

    for pg in range(total_pages):
        try:
            image = ImageReader(image_template_path)
            p.drawImage(image, 0, 0, width=595.27, height=841.89, mask='auto')
        except Exception as e:
            print(f"Erreur image: {e}")

        # --- BLOC CLIENT (Police inchangée) ---
        p.setFont("Helvetica-Bold", 11)
        nom_lignes = simpleSplit(client.nom_client, p._fontname, p._fontsize, MAX_WIDTH)
        y_cursor = 730.3
        for line in nom_lignes:
            p.drawString(X_START, y_cursor, line)
            y_cursor -= 13.0

        p.setFont("Helvetica", 9)
        y_cursor -= 4.0 
        adresse_text = client.adresse or ""
        addr_lignes = simpleSplit(adresse_text, p._fontname, p._fontsize, MAX_WIDTH)
        for line in addr_lignes:
            p.drawString(X_START, y_cursor, line)
            y_cursor -= 11.0
            
        # 3. Matricule Fiscale (Juste en bas de l'adresse)
        p.setFont("Helvetica", 9)
        y_cursor -= 2.0 # Petit espacement avant la matricule
        matricule = getattr(client, 'matricule_fiscal', 'N/A') # Récupère l'attribut s'il existe
        p.drawString(X_START, y_cursor, f"{matricule}")

        p.drawString(354.3, 750.0, f"Page {pg+1} / {total_pages}")

        # --- BLOC INFOS (Police inchangée) ---
        p.setFont("Helvetica-Bold", 12)
        y_infos_row = 685.0
        p.drawCentredString(105.6, 690.0, str(bl.numero_bl))
        p.setFont("Helvetica", 10)
        p.drawCentredString(206.9, y_infos_row, bl.date_bl.strftime("%d/%m/%Y"))
        p.drawCentredString(275.0, y_infos_row, str(client.code_client))

        # --- ARTICLES (Changement vers Courier 11) ---
        p.setFont("Courier", 10.5) 
        start_idx = pg * items_per_page
        current_lignes = lignes[start_idx : start_idx + items_per_page]
        y_line = 605.3
        for ligne in current_lignes:
            pu = float(ligne.prix_unitaire)
            cat_art = str(ligne.categorie_archive or ligne.article.categorie) # Fallback au cas où
            qte = int(ligne.quantite)
            total_ligne = float(ligne.prix_total_ligne)
            
            p.drawCentredString(88.0, y_line, str(ligne.article.reference))
            p.drawString(155, y_line, cat_art[:40])
            p.drawCentredString(399.5, y_line, str(qte))
            p.drawCentredString(456.25, y_line, f"{pu:,.2f}")
            p.drawCentredString(527.75, y_line, f"{total_ligne:,.2f}")
            y_line -= 19.3
            
        # --- MONTANT EN LETTRES (Changement vers Courier 11) ---
        p.setFont("Courier", 11)
        p.drawString(33.0, 83, texte_montant)

        # --- TOTAUX (Police inchangée) ---
        p.setFont("Helvetica-Bold", 11)
        p.drawRightString(555.6, 196, f"{total_ht_general:,.2f}")
        p.drawRightString(555.6, 160.6, f"{total_ht_general:,.2f}")

        p.showPage()

    p.save()
    buffer.seek(0)
    return buffer

