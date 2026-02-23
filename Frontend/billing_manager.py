from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QLineEdit, QDoubleSpinBox, QMessageBox, QDialog, 
    QFormLayout, QTabWidget, QFileDialog, QSpinBox
)
from PyQt6.QtCore import Qt
import requests
from datetime import datetime, date
import calendar
from config import API_BASE_URL

class BillingManager(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.api_url = API_BASE_URL
        self.selected_client_id = None
        self.init_ui()

    def init_ui(self):
        """Structure principale avec Onglets"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        # --- TITRE PRINCIPAL ---
        self.header = QLabel("Gestion de la Facturation Mensuelle")
        self.header.setStyleSheet("font-size: 26px; font-weight: bold; color: #1F2937;")
        self.main_layout.addWidget(self.header)

        # --- SYSTÈME D'ONGLETS ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E5E7EB; background: white; border-radius: 8px; }
            QTabBar::tab { 
                padding: 12px 25px; font-weight: bold; font-size: 14px; 
                background: #F3F4F6; border: 1px solid #E5E7EB;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { background: white; color: #6366F1; border-bottom: 2px solid #6366F1; }
            QTabBar::tab:hover { background: #E5E7EB; }
        """)

        # 1. Onglet Génération
        self.tab_gen = QWidget()
        self.setup_generation_ui()
        self.tabs.addTab(self.tab_gen, "🆕 Nouvelle Facture")

        # 2. Onglet Historique
        self.tab_hist = QWidget()
        self.setup_history_ui()
        self.tabs.addTab(self.tab_hist, "📂 Historique & PDF")

        self.main_layout.addWidget(self.tabs)

    def setup_generation_ui(self):
        """Interface de génération"""
        layout = QVBoxLayout(self.tab_gen)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Barre d'outils (Taux de change)
        top_bar = QHBoxLayout()
        self.btn_taux = QPushButton("💰 Configurer Taux de Change")
        self.btn_taux.setStyleSheet("""
            QPushButton { background-color: #F3F4F6; border: 1px solid #D1D5DB; padding: 8px 15px; border-radius: 5px; font-weight: 500; }
            QPushButton:hover { background-color: #E5E7EB; }
        """)
        self.btn_taux.clicked.connect(self.ouvrir_dialog_taux)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_taux)
        layout.addLayout(top_bar)

        # Filtres Génération
        filter_card = QFrame()
        filter_card.setStyleSheet("background-color: #F9FAFB; border-radius: 10px; border: 1px solid #E5E7EB;")
        f_layout = QHBoxLayout(filter_card)
        
        self.combo_mois = QComboBox()
        self.combo_mois.addItems(["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
        self.combo_mois.setCurrentIndex(date.today().month - 1)
        
                        # NOUVEAU : Sélecteur d'Année
        self.combo_annee = QSpinBox()
        self.combo_annee.setRange(2000, 2100)
        self.combo_annee.setValue(datetime.now().year) # Par défaut 2026
        self.combo_annee.setMinimumWidth(80)

        btn_search = QPushButton("🔍 Lister Clients à Facturer")
        btn_search.setStyleSheet("background-color: #6366F1; color: white; padding: 10px 20px; font-weight: bold; border-radius: 6px;")
        btn_search.clicked.connect(self.load_clients_a_facturer)

        f_layout.addWidget(QLabel("Mois :"))
        f_layout.addWidget(self.combo_mois)
        f_layout.addWidget(QLabel("Année :"))
        f_layout.addWidget(self.combo_annee)
        f_layout.addStretch()
        f_layout.addWidget(btn_search)
        layout.addWidget(filter_card)

        # Table Clients
        self.table_clients = QTableWidget()
        self.table_clients.setColumnCount(4)
        self.table_clients.setHorizontalHeaderLabels(["Client", "Code", "Statut", "Action"])
        self.table_clients.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_clients.setStyleSheet("QTableWidget { border-radius: 8px; border: 1px solid #E5E7EB; }")
        layout.addWidget(self.table_clients)

        # Panel de saisie Facture
        self.invoice_panel = QFrame()
        self.invoice_panel.setVisible(False)
        self.invoice_panel.setStyleSheet("background-color: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 10px; padding: 15px;")
        p_layout = QHBoxLayout(self.invoice_panel)
        
        self.input_num_fact = QLineEdit()
        self.input_num_fact.setPlaceholderText("N° de Facture (ex: 2025/001)")
        
        self.spin_remise = QDoubleSpinBox()
        self.spin_remise.setSuffix(" %")
        self.spin_remise.setRange(0, 100)
        
        self.input_incoterm = QComboBox()
        self.input_incoterm.addItems(["Ex-Works", "FOB", "CIF", "DDP", "CFR"])
        self.input_incoterm.setEditable(True) # Permet de saisir un incoterm personnalisé

        self.spin_poids = QDoubleSpinBox()
        self.spin_poids.setSuffix(" KG")
        self.spin_poids.setRange(0, 10000)

        btn_confirm = QPushButton("🚀 Valider et Générer la Facture")
        btn_confirm.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 10px 20px; border-radius: 6px;")
        btn_confirm.clicked.connect(self.process_generation)

        p_layout.addWidget(QLabel("N° Facture :"))
        p_layout.addWidget(self.input_num_fact)
        p_layout.addWidget(QLabel("Remise :"))
        p_layout.addWidget(self.spin_remise)
        p_layout.addWidget(QLabel("Incoterm :"))
        p_layout.addWidget(self.input_incoterm)
        p_layout.addWidget(QLabel("Poids :"))
        p_layout.addWidget(self.spin_poids)
        p_layout.addWidget(btn_confirm)
        layout.addWidget(self.invoice_panel)

    def setup_history_ui(self):
        """Interface de consultation Historique"""
        layout = QVBoxLayout(self.tab_hist)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Filtres Historique
        h_filter_card = QFrame()
        h_filter_card.setStyleSheet("background-color: #F9FAFB; border-radius: 10px; border: 1px solid #E5E7EB;")
        hf_layout = QHBoxLayout(h_filter_card)

        self.hist_mois = QComboBox()
        self.hist_mois.addItems(["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
        self.hist_mois.setCurrentIndex(date.today().month - 1)
        
                                # NOUVEAU : Sélecteur d'Année
        self.hist_annee = QSpinBox()
        self.hist_annee.setRange(2000, 2100)
        self.hist_annee.setValue(datetime.now().year) # Par défaut 2026
        self.hist_annee.setMinimumWidth(80)

        """
        self.hist_annee = QComboBox()
        self.hist_annee.setMinimumWidth(120)
        curr = date.today().year
        self.hist_annee.addItems([str(y) for y in range(curr-3, curr+1)])
        self.hist_annee.setCurrentText(str(curr))
        """

        btn_search_hist = QPushButton("🔍 Rechercher Factures")
        btn_search_hist.setStyleSheet("background-color: #4B5563; color: white; padding: 10px 20px; font-weight: bold; border-radius: 6px;")
        btn_search_hist.clicked.connect(self.load_history)

        hf_layout.addWidget(QLabel("Mois :"))
        hf_layout.addWidget(self.hist_mois)
        hf_layout.addWidget(QLabel("Année :"))
        hf_layout.addWidget(self.hist_annee)
        hf_layout.addStretch()
        hf_layout.addWidget(btn_search_hist)
        layout.addWidget(h_filter_card)

        # Table Historique
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(5)
        self.table_history.setHorizontalHeaderLabels(["N° Facture", "Date", "Client", "Net (DT)", "Action"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        #self.table_history.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table_history)

    # --- LOGIQUE MÉTIER ---

    def ouvrir_dialog_taux(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuration du Taux de Change")
        dialog.setFixedWidth(350)
        d_layout = QVBoxLayout(dialog)
        form = QFormLayout()

        mois = self.combo_mois.currentIndex() + 1
        annee = int(self.combo_annee.value())
        
        lbl_info = QLabel(f"Configuration pour : {self.combo_mois.currentText()} {annee}")
        lbl_info.setStyleSheet("font-weight: bold; color: #6366F1; margin-bottom: 10px;")
        d_layout.addWidget(lbl_info)

        spin_taux = QDoubleSpinBox()
        spin_taux.setRange(0, 1000)
        spin_taux.setDecimals(4)
        spin_taux.setValue(3.4000)

        form.addRow("Taux de change (DT) :", spin_taux)
        d_layout.addLayout(form)

        btn_save = QPushButton("Enregistrer")
        btn_save.setStyleSheet("background-color: #6366F1; color: white; padding: 10px; font-weight: bold; border-radius: 6px;")
        
        def save_action():
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {"mois": mois, "annee": annee, "taux": spin_taux.value(), "devise": "DT"}
                resp = requests.post(f"{self.api_url}/factures/ajouter", json=data, headers=headers)
                
                if resp.status_code == 200:
                    QMessageBox.information(dialog, "Succès", "Taux enregistré avec succès.")
                    dialog.accept()
                else:
                    # Tentative de modification si déjà existant
                    update_data = {"mois": mois, "annee": annee, "nouveau_taux": spin_taux.value()}
                    requests.put(f"{self.api_url}/factures/modifier_taux", json=update_data, headers=headers)
                    QMessageBox.information(dialog, "Succès", "Taux mis à jour.")
                    dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Erreur", str(e))

        btn_save.clicked.connect(save_action)
        d_layout.addWidget(btn_save)
        dialog.exec()

    def load_clients_a_facturer(self):
        # 1. Récupération des valeurs
        mois_selectionne = self.combo_mois.currentIndex() + 1
        annee_selectionnee = int(self.combo_annee.value())
        
        # 2. Vérification de la date (Sécurité dernier jour du mois)
        today = date.today()
        # Calcule le dernier jour du mois sélectionné
        dernier_jour_mois = calendar.monthrange(annee_selectionnee, mois_selectionne)[1]
        
        # Si on essaie de facturer le mois actuel (ou futur) avant son dernier jour
        if annee_selectionnee >= today.year and mois_selectionne >= today.month:
            if today.day < dernier_jour_mois:
                QMessageBox.warning(
                    self, 
                    "Période non clôturée", 
                    f"La facturation pour {self.combo_mois.currentText()} {annee_selectionnee} "
                    f"ne sera disponible que le {dernier_jour_mois}/{mois_selectionne}/{annee_selectionnee}.\n\n"
                    "Cela garantit que tous les BL (jusqu'au dernier jour) sont inclus."
                )
                self.table_clients.setRowCount(0)
                self.invoice_panel.setVisible(False)
                return

        # 3. Si la date est valide, on procède à l'appel API
        self.invoice_panel.setVisible(False)
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            params = {"mois": mois_selectionne, "annee": annee_selectionnee}
            resp = requests.get(f"{self.api_url}/factures/clients-non-factures/", params=params, headers=headers)
            
            if resp.status_code == 200:
                clients = resp.json()
                self.table_clients.setRowCount(0)
                if not clients:
                    QMessageBox.information(self, "Info", "Aucun client n'a de bons de livraison en attente pour cette période.")
                    return
                
                for c in clients:
                    row = self.table_clients.rowCount()
                    self.table_clients.insertRow(row)
                    # Colonne 0 : Nom du client + ID caché
                    item_nom = QTableWidgetItem(c['nom_client'])
                    # On stocke l'ID dans le "UserRole" pour le récupérer plus tard
                    item_nom.setData(Qt.ItemDataRole.UserRole, c['id_client'])
                    self.table_clients.setItem(row, 0, item_nom)
                    #self.table_clients.setItem(row, 1, QTableWidgetItem(c['nom_client']))
                    self.table_clients.setItem(row, 1, QTableWidgetItem(c['code_client']))
                    self.table_clients.setItem(row, 2, QTableWidgetItem(c['statut']))
                    
                    btn = QPushButton("Choisir")
                    btn.setStyleSheet("background-color: #6366F1; color: white; border-radius: 4px;")
                    btn.clicked.connect(lambda chk, id_c=c['id_client']: self.select_client(id_c))
                    self.table_clients.setCellWidget(row, 3, btn)
            else:
                QMessageBox.critical(self, "Erreur", resp.json().get('detail', "Erreur serveur"))
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur de connexion", f"Impossible de joindre le serveur : {str(e)}")

    def select_client(self, client_id):
        self.selected_client_id = client_id
        self.invoice_panel.setVisible(True)
        self.input_num_fact.setFocus()

    def process_generation(self):
        if not self.input_num_fact.text():
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez entrer un numéro de facture.")
            return

        data = {
            "id_client": self.selected_client_id,
            "mois": self.combo_mois.currentIndex() + 1,
            "annee": int(self.combo_annee.value()),
            "numero_facture_manuel": self.input_num_fact.text(),
            "remise_globale_facture": self.spin_remise.value(),
            "poids_total": self.spin_poids.value(),           # <-- AJOUT ICI
            "incoterm": self.input_incoterm.currentText()
        }

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.post(f"{self.api_url}/factures/generer", json=data, headers=headers)
            if resp.status_code == 200:
                res = resp.json()
                QMessageBox.information(self, "Succès", f"Facture {res.get('numero', 'Générée')} enregistrée !")
                self.invoice_panel.setVisible(False)
                self.input_num_fact.clear()
                self.load_clients_a_facturer()
            else:
                QMessageBox.critical(self, "Erreur API", resp.json().get('detail', "Erreur inconnue"))
        except Exception as e:
            QMessageBox.critical(self, "Erreur Système", str(e))

    def load_history(self):
        mois = self.hist_mois.currentIndex() + 1
        annee = int(self.hist_annee.value())
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.get(f"{self.api_url}/factures/all", params={"mois": mois, "annee": annee}, headers=headers)
            if resp.status_code == 200:
                factures = resp.json()
                self.table_history.setRowCount(0)
                for f in factures:
                    row = self.table_history.rowCount()
                    self.table_history.insertRow(row)
                    
                    self.table_history.setItem(row, 0, QTableWidgetItem(str(f.get('numero_facture') or f['id_facture'])))
                    self.table_history.setItem(row, 1, QTableWidgetItem(str(f['date_facture'])))
                    self.table_history.setItem(row, 2, QTableWidgetItem(f['client_nom']))
                    
                    montant = f.get('montant_net_dt', 0.0)
                    m_item = QTableWidgetItem(f"{montant:.3f} DT")
                    m_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table_history.setItem(row, 3, m_item)
                    
                    # --- CONTENEUR D'ACTIONS ---
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(2, 2, 2, 2)
                    actions_layout.setSpacing(5)

                    # Bouton PDF (Existant)
                    btn_pdf = QPushButton("📥 PDF")
                    btn_pdf.setStyleSheet("background-color: #EF4444; color: white; border-radius: 4px; font-weight: bold; padding: 5px;")
                    btn_pdf.clicked.connect(lambda chk, id_f=f['id_facture']: self.download_pdf(id_f))
                    
                    # Bouton CSV (Nouveau)
                    btn_csv = QPushButton("📊 CSV")
                    btn_csv.setStyleSheet("background-color: #059669; color: white; border-radius: 4px; font-weight: bold; padding: 5px;")
                    btn_csv.clicked.connect(lambda chk, id_f=f['id_facture'], num=f.get('numero_facture'): self.download_csv(id_f, num))
                    
                    actions_layout.addWidget(btn_pdf)
                    actions_layout.addWidget(btn_csv)
                    
                    self.table_history.setCellWidget(row, 4, actions_widget)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def download_pdf(self, facture_id):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.get(f"{self.api_url}/factures/pdf/{facture_id}", headers=headers)
            if resp.status_code == 200:
                path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder la Facture", f"Facture_{facture_id}.pdf", "PDF Files (*.pdf)")
                if path:
                    with open(path, 'wb') as f:
                        f.write(resp.content)
                    QMessageBox.information(self, "Terminé", "Le PDF a été enregistré avec succès.")
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de récupérer le fichier PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            
    def download_csv(self, facture_id, numero_facture):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.get(f"{self.api_url}/factures/{facture_id}/csv", headers=headers)
            
            if resp.status_code == 200:
                # Nettoyage du numéro de facture pour éviter les caractères interdits dans le nom de fichier
                clean_num = str(numero_facture or facture_id).replace("/", "_").replace("\\", "_")
                filename = f"Facture_{clean_num}.csv"
                
                path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder le CSV", filename, "CSV Files (*.csv)")
                
                if path:
                    try:
                        with open(path, 'wb') as f:
                            f.write(resp.content)
                        QMessageBox.information(self, "Succès", "Fichier CSV enregistré.")
                    except PermissionError:
                        QMessageBox.critical(self, "Erreur de Permission", 
                            f"Impossible d'enregistrer le fichier.\n\n"
                            f"Vérifiez que le fichier '{filename}' n'est pas déjà ouvert dans Excel "
                            f"et que vous avez le droit d'écrire dans ce dossier.")
            else:
                QMessageBox.critical(self, "Erreur", f"Erreur serveur: {resp.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Système", f"Erreur : {str(e)}")
        
        