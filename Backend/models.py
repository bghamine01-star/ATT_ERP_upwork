from sqlalchemy import (Column, Integer, String,Numeric, DECIMAL,Enum, ForeignKey, Date, Text, Float, Boolean, Table, DateTime, Text, UniqueConstraint)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import Index
from datetime import datetime
from sqlalchemy.orm import declarative_base
import enum
from sqlalchemy import func

Base = declarative_base()

association_table = Table(
    'article_stock_association',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id_article'), primary_key=True),
    Column('stock_se_id', Integer, ForeignKey('stock_se.id_se'), primary_key=True),
    Column('quantite_dans_stock', Integer, nullable=False)
)

class Articles(Base):
    __tablename__ = "articles"

    id_article = Column(Integer, primary_key=True, autoincrement=True)
    nom_article = Column(String(255), nullable=False)
    reference = Column(String(255), unique=True, nullable=False)
    prix_vente = Column(DECIMAL(10, 2), nullable=False)
    quantite_disponible = Column(Integer, nullable=False)
    categorie = Column(String(100), nullable=True)
    emplacement = Column(String(100), nullable=True)

    stock_ses = relationship("StockSE", secondary=association_table, back_populates="articles")
    prix_achat = relationship("PrixAchat", back_populates="article", uselist=False)

    __table_args__ = (
        Index("idx_articles_nom_article_gin", "nom_article", postgresql_using="gin", postgresql_ops={"nom_article": "gin_trgm_ops"}),
        Index("idx_articles_reference_gin", "reference", postgresql_using="gin", postgresql_ops={"reference": "gin_trgm_ops"})
    )

class StockSE(Base):
    __tablename__ = "stock_se"

    id_se = Column(Integer, primary_key=True, autoincrement=True)
    numero_se = Column(String, nullable=False)
    date_importation = Column(Date, nullable=False)
    quantite_totale = Column(Integer, nullable=False)
    fournisseur = Column(String(255), nullable=True)
    
    # ATTRIBUT CRUCIAL : permet d'ignorer les stocks clos lors des scans quotidiens
    est_apure = Column(Boolean, default=False)

    apurement_details = relationship("Apurement", back_populates="stock_se", uselist=False)
    articles = relationship("Articles", secondary=association_table, back_populates="stock_ses")
    
class PrixAchat(Base):
    __tablename__ = "prix_achat"
    id_prix_achat = Column(Integer, primary_key=True, autoincrement=True)
    prix_achat = Column(DECIMAL(10, 2), nullable=True)
    article_id = Column(Integer, ForeignKey("articles.id_article", ondelete="CASCADE"), nullable=True)

    article = relationship("Articles", back_populates="prix_achat")

class ClientStatus(enum.Enum):
    Resident = "Resident"
    Non_Resident = "Non_Resident"
    
class Clients(Base):
    __tablename__ = "clients"

    id_client = Column(Integer, primary_key=True, autoincrement=True)
    nom_client = Column(String(255), nullable=False)
    code_client = Column(String(100), unique=True, nullable=False)
    matricule_fiscal = Column(String(100), unique=True, nullable=True)
    adresse = Column(Text, nullable=False)
    statut = Column(Enum(ClientStatus), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    telephone = Column(String(20), nullable=False)
    
class FactureBonLivraison(Base):
    __tablename__ = "facture_bon_livraison"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_facture = Column(Integer, ForeignKey("factures.id_facture", ondelete="CASCADE"), nullable=False)
    id_bl = Column(Integer, ForeignKey("bons_de_livraison.id_bl", ondelete="CASCADE"), nullable=False)

    facture = relationship("Factures", back_populates="bons_livraison_associes")
    bon_livraison = relationship("BonsDeLivraison", back_populates="facture_associee")


class BonsDeLivraison(Base):
    __tablename__ = "bons_de_livraison"

    id_bl = Column(Integer, primary_key=True, autoincrement=True)
    date_bl = Column(Date, nullable=False)
    numero_bl = Column(String(100), unique=True, nullable=False)
    id_client = Column(Integer, ForeignKey("clients.id_client", ondelete="CASCADE"), nullable=False)
    total_a_payer = Column(DECIMAL(10, 2), nullable=False)
    
    facture_associee = relationship("FactureBonLivraison", back_populates="bon_livraison", uselist=False)

    client = relationship("Clients")
    
    lignes = relationship("LigneBL", back_populates="bon_livraison")

class LigneBL(Base):
    __tablename__ = "ligne_bl"

    id_ligne_bl = Column(Integer, primary_key=True, autoincrement=True)
    id_bl = Column(Integer, ForeignKey("bons_de_livraison.id_bl", ondelete="CASCADE"), nullable=False)
    id_article = Column(Integer, ForeignKey("articles.id_article", ondelete="CASCADE"), nullable=False)
    nom_article_archive = Column(String(255))
    categorie_archive = Column(String(100))
    quantite = Column(Integer, nullable=False)
    prix_unitaire = Column(DECIMAL(10, 2), nullable=False)
    prix_total_ligne = Column(DECIMAL(10, 2))
    stock_se_id = Column(Integer, ForeignKey("stock_se.id_se"), nullable=False)
    remise = Column(Numeric(5, 2), default=0.00)  # Pourcentage de remise (ex: 10.50 pour 10.5%)
    
    bon_livraison = relationship("BonsDeLivraison", back_populates="lignes")
    article = relationship("Articles")
    stock_se = relationship("StockSE")
    

class Factures(Base):
    __tablename__ = "factures"

    id_facture = Column(Integer, primary_key=True, autoincrement=True)
    numero_facture = Column(String(50), unique=True, nullable=True)  # Pour usage futur
    date_facture = Column(Date, nullable=False)

    id_client = Column(Integer, ForeignKey("clients.id_client", ondelete="CASCADE"), nullable=False)
    client = relationship("Clients")

    montant_total_euro = Column(DECIMAL(10, 2), nullable=False)
    montant_total_dt = Column(DECIMAL(15, 3), nullable=False)

    remise_pourcentage = Column(DECIMAL(5, 2), nullable=True)  # Ex : 10.00 = 10%
    montant_net_euro = Column(DECIMAL(10, 2), nullable=False)
    montant_net_dt = Column(DECIMAL(15, 3), nullable=False)

    taux_conversion = Column(DECIMAL(10, 4), nullable=False)
    poid_en_kg = Column(DECIMAL(10, 2), nullable=True)

    total_en_lettre_euro = Column(Text, nullable=True)
    total_en_lettre_dt = Column(Text, nullable=True)
    
    numeros_se = Column(Text, nullable=True) 
    incoterm = Column(String(50), nullable=True)

    bons_livraison_associes = relationship(
        "FactureBonLivraison",
        back_populates="facture",
        cascade="all, delete-orphan"
    )


    
class TauxDeChangeMensuel(Base):
    __tablename__ = "taux_de_change_mensuel"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mois = Column(Integer, nullable=False)  # 1 = Janvier, 12 = Décembre
    annee = Column(Integer, nullable=False)
    taux = Column(DECIMAL(10, 4), nullable=False)
    devise = Column(String(10), nullable=False)

    __table_args__ = (
        UniqueConstraint('mois', 'annee', name='unique_mois_annee'),
    )

class Apurement(Base):
    __tablename__ = "apurements"

    id_apurement = Column(Integer, primary_key=True, autoincrement=True)
    id_se = Column(Integer, ForeignKey("stock_se.id_se", ondelete="CASCADE"), nullable=False)
    date_echeance_initiale = Column(Date, nullable=False)
    date_echeance_actuelle = Column(Date, nullable=False)
    statut = Column(String(50), default="En cours") # "En cours", "Apuré", "En retard"
    date_cloture = Column(Date, nullable=True)

    stock_se = relationship("StockSE", back_populates="apurement_details")


class AggregationHistory(Base):
    __tablename__ = "aggregation_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    last_run_date = Column(DateTime, nullable=False, default=datetime.utcnow)

class HistoriqueVentes(Base):
    __tablename__ = 'historique_ventes'
    id = Column(Integer, primary_key=True, index=True)
    id_article = Column(Integer, ForeignKey('articles.id_article'))
    date_vente = Column(Date)
    quantite_vendue = Column(Integer)
    montant_total = Column(Float)
    id_facture = Column(Integer, ForeignKey('factures.id_facture'))
    id_ligne_bl = Column(Integer, ForeignKey('ligne_bl.id_ligne_bl'))
    prix_achat = Column(Float) # <-- NOUVEAU: Ajout du prix d'achat
    
    article = relationship("Articles")
    
class HistoriqueVentesAgregees(Base):
    __tablename__ = 'historique_ventes_agregees'
    
    id = Column(Integer, primary_key=True, index=True)
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    chiffre_affaire = Column(DECIMAL(10, 2), nullable=False)
    marge_brute = Column(DECIMAL(10, 2), nullable=False)
    
    __table_args__ = (UniqueConstraint('annee', 'mois', name='_annee_mois_uc'),)


class RoleEnum(str, enum.Enum):
    gerant = "gerant"
    employe = "employe"
    
    
class Utilisateurs(Base):
    __tablename__ = "utilisateurs"

    id_utilisateur = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(255),unique=True, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    mot_de_passe = Column(Text,unique=True, nullable=False)
    
class PredictionStock(Base):
      __tablename__ = 'prediction_stock'
      id = Column(Integer, primary_key=True, index=True)
      article_id = Column(Integer, ForeignKey('articles.id_article'), nullable=False)
      annee = Column(Integer, nullable=False)
      mois = Column(Integer, nullable=False)
      quantite_predite = Column(Integer, nullable=False)
      date_prediction = Column(Date, nullable=False)
      __table_args__ = (UniqueConstraint('article_id', 'annee', 'mois', name='_article_annee_mois_uc'),)
 
'''
class Apurement(Base):
    __tablename__ = "apurement"
    id_apurement = Column(Integer, primary_key=True, autoincrement=True)
    id_se = Column(Integer, ForeignKey("stock_se.id_se", ondelete="CASCADE"), nullable=False)
    
    date_echeance_initiale = Column(Date, nullable=False)
    date_echeance_actuelle = Column(Date, nullable=False)
    nb_prolongations = Column(Integer, default=0)
    
    
    statut = Column(String(50), nullable=False) # 'En cours', 'Prolongé', 'Apuré', 'Expiré'
    
    est_archive = Column(Boolean, default=False)
    date_archivage = Column(Date, nullable=True)
    annee_archivage = Column(Integer, nullable=True)
    
    stock_se = relationship("StockSE", back_populates="apurement_details")
    notifications = relationship("Notifications", back_populates="apurement")
    
    class Notifications(Base):
    __tablename__ = "notifications"

    id_notification = Column(Integer, primary_key=True, autoincrement=True)
    # Lien vers l'apurement concerné pour savoir de quel lot on parle
    id_apurement = Column(Integer, ForeignKey("apurement.id_apurement", ondelete="CASCADE"), nullable=False)
    
    type_notification = Column(String(100), nullable=False) # 'Alerte 9 mois', 'Alerte 11 mois', etc.
    details = Column(Text, nullable=False)
    statut = Column(String(50), default="Non lu") # 'Non lu', 'Lu', 'Archivé'
    date_notification = Column(Date, nullable=False)

    apurement = relationship("Apurement", back_populates="notifications")
    '''