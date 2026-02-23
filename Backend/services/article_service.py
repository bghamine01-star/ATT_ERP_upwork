from sqlalchemy.orm import Session
from sqlalchemy import insert, delete, update
from Backend import models, schemas
from sqlalchemy import insert
from fastapi import HTTPException
from datetime import timedelta
from typing import List

def create_stock_se_with_articles(db: Session, stock_se_data: schemas.StockSECreateWithArticlesSchema):
    if not stock_se_data.articles:
        raise ValueError("Au moins un article doit être associé à ce Stock SE.")
    
    try:
        # 1. Création du Stock SE
        db_stock_se = models.StockSE(
            numero_se=stock_se_data.numero_se,
            date_importation=stock_se_data.date_importation,
            fournisseur=stock_se_data.fournisseur,
            quantite_totale=0,
            est_apure=False
        )
        db.add(db_stock_se)
        db.flush()

        # 2. Initialisation Apurement (inchangé)
        echeance = db_stock_se.date_importation + timedelta(days=365)
        db_apurement = models.Apurement(
            id_se=db_stock_se.id_se,
            date_echeance_initiale=echeance,
            date_echeance_actuelle=echeance,
            statut="En cours"
        )
        db.add(db_apurement)

        total_quantite_stock_se = 0
        
        for article_data in stock_se_data.articles:
            # LOGIQUE : Recherche par Référence (Clé unique)
            db_article = db.query(models.Articles).filter(
                models.Articles.reference == article_data.reference
            ).first()

            if db_article:
                # MISE À JOUR : Si l'article existe, on met à jour le prix de vente PARTOUT
                db_article.prix_vente = article_data.prix_vente
                db_article.quantite_disponible += article_data.quantite_dans_stock
                # Optionnel : mise à jour du nom si besoin de synchronisation
                db_article.nom_article = article_data.nom_article 
                article_id = db_article.id_article
            else:
                # CRÉATION : Nouvel article
                db_article = models.Articles(
                    nom_article=article_data.nom_article,
                    reference=article_data.reference,
                    prix_vente=article_data.prix_vente,
                    quantite_disponible=article_data.quantite_dans_stock,
                    categorie=article_data.categorie,
                    emplacement=article_data.emplacement
                )
                db.add(db_article)
                db.flush()
                article_id = db_article.id_article

            # Association Article <-> StockSE (Table de liaison)
            existing_assoc = db.query(models.association_table).filter(
                models.association_table.c.article_id == article_id,
                models.association_table.c.stock_se_id == db_stock_se.id_se
            ).first()

            if existing_assoc:
                # Si ça existe déjà, on UPDATE la quantité au lieu d'INSERT
                stmt = (
                    update(models.association_table)
                    .where(models.association_table.c.article_id == article_id)
                    .where(models.association_table.c.stock_se_id == db_stock_se.id_se)
                    .values(quantite_dans_stock=existing_assoc.quantite_dans_stock + article_data.quantite_dans_stock)
                )
                db.execute(stmt)
            else:
                # Sinon, on fait l'INSERT classique
                stmt = insert(models.association_table).values(
                    article_id=article_id,
                    stock_se_id=db_stock_se.id_se,
                    quantite_dans_stock=article_data.quantite_dans_stock
                )
                db.execute(stmt)

            total_quantite_stock_se += article_data.quantite_dans_stock

        db_stock_se.quantite_totale = total_quantite_stock_se
        db.commit()
        db.refresh(db_stock_se)
        return db_stock_se

    except Exception as e:
        db.rollback()
        raise e



# NOUVELLE MÉTHODE : Update groupé des prix d'achat pour le gérant
def update_bulk_prix_achat(db: Session, updates: List[schemas.BulkPrixAchatUpdate]):
    updated_count = 0
    try:
        for item in updates:
            # On appelle la logique sans commit immédiat
            success = create_or_update_logic_only(db, item.article_id, item.prix_achat)
            if success:
                updated_count += 1
        
        # Un SEUL commit pour tout le lot
        db.commit() 
        return {"status": "success", "updated_count": updated_count}
    except Exception as e:
        db.rollback()
        raise e
    
def create_or_update_logic_only(db: Session, article_id: int, new_prix_achat: float | None):
    """Logique pure sans commit pour permettre le traitement en masse"""
    db_prix_achat = db.query(models.PrixAchat).filter(models.PrixAchat.article_id == article_id).first()
    
    if new_prix_achat is None:
        if db_prix_achat:
            db.delete(db_prix_achat)
    else:
        if db_prix_achat:
            db_prix_achat.prix_achat = new_prix_achat
        else:
            new_entry = models.PrixAchat(article_id=article_id, prix_achat=new_prix_achat)
            db.add(new_entry)
    return True

def update_article_metadata_safe(
    db: Session, 
    numero_se: str, 
    article_reference: str, 
    data: schemas.ArticleMetadataUpdate
):
    # 1. Vérifier que l'article existe dans ce stock précis (sécurité contexte)
    stock_assoc = db.query(models.StockSE).join(models.Articles, models.StockSE.articles).filter(
        models.StockSE.numero_se == numero_se,
        models.Articles.reference == article_reference
    ).first()

    if not stock_assoc:
        raise ValueError(f"L'article {article_reference} n'existe pas dans le stock {numero_se}")

    # 2. Mise à jour de l'Article (Globalement)
    db_article = db.query(models.Articles).filter(models.Articles.reference == article_reference).first()
    
    if data.prix_vente is not None:
        db_article.prix_vente = data.prix_vente
    if data.categorie is not None:
        db_article.categorie = data.categorie
    if data.emplacement is not None:
        db_article.emplacement = data.emplacement
    if data.nom_article is not None:
        db_article.nom_article = data.nom_article

    # 3. Mise à jour du Stock SE (Métadonnées uniquement)
    if data.fournisseur_stock is not None:
        stock_assoc.fournisseur = data.fournisseur_stock

    try:
        db.commit()
        db.refresh(db_article)
        return {"status": "success", "message": "Mise à jour effectuée avec succès"}
    except Exception as e:
        db.rollback()
        raise e

def get_all_stock_ses(db: Session):
    """
    Récupère tous les stocks SE de la base de données.
    """
    return db.query(models.StockSE).order_by(models.StockSE.numero_se.asc()).all()


def get_article_by_reference_with_stock_info(db: Session, reference: str):
    article = db.query(models.Articles).filter(models.Articles.reference == reference).first()
    if article:
        stock_se_details = db.query(
            models.association_table.c.stock_se_id,
            models.association_table.c.quantite_dans_stock,
            models.StockSE.numero_se,
            models.StockSE.date_importation  
        ).\
            join(models.StockSE, models.association_table.c.stock_se_id == models.StockSE.id_se).\
            filter(models.association_table.c.article_id == article.id_article).all()

        stock_info_list = []
        for stock_id, quantite, numero_se, date_importation in stock_se_details:
            stock_info_list.append({
                "numero_se": numero_se,
                "quantite_dans_stock": quantite,
                "date_importation": date_importation  # Ajouter la date à la liste
            })

        return schemas.ArticleWithStockSEDetails(
            id_article=article.id_article,
            nom_article=article.nom_article,
            reference=article.reference,
            prix_vente=article.prix_vente,
            quantite_disponible=article.quantite_disponible,
            categorie=article.categorie,
            emplacement=article.emplacement,
            stock_se_details=stock_info_list
        )
    return None


def get_articles_by_stock_se_with_info(db: Session, numero_se: str):
    stock_se = db.query(models.StockSE).filter(models.StockSE.numero_se == numero_se).first()
    if stock_se:
        articles_in_stock = []
        for association in stock_se.articles:
            articles_in_stock.append(schemas.ArticleInStockSE(
                id_article=association.id_article,
                nom_article=association.nom_article,
                reference=association.reference,
                prix_vente=association.prix_vente,
                categorie=association.categorie,
                quantite_dans_stock_se=db.query(models.association_table.c.quantite_dans_stock).filter(
                    models.association_table.c.article_id == association.id_article,
                    models.association_table.c.stock_se_id == stock_se.id_se
                ).scalar(),
                emplacement=association.emplacement
            ))

        stock_se_schema = schemas.StockSESchemaOut.from_orm(stock_se)
        return schemas.StockSEWithArticles(stock_se=stock_se_schema, articles=articles_in_stock)
    return None

def search_articles_optimized(db: Session, reference: str = None, designation: str = None, limit: int = 100):
    """
    Recherche optimisée utilisant les index GIN et limitant les résultats.
    """
    # Si aucun critère, on ne renvoie rien pour économiser les ressources
    if not reference and not designation:
        return []

    query = db.query(models.Articles)

    if reference:
        query = query.filter(models.Articles.reference.ilike(f"%{reference}%"))
    
    if designation:
        query = query.filter(models.Articles.nom_article.ilike(f"%{designation}%"))

    # Exécution de la requête avec limite
    articles = query.limit(limit).all()

    # Transformation en dictionnaire pour le JSON (Data Transfer Object)
    results = []
    for a in articles:
        results.append({
            "id_article": a.id_article,
            "reference": a.reference,
            "nom_article": a.nom_article,
            "categorie": a.categorie,
            "emplacement": a.emplacement,
            "prix_vente": float(a.prix_vente), # Conversion DECIMAL -> float pour JSON
            "quantite_disponible": a.quantite_disponible,
            "prix_achat": float(a.prix_achat.prix_achat) if a.prix_achat else None
        })
    
    return results

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def get_stock_details_by_numero(db: Session, numero_se: str):
    """Récupère les détails complets du lot pour suppression et édition des prix"""
    stock_se = db.query(models.StockSE).filter(models.StockSE.numero_se == numero_se).first()
    if not stock_se:
        return None
    
    articles_list = []
    for art in stock_se.articles:
        # On récupère la quantité spécifique à ce lot
        qty = db.query(models.association_table.c.quantite_dans_stock).filter(
            models.association_table.c.article_id == art.id_article,
            models.association_table.c.stock_se_id == stock_se.id_se
        ).scalar()
        
        # On récupère le prix d'achat actuel (lié à l'article via votre table PrixAchat)
        current_purchase_price = art.prix_achat.prix_achat if art.prix_achat else 0.0
        
        articles_list.append({
            "id_article": art.id_article,  # <--- CRUCIAL : L'ID manquant
            "reference": art.reference,
            "nom_article": art.nom_article,
            "categorie": art.categorie,      # Ajouté
            "emplacement": art.emplacement,  # Ajouté
            "prix_vente": float(art.prix_vente) if art.prix_vente else 0.0, # Ajouté
            "quantite": qty,
            "prix_achat": float(current_purchase_price) # Pour l'affichage initial
        })
        
    return {
        "id_se": stock_se.id_se,
        "numero_se": stock_se.numero_se,
        "fournisseur": stock_se.fournisseur,
        "articles": articles_list
    }

def delete_stock_se_safely(db: Session, id_se: int):
    """
    Supprime un Stock SE, ses détails d'apurement et ses associations d'articles
    uniquement si aucun Bon de Livraison (BL) n'a été émis.
    """
    # 1. Vérifier s'il existe des ventes (Lignes de BL) liées à ce stock
    existe_vente = db.query(models.LigneBL).filter(models.LigneBL.stock_se_id == id_se).first()
    
    if existe_vente:
        raise HTTPException(
            status_code=400, 
            detail="Suppression impossible : ce lot SE a déjà fait l'objet de Bons de Livraison."
        )

    # 2. Récupérer le stock et ses articles associés avant suppression pour remettre les stocks à jour
    stock_se = db.query(models.StockSE).filter(models.StockSE.id_se == id_se).first()
    if not stock_se:
        raise HTTPException(status_code=404, detail="Stock SE introuvable.")

    try:
        # 3. Restituer les quantités aux articles (décrémenter la quantité_disponible générale)
        # On récupère les quantités via la table associative
        associations = db.execute(
            models.association_table.select().where(models.association_table.c.stock_se_id == id_se)
        ).fetchall()

        for assoc in associations:
            # assoc[0] = article_id, assoc[2] = quantite_dans_stock
            db_article = db.query(models.Articles).filter(models.Articles.id_article == assoc.article_id).first()
            if db_article:
                db_article.quantite_disponible -= assoc.quantite_dans_stock

        # 4. Supprimer les détails d'apurement (Relation 1:1)
        db.query(models.Apurement).filter(models.Apurement.id_se == id_se).delete()

        # 5. Supprimer les notifications liées à cet apurement
        # (Si vous avez une table notifications liée à l'id_apurement)
        # db.query(models.Notifications).join(models.Apurement).filter(models.Apurement.id_se == id_se).delete()

        # 6. Supprimer les entrées dans la table associative
        stmt_assoc = delete(models.association_table).where(models.association_table.c.stock_se_id == id_se)
        db.execute(stmt_assoc)

        # 7. Supprimer le Stock SE lui-même
        db.delete(stock_se)

        db.commit()
        return {"status": "success", "message": f"Le lot SE n°{stock_se.numero_se} et ses données liées ont été supprimés."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {str(e)}")
    
    
    #sales_managment recherche avancé reference
    
def search_articles_by_prefix(db: Session, query: str, limit: int = 10):
    """Recherche rapide des références pour l'auto-complétion"""
    return db.query(models.Articles).filter(
        models.Articles.reference.ilike(f"{query}%")
    ).limit(limit).all()
    
def get_article_by_reference(db: Session, reference: str):
    """Récupère un article unique par sa référence exacte"""
    return db.query(models.Articles).filter(models.Articles.reference == reference).first()


###########################################

'''         Prix Achat          '''



def get_prix_achat(db: Session, prix_achat_id: int):
    return db.query(models.PrixAchat).filter(models.PrixAchat.id_prix_achat == prix_achat_id).first()


def create_or_update_prix_achat_by_article_id(db: Session, article_id: int, new_prix_achat: float | None):
    """
    Crée ou met à jour le prix d'achat d'un article en utilisant son ID.
    Si new_prix_achat est None, cela supprime l'entrée.
    """
    db_prix_achat = db.query(models.PrixAchat).filter(models.PrixAchat.article_id == article_id).first()
    
    if new_prix_achat is None: 
        if db_prix_achat:
            db.delete(db_prix_achat)
            db.commit()
            return {"message": "Prix d'achat supprimé avec succès."}
    else:
        if db_prix_achat:
            db_prix_achat.prix_achat = new_prix_achat
            db.commit()
            db.refresh(db_prix_achat)
            return db_prix_achat
        else:
            new_entry = models.PrixAchat(
                article_id=article_id,
                prix_achat=new_prix_achat
            )
            db.add(new_entry)
            db.commit()
            db.refresh(new_entry)
            return new_entry
    return None

def delete_prix_achat(db: Session, prix_achat_id: int):
    db_prix_achat = db.query(models.PrixAchat).filter(models.PrixAchat.id_prix_achat == prix_achat_id).first()
    if db_prix_achat:
        db.delete(db_prix_achat)
        db.commit()
        return {"message": f"Prix d'achat avec l'ID {prix_achat_id} supprimé"}
    return None

def get_all_articles_with_prices(db: Session):
    """
    Récupère tous les articles avec leur prix d'achat, si disponible.
    """
    articles_with_prices = db.query(
        models.Articles,
        models.PrixAchat.prix_achat
    ).outerjoin(models.PrixAchat).all()

    # Formater les résultats dans une liste de dictionnaires
    result = []
    for article, prix_achat in articles_with_prices:
        article_dict = article.__dict__.copy()
        article_dict.pop('_sa_instance_state', None)
        article_dict['prix_achat'] = prix_achat
        result.append(article_dict)
    
    return result
