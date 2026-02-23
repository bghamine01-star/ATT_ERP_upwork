from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import requests
from datetime import datetime
from config import API_BASE_URL

class BLConsultation(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.api_url = API_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- HEADER ---
        title = QLabel("Consultation des Bons de Livraison")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        layout.addWidget(title)

        # --- BARRE DE FILTRES ---
        filter_card = QFrame()
        filter_card.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #E5E7EB;")
        filter_card.setFixedHeight(80)
        filter_layout = QHBoxLayout(filter_card)
        
        self.combo_client = QComboBox()
        self.combo_client.setMinimumWidth(200)
        self.load_clients()

        self.combo_mois = QComboBox()
        self.combo_mois.addItems(["Tous les mois", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                                  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
        self.combo_mois.setCurrentIndex(datetime.now().month)
        
                # NOUVEAU : Sélecteur d'Année
        self.spin_annee = QSpinBox()
        self.spin_annee.setRange(2000, 2100)
        self.spin_annee.setValue(datetime.now().year) # Par défaut 2026
        self.spin_annee.setMinimumWidth(80)

        btn_search = QPushButton("🔍 Rechercher")
        btn_search.setStyleSheet("background-color: #111827; color: white; padding: 10px 20px; font-weight: bold; border-radius: 6px;")
        btn_search.clicked.connect(self.fetch_bl_data)

        filter_layout.addWidget(QLabel("<b>Client :</b>"))
        filter_layout.addWidget(self.combo_client)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(QLabel("<b>Mois :</b>"))
        filter_layout.addWidget(self.combo_mois)
        filter_layout.addSpacing(10)
        filter_layout.addWidget(QLabel("<b>Année :</b>"))
        filter_layout.addWidget(self.spin_annee)
        filter_layout.addStretch()
        filter_layout.addWidget(btn_search)
        layout.addWidget(filter_card)

        # --- TABLEAU DES RÉSULTATS ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Numéro BL", "Client", "Montant Total", "Statut", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #E5E7EB; border-radius: 8px; gridline-color: #F3F4F6; }
            QHeaderView::section { background-color: #F9FAFB; padding: 12px; border: none; font-weight: bold; border-bottom: 1px solid #E5E7EB; }
        """)
        layout.addWidget(self.table)

        self.fetch_bl_data() # Chargement initial

    def load_clients(self):
        try:
            res = requests.get(f"{self.api_url}/clients/", headers=self.headers)
            if res.status_code == 200:
                self.combo_client.addItem("Tous les clients", None)
                for c in res.json():
                    self.combo_client.addItem(c['nom_client'], c['id_client'])
        except: pass

    def fetch_bl_data(self):
        annee = self.spin_annee.value()
        mois = self.combo_mois.currentIndex() if self.combo_mois.currentIndex() > 0 else None
        client_id = self.combo_client.currentData()

        params = {"annee": annee}
        if mois: params["mois"] = mois
        if client_id: params["client_id"] = client_id

        try:
            res = requests.get(f"{self.api_url}/ventes/bons-de-livraison/filter", params=params, headers=self.headers)
            if res.status_code == 200:
                self.update_table(res.json())
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur réseau : {e}")

    def update_table(self, data):
        self.table.setRowCount(0)
        # On récupère le mois sélectionné dans le combo pour la comparaison
        selected_month_index = self.combo_mois.currentIndex() 
        
        for bl in data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Conversion de la date (Assurez-vous que le format correspond au backend)
            # Si le backend envoie "2026-01-13", on utilise %Y-%m-%d
            try:
                date_dt = datetime.strptime(bl['date_bl'], "%Y-%m-%d")
            except:
                # Au cas où le format inclurait l'heure
                date_dt = datetime.fromisoformat(bl['date_bl'])
            
            self.table.setItem(row, 0, QTableWidgetItem(date_dt.strftime("%d/%m/%Y")))
            self.table.setItem(row, 1, QTableWidgetItem(bl['numero_bl']))
            self.table.setItem(row, 2, QTableWidgetItem(bl['client']))
            self.table.setItem(row, 3, QTableWidgetItem(f"{bl['total_a_payer']:.2f} EUR"))

            # --- STATUT ---
            status_label = "Facturé" if bl['est_facture'] else "En attente"
            status_item = QTableWidgetItem(status_label)
            status_item.setForeground(QColor("#059669") if bl['est_facture'] else QColor("#D97706"))
            self.table.setItem(row, 4, status_item)

            # --- ACTIONS ---
            actions_container = QWidget()
            actions_layout = QHBoxLayout(actions_container)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(8)

            # Bouton PDF (Toujours visible)
            btn_pdf = QPushButton("📄 PDF")
            btn_pdf.clicked.connect(lambda _, n=bl['numero_bl']: self.open_pdf(n))
            actions_layout.addWidget(btn_pdf)
            
            # NOUVEAU : Bouton CSV
            btn_csv = QPushButton("📊 CSV")
            btn_csv.setStyleSheet("background-color: #059669; color: white; font-weight: bold; border-radius: 4px;")
            btn_csv.clicked.connect(lambda _, i=bl['id_bl'], n=bl['numero_bl']: self.download_bl_csv(i, n))
            actions_layout.addWidget(btn_csv)

            # --- LOGIQUE DU BOUTON SUPPRIMER ---
            # Condition : Non facturé ET (C'est le mois en cours OU on a filtré spécifiquement ce mois)
            if not bl.get('est_facture', False):
                btn_del = QPushButton("🗑️")
                btn_del.setToolTip("Supprimer et restaurer le stock")
                btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_del.setStyleSheet("""
                    QPushButton { color: #EF4444; border: none; font-size: 18px; font-weight: bold; }
                    QPushButton:hover { background-color: #FEE2E2; border-radius: 4px; }
                """)
                # On utilise bl['id_bl'] car votre service backend attend l'ID numérique
                btn_del.clicked.connect(lambda _, i=bl['id_bl']: self.confirm_delete(i))
                actions_layout.addWidget(btn_del)
            else:
                # Optionnel : Ajouter un label "Verrouillé" ou laisser vide
                actions_layout.addStretch()

            self.table.setCellWidget(row, 5, actions_container)

    def open_pdf(self, numero_bl):
        import webbrowser
        webbrowser.open(f"{self.api_url}/ventes/bons-de-livraison/{numero_bl}/pdf")
        
    def download_bl_csv(self, id_bl, numero_bl):
        try:
            res = requests.get(f"{self.api_url}/ventes/bons-de-livraison/{numero_bl}/csv", headers=self.headers)
            if res.status_code == 200:
                clean_num = str(numero_bl).replace("/", "_").replace("\\", "_")
                path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder le BL", f"BL_{clean_num}.csv", "CSV Files (*.csv)")
                if path:
                    try:
                        with open(path, 'wb') as f:
                            f.write(res.content)
                        QMessageBox.information(self, "Succès", "Fichier CSV du BL enregistré avec succès.")
                    except PermissionError:
                        QMessageBox.critical(self, "Erreur", "Fermez le fichier s'il est ouvert dans Excel.")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de générer le CSV.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur réseau : {e}")

    def confirm_delete(self, id_bl):
        rep = QMessageBox.question(self, "Confirmation", "Voulez-vous supprimer ce BL ?\nCette action restaurera les stocks.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rep == QMessageBox.StandardButton.Yes:
            res = requests.delete(f"{self.api_url}/ventes/bons-de-livraison/{id_bl}", headers=self.headers)
            if res.status_code == 200:
                self.fetch_bl_data()