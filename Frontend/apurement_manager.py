import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from config import API_BASE_URL

class ApurementManager(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.api_url = API_BASE_URL
        self.current_data = None  # Stockage des données pour le filtrage local
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- HEADER & RECHERCHE ---
        header_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Entrez le numéro de Stock SE (ex: SE-2024-001)...")
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet("border: 1px solid #E5E7EB; border-radius: 8px; padding: 5px 15px;")
        
        btn_search = QPushButton("🔍 Rechercher")
        btn_search.setFixedHeight(40)
        btn_search.setStyleSheet("background-color: #6366F1; color: white; border-radius: 8px; padding: 0 20px; font-weight: bold;")
        btn_search.clicked.connect(self.rechercher_se)
        
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(btn_search)
        layout.addLayout(header_layout)

        # --- CARTE INFO ECHEANCE ---
        self.info_card = QFrame()
        self.info_card.setStyleSheet("background-color: white; border: 1px solid #E5E7EB; border-radius: 12px;")
        self.info_card.setFixedHeight(120)
        self.info_card_layout = QHBoxLayout(self.info_card)
        
        self.lbl_echeance = QLabel("Recherchez un SE pour voir les détails")
        self.lbl_echeance.setStyleSheet("font-size: 16px; color: #4B5563;")
        self.btn_cloturer = QPushButton("Clôturer l'Apurement")
        self.btn_cloturer.setFixedSize(180, 40)
        self.btn_cloturer.setStyleSheet("background-color: #10B981; color: white; border-radius: 8px; font-weight: bold;")
        self.btn_cloturer.setVisible(False)
        self.btn_cloturer.clicked.connect(self.cloturer_dossier)

        self.info_card_layout.addWidget(self.lbl_echeance)
        self.info_card_layout.addStretch()
        self.info_card_layout.addWidget(self.btn_cloturer)
        layout.addWidget(self.info_card)

        # --- TABLES (Articles et Factures) ---
        tables_layout = QHBoxLayout()
        
        # Table Articles
        v_box_art = QVBoxLayout()
        v_box_art.addWidget(QLabel("<b>📦 État des Articles du SE (Sélectionnez pour filtrer)</b>"))
        self.table_articles = self.create_styled_table(["Référence", "Importé", "Vendu", "Restant"])
        # CONNECTION DU SIGNAL DE SELECTION
        self.table_articles.itemSelectionChanged.connect(self.filtrer_factures_par_article)
        v_box_art.addWidget(self.table_articles)
        
        # Table Factures
        v_box_fact = QVBoxLayout()
        v_box_fact.addWidget(QLabel("<b>📄 Factures liées (Ventes)</b>"))
        self.table_factures = self.create_styled_table(["Facture", "Date", "Réf. Article", "Qté"])
        v_box_fact.addWidget(self.table_factures)
        
        tables_layout.addLayout(v_box_art, 3) 
        tables_layout.addLayout(v_box_fact, 2)
        layout.addLayout(tables_layout)

    def create_styled_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setStyleSheet("background-color: white; border: 1px solid #E5E7EB; border-radius: 8px;")
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

    def rechercher_se(self):
        numero_se = self.search_input.text().strip()
        if not numero_se: return

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_url}/apurement/recherche/{numero_se}", headers=headers)
            
            if response.status_code == 200:
                self.current_data = response.json() # On garde tout en mémoire
                self.update_ui_with_data(self.current_data)
            else:
                QMessageBox.warning(self, "Erreur", "Numéro SE non trouvé ou erreur serveur.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Connexion impossible : {str(e)}")

    def update_ui_with_data(self, data):
        # Désactiver temporairement les signaux pour éviter un filtrage pendant le remplissage
        self.table_articles.blockSignals(True)
        
        # Mise à jour du bandeau d'infos
        color = "#EF4444" if data['jours_restants'] < 30 else "#F59E0B" if data['jours_restants'] < 90 else "#10B981"
        status_text = "APURÉ" if data['est_apure'] else f"{data['jours_restants']} jours restants"
        
        self.lbl_echeance.setText(
            f"<b>Stock SE: {data['numero_se']}</b><br>"
            f"Échéance: {data['date_echeance']} | <span style='color: {color};'>{status_text}</span>"
        )
        self.btn_cloturer.setVisible(not data['est_apure'])

        # Remplissage Table Articles
        self.table_articles.setRowCount(0)
        for art in data['articles']:
            row = self.table_articles.rowCount()
            self.table_articles.insertRow(row)
            self.table_articles.setItem(row, 0, QTableWidgetItem(art['reference']))
            self.table_articles.setItem(row, 1, QTableWidgetItem(str(art['quantite_initiale'])))
            self.table_articles.setItem(row, 2, QTableWidgetItem(str(art['quantite_vendue'])))
            
            restant_item = QTableWidgetItem(str(art['quantite_restante']))
            if art['quantite_restante'] > 0: restant_item.setForeground(QColor("#6366F1"))
            self.table_articles.setItem(row, 3, restant_item)

        # Remplissage initial de la Table Factures (Toutes)
        self.remplir_table_factures(data['factures'])
        
        self.table_articles.blockSignals(False)

    def remplir_table_factures(self, factures_list):
        """Méthode utilitaire pour remplir la table des factures selon une liste donnée"""
        self.table_factures.setRowCount(0)
        for f in factures_list:
            row = self.table_factures.rowCount()
            self.table_factures.insertRow(row)
            self.table_factures.setItem(row, 0, QTableWidgetItem(f['numero_facture']))
            self.table_factures.setItem(row, 1, QTableWidgetItem(str(f['date_facture'])))
            self.table_factures.setItem(row, 2, QTableWidgetItem(f['article_reference']))
            self.table_factures.setItem(row, 3, QTableWidgetItem(str(f['quantite_art_concerne'])))

    def filtrer_factures_par_article(self):
        """Filtre localement les factures sans appel API"""
        if not self.current_data:
            return

        selected_items = self.table_articles.selectedItems()
        if not selected_items:
            # Si rien n'est sélectionné, on réaffiche tout
            self.remplir_table_factures(self.current_data['factures'])
            return

        # La référence est dans la première colonne (index 0) de la ligne sélectionnée
        row_index = selected_items[0].row()
        reference_selectionnee = self.table_articles.item(row_index, 0).text()

        # Filtrage de la liste stockée en mémoire
        factures_filtrees = [
            f for f in self.current_data['factures'] 
            if f['article_reference'] == reference_selectionnee
        ]
        
        self.remplir_table_factures(factures_filtrees)

    def cloturer_dossier(self):
        numero_se = self.search_input.text().strip()
        reply = QMessageBox.question(self, "Confirmation", f"Voulez-vous clôturer l'apurement du SE {numero_se} ?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            headers = {"Authorization": f"Bearer {self.token}"}
            res = requests.post(f"{self.api_url}/apurement/cloturer/{numero_se}", headers=headers)
            if res.status_code == 200:
                QMessageBox.information(self, "Succès", "Dossier clôturé avec succès.")
                self.rechercher_se()
