from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from Backend.models import StockSE, Utilisateurs, Articles
from Backend.database import get_db
from Backend.schemas import *
from Backend.services import article_service
from Backend.routers import user_routes

router = APIRouter(tags=["articles"])

@router.get("/articles/search_v2")
def search_articles(
    reference: Optional[str] = Query(None),
    designation: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    #current_user = Depends(get_current_user) # Optionnel: vérifie que l'user est loggé
):
    """
    Endpoint de recherche filtrée : appelle le service métier.
    """
    return article_service.search_articles_optimized(
        db=db, 
        reference=reference, 
        designation=designation
    )


@router.get("/articles/search-refs")
def search_refs(q: str = "", db: Session = Depends(get_db)):
    articles = article_service.search_articles_by_prefix(db, q)
    return [{"reference": a.reference, "designation": a.nom_article, "prix": float(a.prix_vente), "dispo": a.quantite_disponible} for a in articles]

@router.get("/articles/ref/{ref}")
def read_article_by_ref(ref: str, db: Session = Depends(get_db)):
    article = article_service.get_article_by_reference(db, ref)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    return {
        "id_article": article.id_article,
        "reference": article.reference,
        "nom_article": article.nom_article,
        "prix_vente": float(article.prix_vente),
        "quantite_disponible": article.quantite_disponible
    }

@router.get("/articles/refv2/{ref}")
def read_article_by_ref(ref: str, db: Session = Depends(get_db)):
    article = article_service.get_article_by_reference(db, ref)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    return {
        "id_article": article.id_article,
        "reference": article.reference,
        "nom_article": article.nom_article,
        "categorie": article.categorie,    
        "emplacement": article.emplacement,
        "prix_vente": float(article.prix_vente),
        "quantite_disponible": article.quantite_disponible
    }

import csv
import io
from fastapi.responses import StreamingResponse
from datetime import datetime

@router.get("/articles/export/csv")
def export_articles_csv(
    db: Session = Depends(get_db), 
    current_user: Utilisateurs = Depends(user_routes.get_current_user) # On récupère l'user
):
    """
    Exporte le stock en CSV avec restriction sur le prix d'achat selon le rôle.
    """
    articles_data = article_service.get_all_articles_with_prices(db)
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # 1. Définir les en-têtes selon le rôle
    headers = ["Reference", "Designation", "Categorie", "Emplacement", "Prix Vente", "Stock"]
    is_gerant = current_user.role == "gerant"
    
    if is_gerant:
        headers.append("Prix Achat")
    
    writer.writerow(headers)
    
    # 2. Remplir les lignes
    for art in articles_data:
        row = [
            art["reference"],
            art["nom_article"],
            art["categorie"],
            art["emplacement"],
            art.get("prix_vente", 0),
            art.get("quantite_disponible", 0)
        ]
        
        # On n'ajoute la donnée que si l'utilisateur est gérant
        if is_gerant:
            row.append(art.get("prix_achat", 0) if art.get("prix_achat") else 0)
            
        writer.writerow(row)
    
    output.seek(0)
    filename = f"export_stock_{datetime.now().strftime('%d_%m_%Y')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    
    
@router.get("/stock_se/details/{numero_se}")
def get_details_by_numero(numero_se: str, db: Session = Depends(get_db)):
    details = article_service.get_stock_details_by_numero(db, numero_se)
    if not details:
        raise HTTPException(status_code=404, detail="Numéro SE introuvable")
    return details


@router.post("/stock_se/", response_model=StockSESchemaOut)
def create_stock_se_with_articles_route(stock_se_data: StockSECreateWithArticlesSchema, db: Session = Depends(get_db)):
    try:
        db_stock_se_numero = db.query(StockSE).filter(StockSE.numero_se == stock_se_data.numero_se).first()
        if db_stock_se_numero:
            raise HTTPException(status_code=400, detail="Numero SE already registered")
        return article_service.create_stock_se_with_articles(db=db, stock_se_data=stock_se_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reference/{reference}/stocks", response_model=ArticleWithStockSEDetails)
def read_article_by_reference_with_stocks(reference: str, db: Session = Depends(get_db)):
    db_article_with_stocks = article_service.get_article_by_reference_with_stock_info(db, reference=reference)
    if db_article_with_stocks is None:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return db_article_with_stocks

@router.get("/stock_se/all", response_model=List[StockSEOutSchema])
def read_all_stock_ses(db: Session = Depends(get_db)):
    """
    Récupère la liste de tous les stocks SE existants.
    """
    stocks = article_service.get_all_stock_ses(db)
    return stocks

@router.get("/stock_se/{numero_se}", response_model=StockSEWithArticles)
def read_articles_by_stock_se(numero_se: int, db: Session = Depends(get_db)):
    stock_se_with_articles = article_service.get_articles_by_stock_se_with_info(db, numero_se=numero_se)
    if stock_se_with_articles is None:
        raise HTTPException(status_code=404, detail=f"Stock SE avec le numéro {numero_se} non trouvé ou ne contient aucun article")
    return stock_se_with_articles

@router.delete("/stock-se/{id_se}")
def delete_stock(id_se: int, db: Session = Depends(get_db)):
    return article_service.delete_stock_se_safely(db, id_se)
    
     
@router.put("/{numero_se}/articles/{article_reference}")
def update_article_in_stock_se_route(
    numero_se: int,
    article_reference: str,
    article_update: ArticleUpdateInStock, # Utilise le schéma Pydantic pour la validation
    db: Session = Depends(get_db)
):
    """
    Met à jour la quantité d'un article spécifique dans un Stock SE donné.

    - **numero_se**: Le numéro du Stock SE (dans le chemin de l'URL).
    - **article_reference**: La référence de l'article à modifier (dans le chemin de l'URL).
    - **new_quantite_dans_stock**: La nouvelle quantité de l'article dans ce Stock SE (dans le corps de la requête).
    """
    try:
        updated_data = article_service.update_article_in_stock_se(
            db=db,
            numero_se=numero_se,
            article_reference=article_reference,
            new_quantite_dans_stock=article_update.new_quantite_dans_stock
        )
        return updated_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Gérer d'autres erreurs inattendues
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur inattendue est survenue: {e}"
        )


'''         Prix achat          '''


@router.get("/prix_achat/{prix_achat_id}", response_model=PrixAchatOut, dependencies=[Depends(user_routes.gerant_only)])
def read_prix_achat(prix_achat_id: int, db: Session = Depends(get_db)):
    db_prix_achat = article_service.get_prix_achat(db, prix_achat_id)
    if not db_prix_achat:
        raise HTTPException(status_code=404, detail="Prix d'achat non trouvé")
    return db_prix_achat



@router.delete("/prix_achat/{prix_achat_id}", response_model=None, dependencies=[Depends(user_routes.gerant_only)])
def delete_prix_achat(prix_achat_id: int, db: Session = Depends(get_db)):
    result = article_service.delete_prix_achat(db, prix_achat_id)
    if not result:
        raise HTTPException(status_code=404, detail="Prix d'achat non trouvé")
    return result



@router.get("/articles/all_with_prices", response_model=list[ArticleWithPriceOut])
def get_all_articles_with_prices_route(db: Session = Depends(get_db)):
    return article_service.get_all_articles_with_prices(db)

# Backend/routers/articles.py
'''

@router.patch("/stock_se/{id_se}/update_prices")
def update_purchase_prices(id_se: int, prices_data: dict, db: Session = Depends(get_db)):
    """
    Met à jour les prix d'achat dans la table d'association
    prices_data est un dictionnaire: {"REF_ART_1": 150.5, "REF_ART_2": 200.0}
    """
    # 1. On cherche le lot SE
    stock_se = db.query(models.StockSE).filter(models.StockSE.id_se == id_se).first()
    if not stock_se:
        raise HTTPException(status_code=404, detail="Lot SE non trouvé")

    # 2. On boucle sur les articles envoyés
    for ref, new_price in prices_data.items():
        # On cherche l'article par sa référence
        article = db.query(models.Article).filter(models.Article.reference == ref).first()
        if article:
            # On met à jour le champ 'prix_achat' dans la table d'association
            db.execute(
                models.association_table.update()
                .where(models.association_table.c.stock_se_id == id_se)
                .where(models.association_table.c.article_id == article.id_article)
                .values(prix_achat=new_price)
            )
    
    db.commit()
    return {"message": "Prix d'achat mis à jour avec succès"} '''
    
@router.put("/articles/bulk/prix_achat", dependencies=[Depends(user_routes.gerant_only)])
def update_bulk_articles_prices(
    updates: List[BulkPrixAchatUpdate], 
    db: Session = Depends(get_db)
):
    """
    Met à jour un lot de prix d'achat en une seule transaction.
    Utilise la méthode optimisée avec un seul commit.
    """
    return article_service.update_bulk_prix_achat(db, updates)

@router.put("/articles/{article_id}/prix_achat", 
            dependencies=[Depends(user_routes.gerant_only)],
            response_model=PrixAchatUpdate) # Optionnel: pour valider la sortie
def update_prix_achat_for_article(
    article_id: int, 
    prix_achat_update: PrixAchatUpdate, 
    db: Session = Depends(get_db)
):
    """
    Met à jour ou crée le prix d'achat d'un article via son ID.
    Cette route est utilisée par l'InventoryManager et le module d'Apurement.
    """
    # Appel au service (on passe article_id et la valeur float/decimal directement)
    result = article_service.create_or_update_prix_achat_by_article_id(
        db, 
        article_id, 
        prix_achat_update.prix_achat
    )
    
    if result is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Article avec l'ID {article_id} introuvable."
        )
        
    return result



@router.get("/articles/search", response_model=list[ArticleWithOptionalPrixAchat]) # Le type de retour doit correspondre à votre schéma de sortie pour les articles
def search_articles(query: str, db: Session = Depends(get_db)):
    """
    Recherche des articles par référence ou nom d'article.
    """
    if not query:
        # Retourner une erreur ou une liste vide si la requête est vide, selon la préférence
        raise HTTPException(status_code=400, detail="Le terme de recherche ne peut être vide.")
        
    articles = article_service.search_articles_by_ref_or_name(db, query)
    
    if not articles:
        # Optionnel: retourner une 404 si rien n'est trouvé
        return []

    return articles

@router.put("/prix_achat/bulk-update", dependencies=[Depends(user_routes.gerant_only)])
def bulk_update_prix_achat_route(updates: List[BulkPrixAchatUpdate], db: Session = Depends(get_db)):
    """
    Interface spéciale Gérant : permet de mettre à jour plusieurs prix d'achat d'un coup.
    """
    return article_service.update_bulk_prix_achat(db, updates)

@router.patch("/stock/{numero_se}/article/{article_reference}/safe-update")
def safe_update_article_route(
    numero_se: str, 
    article_reference: str, 
    update_data: ArticleMetadataUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update sécurisé : ne permet de modifier que le nom, prix, catégorie, 
    emplacement et fournisseur. N'affecte pas les quantités ni l'apurement.
    """
    try:
        return article_service.update_article_metadata_safe(
            db, numero_se, article_reference, update_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
