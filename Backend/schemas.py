from pydantic import BaseModel, Field, EmailStr, ConfigDict, conint, condecimal, validator
from typing import Optional, Annotated
from enum import Enum
from decimal import Decimal, InvalidOperation
from datetime import date
from typing import List, Dict, Annotated
from Backend.models import ClientStatus

# Modèle pour la création d'un client
class ClientCreate(BaseModel):
    # Field(min_length=1) empêche d'envoyer une chaîne vide ""
    nom_client: str = Field(..., min_length=1)
    code_client: str = Field(..., min_length=1)
    matricule_fiscal: Optional[str] = None
    adresse: str = Field(..., min_length=1)
    # En utilisant ClientStatus, Pydantic rejettera "Touriste" avec une 422
    statut: ClientStatus 
    email: EmailStr
    telephone: str = Field(..., min_length=1)

# Modèle pour la réponse (y compris l'ID)
class ClientResponse(ClientCreate):
    id_client: int

    model_config = ConfigDict(from_attributes=True)
        
# Modèle pour la mise à jour d'un client (tous les champs sont optionnels)
class ClientUpdate(BaseModel):
    nom_client: Optional[str] = Field(None, min_length=1)
    code_client: Optional[str] = Field(None, min_length=1)
    matricule_fiscal: Optional[str] = None
    adresse: Optional[str] = Field(None, min_length=1)
    statut: Optional[ClientStatus] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = Field(None, min_length=1)
    
class ClientVenteSchema(BaseModel):
    id_client: int
    nom_client: str
    code_client: str
    adresse: str
    statut: ClientStatus

    class Config:
        from_attributes = True
    
    
    
                    
'''                 USER SCHEMAS            '''
    


class RoleEnum(str, Enum):
    gerant = "gerant"
    employe = "employe"
    
class UtilisateurCreate(BaseModel):
    nom: str
    role: RoleEnum
    mot_de_passe: str

class UtilisateurLogin(BaseModel):
    nom: str
    mot_de_passe: str

class Utilisateur(UtilisateurCreate):
    id_utilisateur: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user_role: Optional[str] = None # Champ ajouté

class TokenData(BaseModel):
    nom: Optional[str] = None
    role: Optional[str] = None
    
    
    '''                 Article   + Apurement              '''
    

'''
class ArticleCreateWithStockSchema(BaseModel):
    nom_article: str
    reference: str
    prix_vente: Decimal
    #quantite_disponible: int
    categorie: str
    #prix_achat: Decimal | None = None
    quantite_dans_stock: int  # Quantité de cet article pour le nouveau stock SE
    prix_achat: Optional[float] = None

class StockSECreateWithArticlesSchema(BaseModel):
    numero_se: int
    date_importation: date
    fournisseur: str
    articles: List[ArticleCreateWithStockSchema]

class StockSESchemaOut(BaseModel):
    id_se: int
    numero_se: int
    date_importation: date
    quantite_totale: int
    fournisseur: str

    class Config:
        from_attributes  = True '''
        
class ArticleCreateWithStockSchema(BaseModel):
    nom_article: str = Field(..., min_length=1, max_length=255, description="Le nom de l'article")
    reference: str = Field(..., min_length=1, max_length=255, description="Référence unique de l'article")
    
    # Validation : Prix doit être > 0 (gt = greater than)
    prix_vente: Decimal = Field(..., gt=0, decimal_places=2)
    
    # Validation : Quantité doit être >= 0 (ge = greater or equal)
    quantite_dans_stock: int = Field(..., ge=0)
    
    categorie: Optional[str] = Field(None, max_length=100)
    emplacement: Optional[str] = Field(None, max_length=100)

    class Config:
        from_attributes = True # Permet de mapper facilement avec SQLAlchemy

class StockSECreateWithArticlesSchema(BaseModel):
    numero_se: str = Field(..., min_length=1)
    date_importation: date
    fournisseur: Optional[str] = Field(None, max_length=255)
    
    # Validation : Au moins un article est requis dans la liste
    articles: List[ArticleCreateWithStockSchema] = Field(..., min_items=1)

    @validator('articles')
    def check_articles_not_empty(cls, v):
        if not v:
            raise ValueError("La liste des articles ne peut pas être vide.")
        return v

    class Config:
        from_attributes = True
    
# Nouveau schéma pour l'update groupé des prix d'achat par le gérant
class BulkPrixAchatUpdate(BaseModel):
    article_id: int
    prix_achat: Decimal = Field(..., ge=0) # On impose un prix > 0

# Si tu veux envoyer tout le lot d'un coup dans une seule requête
class BulkUpdatePayload(BaseModel):
    updates: List[BulkPrixAchatUpdate]

class ArticleMetadataUpdate(BaseModel):
    nom_article: Optional[str] = Field(None, min_length=1)
    prix_vente: Optional[Decimal] = Field(None, ge=0)
    categorie: Optional[str] = None
    emplacement: Optional[str] = None
    fournisseur_stock: Optional[str] = None # Pour mettre à jour le stock lié
    
    class Config:
        from_attributes = True
    
# Nouveau : Détails de l'apurement pour la sortie
class ApurementSchemaOut(BaseModel):
    date_echeance_initiale: date
    date_echeance_actuelle: date
    statut: str

    class Config:
        from_attributes = True

class StockSESchemaOut(BaseModel):
    id_se: int
    numero_se: str
    date_importation: date
    quantite_totale: int
    fournisseur: str
    # Optionnel mais recommandé : inclure l'apurement créé
    apurement_details: Optional[ApurementSchemaOut] = None 

    class Config:
        from_attributes = True

class ArticleOutSchema(BaseModel):
    id_article: int
    nom_article: str
    reference: str
    prix_vente: Decimal
    quantite_disponible: int
    categorie: str
    #prix_achat: Decimal | None = None
    #stocks: List[StockSESchemaOut]

    class Config:
        from_attributes  = True
     

class ArticleWithStockSEInfo(BaseModel):
    numero_se: str
    quantite_dans_stock: int
    date_importation: date

class ArticleWithStockSEDetails(BaseModel):
    id_article: int
    nom_article: str
    reference: str
    prix_vente: Decimal
    quantite_disponible: int
    categorie: str
    emplacement: str
    stock_se_details: List[ArticleWithStockSEInfo]

    class Config:
        from_attributes  = True


class ArticleInStockSE(BaseModel):
    id_article: int
    nom_article: str
    reference: str
    prix_vente: Decimal
    categorie: str
    quantite_dans_stock_se: int  # La quantité spécifique pour ce Stock SE
    emplacement: str
    
class StockSEWithArticles(BaseModel):
    stock_se: StockSESchemaOut
    articles: List[ArticleInStockSE]

    class Config:
        from_attributes  = True 
        
        
        
class ArticleUpdateInStock(BaseModel):
    new_quantite_dans_stock: int = Field(..., gt=0, description="La nouvelle quantité de l'article dans ce Stock SE. Doit être supérieure à 0.")

class ArticleWithOptionalPrixAchat(BaseModel):
    id_article: int
    nom_article: str
    reference: str
    prix_vente: Decimal
    quantite_disponible: int
    categorie: str
    # Clé manquante dans vos schémas actuels et cruciale pour cette route/service
    prix_achat: Optional[float] = None 
    
    class Config:
        from_attributes = True
        # Assurez-vous d'avoir ceci pour la gestion de Decimal
        json_encoders = {Decimal: float}
        
'''         Prix achat          '''

class PrixAchatBase(BaseModel):
    prix_achat: Optional[Decimal] = None
    article_id: Optional[int] = None

class PrixAchatCreate(PrixAchatBase):
    prix_achat: Decimal
    article_id: int

class PrixAchatUpdate(BaseModel):
    # On utilise Decimal pour la précision monétaire
    # Field(gt=0) empêche les prix nuls ou négatifs
    prix_achat: Decimal = Field(..., ge=0, decimal_places=2)

    class Config:
        from_attributes = True

class PrixAchatOut(PrixAchatBase):
    id_prix_achat: int

    class Config:
        from_attributes  = True
        
   
class StockSEOutSchema(BaseModel):
    id_se: int
    numero_se: str
    date_importation: date
    fournisseur: str
    quantite_totale: int

    class Config:
        from_attributes = True     
        
'''         Vente          '''



class ArticleVenduSchema(BaseModel):
    reference: str
    quantite: Annotated[int, Field(gt=0)]
    # Limitation de la remise entre 0 et 100%
    remise: Annotated[float, Field(ge=0.0, le=100.0)] = 0.0

class CreerVenteSchema(BaseModel):
    client_id: int
    date_bl: date
    numero_bl: str
    articles: List[ArticleVenduSchema]
    
class LigneBLSchema(BaseModel):
    id_ligne_bl: int
    id_bl: int
    id_article: int
    quantite: int
    remise: float | None = None
    prix_unitaire: Annotated[Decimal, Field(ge=0)]
    prix_total_ligne: Annotated[Decimal, Field(ge=0)]
    stock_se_id: int

    class Config:
        from_attributes = True
        

        
class ArticleSchema(BaseModel):
    id_article: int
    nom_article: str
    reference: str
    prix_vente: Decimal
    quantite_disponible: int
    categorie: str
    
    class Config:
        from_attributes = True
        # For Decimal to be correctly handled by Pydantic
        json_encoders = {Decimal: float}
        
class ArticleReferenceSchema(BaseModel):
    reference: str
    
    class Config:
        from_attributes = True
        
class BonDeLivraisonSchema(BaseModel):
    id_bl: int
    date_bl: date
    numero_bl: str
    id_client: int
    total_a_payer: Annotated[Decimal, Field(ge=0)]
    lignes: List[LigneBLSchema] = []
    client: "ClientVenteSchema"  # Forward reference pour éviter les erreurs de définition

    class Config:
        from_attributes = True

from Backend.schemas import ClientVenteSchema
# Importation circulaire gérée ici
BonDeLivraisonSchema.update_forward_refs()


class BLFilterParams(BaseModel):
    annee: int
    mois: Optional[int] = None
    client_id: Optional[int] = None
    group_by_client: Optional[bool] = False


class BLResponseItem(BaseModel):
    id_bl: int  # Ajouté pour faciliter la suppression
    numero_bl: str
    date_bl: date
    total_a_payer: float
    client: str
    est_facture: bool # Nouveau champ

# Groupement par nom du client
BLGroupedResponse = Dict[str, List[BLResponseItem]]


'''        Facture          '''

class TauxRequest(BaseModel):
    mois: int
    annee: int
    taux: Decimal = Field(..., ge=Decimal('2.5'), le=Decimal('4.5'))
    devise: str = "DT"  # Devise par défaut, peut être modifié si nécessaire

    @validator('taux', pre=True)
    def format_taux(cls, value):
        try:
            taux_decimal = Decimal(value)
            return taux_decimal.quantize(Decimal('0.000'))
        except (TypeError, InvalidOperation):
            raise ValueError("Le taux doit être un nombre décimal.")
        
class TauxUpdateRequest(BaseModel):
    mois: int
    annee: int
    nouveau_taux: Decimal = Field(..., gt=Decimal('2.5'), lt=Decimal('4.5'))

    @validator('nouveau_taux', pre=True)
    def format_nouveau_taux(cls, value):
        try:
            taux_decimal = Decimal(value)
            return taux_decimal.quantize(Decimal('0.000'))
        except (TypeError, InvalidOperation):
            raise ValueError("Le nouveau taux doit être un nombre décimal.")
        
class FactureResponse(BaseModel):
    id_facture: int
    numero_facture: Optional[str]
    date_facture: date
    client_nom: str
    montant_net_dt: float
    
# Backend/schemas.py
class FactureGenerationRequest(BaseModel):
    id_client: int
    mois: int
    annee: int
    numero_facture_manuel: str  # Saisie manuelle par l'utilisateur
    remise_globale_facture: Optional[Decimal] = Decimal('0.00') # Remise en % sur le total
    poids_total: float
    incoterm: Optional[str] = "fob"
    
'''  APUREMENT  '''


from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from decimal import Decimal

class ArticleApurementSchema(BaseModel):
    reference: str
    nom_article: str
    quantite_initiale: int
    quantite_vendue: int
    quantite_restante: int

class FactureAssocieeSchema(BaseModel):
    numero_facture: str
    date_facture: date
    article_reference: str
    quantite_art_concerne: int

class ApurementDetailResponse(BaseModel):
    numero_se: str
    date_importation: date
    date_echeance: date
    jours_restants: int
    est_apure: bool
    articles: List[ArticleApurementSchema]
    factures: List[FactureAssocieeSchema]

    class Config:
        from_attributes = True
        
'''
class ArticleBase(BaseModel):
    id_article: int
    nom_article: str
    reference: str

class StockSEBase(BaseModel):
    id_se: int
    numero_se: int
    date_importation: date

class BonDeLivraisonBase(BaseModel):
    id_bl: int
    numero_bl: str
    date_bl: date

class LigneBLBase(BaseModel):
    id_ligne_bl: int
    quantite: int
    prix_unitaire: float
    prix_total_ligne: Optional[float]
    article: ArticleBase
    bon_livraison: BonDeLivraisonBase
    stock_se_id: int

class ApurementBase(BaseModel):
    id_apurement: int
    id_se: int # Modification : Stocker uniquement le numero_se
    statut: str
    date_echeance: date # Ajout de la date d'échéance
    date_de_declaration: Optional[date] # Ajout de la date de déclaration

class ArticleVendu(ArticleBase):
    id_article: int
    nom_article: str
    reference: str
    quantite_vendue: int
    bons_de_livraison: List[BonDeLivraisonBase]

class ArticleRestant(ArticleBase):
    id_article: int
    nom_article: str
    reference: str
    quantite_restante: int

class StockApureResponse(BaseModel):
    stock_se: StockSEBase
    articles_vendus: List[ArticleVendu]
    articles_restants: List[ArticleRestant]
    date_echeance: date # Ajout de la date d'échéance pour l'affichage

class NotificationResponse(BaseModel):
    numero_se: int
    date_echeance: date
    articles: List[ArticleBase] # Ajout de la liste des articles concernés

'''
class ArticleWithPriceOut(BaseModel):
    id_article: int
    nom_article: str
    reference: str
    prix_vente: float
    quantite_disponible: int
    categorie: str
    prix_achat: Optional[float] # Le prix d'achat est maintenant inclus
    
    class Config:
        from_attributes = True
   
  
    class Config:
        from_attributes = True
        
                
    
    
        '''        Dashboard          ''' 

class TauxDeChangeMensuelBase(BaseModel):
    mois: int
    annee: int
    taux: Decimal

class TauxDeChangeMensuelCreate(TauxDeChangeMensuelBase):
    pass

class TauxDeChangeMensuel(TauxDeChangeMensuelBase):
    id_taux: int

    class Config:
        from_attributes = True

class HistoriqueVentesAgregeesBase(BaseModel):
    annee: int
    mois: int
    chiffre_affaire: Decimal
    marge_brute: Decimal

class HistoriqueVentesAgregees(HistoriqueVentesAgregeesBase):
    id_historique: int

    class Config:
        from_attributes = True

class YearlyRevenue(BaseModel):
    annee: int
    total_revenue: float
    total_gross_margin: float
    average_cart: float

class MonthlyRevenue(BaseModel):
    month: int
    revenue: float
    gross_margin: float
    
class ClientProfitability(BaseModel):
    id_client: int
    client_name: str
    total_gross_margin: float

class ClientMonthlyProfitability(BaseModel):
    client_name: str
    month: int
    year: int
    gross_margin: float