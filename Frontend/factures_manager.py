import sys
import requests
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDateEdit, QMessageBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QIntValidator, QDoubleValidator
from PyQt6.QtCore import QDate
from datetime import date
from decimal import Decimal
#from config import API_BASE_URL

class FacturesManager(QWidget):
    def __init__(self, base_url, headers, user_role, parent=None):
        super().__init__(parent)
        self.base_url = base_url
        self.headers = headers
        self.user_role = user_role
        self.clients = {}
        
        # Appliquer le Style Sheet au FacturesManager
        self.setStyleSheet(self.get_stylesheet()) 
        
        self.init_ui()
        self.load_factures()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # =====================================================================
        #                         Section Taux de Change
        # =====================================================================
        
        # Titre stylisé
        taux_change_title = QLabel("Gestion du Taux de Change")
        taux_change_title.setObjectName("SectionTitle")
        
        # Conteneur stylisé (remplace QGroupBox)
        taux_change_container = QWidget()
        taux_change_container.setObjectName("SectionContainer")
        taux_layout = QGridLayout(taux_change_container)

        self.taux_mois_edit = QLineEdit(self)
        self.taux_mois_edit.setPlaceholderText("Mois (1-12)")
        self.taux_mois_edit.setObjectName("TauxMoisEdit")
        
        self.taux_annee_edit = QLineEdit(self)
        self.taux_annee_edit.setPlaceholderText("Année (YYYY)")
        self.taux_annee_edit.setObjectName("TauxAnneeEdit")
        
        self.taux_taux_edit = QLineEdit(self)
        self.taux_taux_edit.setPlaceholderText("Taux (ex: 3.250)")
        self.taux_taux_edit.setObjectName("TauxTauxEdit")

        self.add_taux_btn = QPushButton("Ajouter un Taux", self)
        self.add_taux_btn.setObjectName("AddTauxButton")
        self.mod_taux_btn = QPushButton("Modifier le Taux", self)
        self.mod_taux_btn.setObjectName("ModTauxButton")

        # Utilisation de QLabel génériques pour les labels du formulaire
        taux_layout.addWidget(QLabel("Mois:"), 0, 0)
        taux_layout.addWidget(self.taux_mois_edit, 0, 1)
        taux_layout.addWidget(QLabel("Année:"), 1, 0)
        taux_layout.addWidget(self.taux_annee_edit, 1, 1)
        taux_layout.addWidget(QLabel("Taux:"), 2, 0)
        taux_layout.addWidget(self.taux_taux_edit, 2, 1)
        taux_layout.addWidget(self.add_taux_btn, 3, 0)
        taux_layout.addWidget(self.mod_taux_btn, 3, 1)

        main_layout.addWidget(taux_change_title)
        main_layout.addWidget(taux_change_container)

        # =====================================================================
        #                         Section Génération de Facture
        # =====================================================================
        
        # Titre stylisé
        facture_title = QLabel("Génération de Facture")
        facture_title.setObjectName("SectionTitle")
        
        # Conteneur stylisé (remplace QGroupBox)
        facture_container = QWidget()
        facture_container.setObjectName("SectionContainer")
        facture_layout = QGridLayout(facture_container)

        # Les widgets n'ont pas besoin d'être réorganisés, juste de recevoir des ID pour le style
        self.client_combo_facture = QComboBox(self)
        self.client_combo_facture.setObjectName("ClientComboFacture")
        self.remise_edit = QLineEdit(self)
        self.remise_edit.setPlaceholderText("Remise (%)")
        self.remise_edit.setObjectName("RemiseEdit")
        self.poids_edit = QLineEdit(self)
        self.poids_edit.setPlaceholderText("Poids (kg)")
        self.poids_edit.setObjectName("PoidsEdit")

        self.load_clients_btn = QPushButton("Charger les clients à facturer", self)
        self.load_clients_btn.setObjectName("LoadClientsButton")
        self.generer_facture_btn = QPushButton("Générer la Facture", self)
        self.generer_facture_btn.setObjectName("GenerateFactureButton")
        
        self.facture_mois_edit = QLineEdit(self)
        self.facture_mois_edit.setPlaceholderText("Mois (1-12)")
        self.facture_mois_edit.setObjectName("FactureMoisEdit")
        
        self.facture_annee_edit = QLineEdit(self)
        self.facture_annee_edit.setPlaceholderText("Année (YYYY)")
        self.facture_annee_edit.setObjectName("FactureAnneeEdit")

        facture_layout.addWidget(QLabel("Mois:"), 0, 0)
        facture_layout.addWidget(self.facture_mois_edit, 0, 1)

        facture_layout.addWidget(QLabel("Année:"), 1, 0)
        facture_layout.addWidget(self.facture_annee_edit, 1, 1)

        facture_layout.addWidget(self.load_clients_btn, 2, 0, 1, 2)
        facture_layout.addWidget(QLabel("Client:"), 3, 0)
        facture_layout.addWidget(self.client_combo_facture, 3, 1)
        facture_layout.addWidget(QLabel("Remise:"), 4, 0)
        facture_layout.addWidget(self.remise_edit, 4, 1)
        facture_layout.addWidget(QLabel("Poids:"), 5, 0)
        facture_layout.addWidget(self.poids_edit, 5, 1)
        facture_layout.addWidget(self.generer_facture_btn, 6, 0, 1, 2)

        main_layout.addWidget(facture_title)
        main_layout.addWidget(facture_container)
        
        # =====================================================================
        #                         Section Affichage des Factures
        # =====================================================================
        
        # Titre stylisé
        factures_list_title = QLabel("Factures existantes")
        factures_list_title.setObjectName("SectionTitle")
        
        # Conteneur stylisé (remplace QGroupBox)
        factures_list_container = QWidget()
        factures_list_container.setObjectName("SectionContainer")
        factures_list_layout = QVBoxLayout(factures_list_container)
        
        self.factures_table = QTableWidget(self)
        self.factures_table.setObjectName("FacturesTable")
        self.factures_table.setColumnCount(4)
        self.factures_table.setHorizontalHeaderLabels(["ID", "Date", "Client", "Actions"])
        self.factures_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.factures_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        self.delete_all_factures_btn = QPushButton("Supprimer toutes les factures", self)
        self.delete_all_factures_btn.setObjectName("DeleteAllButton")
    
        factures_list_layout.addWidget(self.factures_table)
        factures_list_layout.addWidget(self.delete_all_factures_btn)
        
        main_layout.addWidget(factures_list_title)
        main_layout.addWidget(factures_list_container)

        # Connexions des signaux (inchangées)
        self.add_taux_btn.clicked.connect(self.ajouter_taux)
        self.mod_taux_btn.clicked.connect(self.modifier_taux)
        self.load_clients_btn.clicked.connect(self.load_clients_a_facturer)
        self.generer_facture_btn.clicked.connect(self.generer_facture)
        self.delete_all_factures_btn.clicked.connect(self.delete_all_factures)

        # Validation des entrées numériques (inchangée)
        self.taux_mois_edit.setValidator(QIntValidator(1, 12, self))
        self.taux_annee_edit.setValidator(QIntValidator(2000, 2100, self))
        self.remise_edit.setValidator(QDoubleValidator(0.0, 100.0, 2, self))
        self.poids_edit.setValidator(QDoubleValidator(0.0, 9999.99, 2, self))
        self.facture_mois_edit.setValidator(QIntValidator(1, 12, self))
        self.facture_annee_edit.setValidator(QIntValidator(2000, 2100, self))

# -----------------------------------------------------------------------------
#                               STYLE SHEET CSS
# -----------------------------------------------------------------------------

    def get_stylesheet(self):
        return """
            QWidget {
                background-color: #2e3440; /* Fond sombre */
                color: #eceff4;
                font-size: 14px;
            }
            
            /* Titres de section */
            #SectionTitle {
                color: #88c0d0; /* Bleu clair d'accentuation */
                font-size: 20px;
                font-weight: bold;
                padding: 10px 0 5px 0;
            }

            /* Conteneur de section */
            #SectionContainer {
                background-color: #3b4252;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
            }

            /* Champs de saisie et ComboBox */
            QLineEdit, QComboBox, QDateEdit {
                background-color: #4c566a;
                border: 1px solid #5e81ac;
                border-radius: 4px;
                padding: 5px;
                color: #eceff4;
            }
            
            /* Labels (texte simple) */
            QLabel {
                color: #eceff4;
            }

            /* Style des Tables */
            QTableWidget {
                background-color: #4c566a;
                border: 1px solid #5e81ac;
                gridline-color: #3b4252;
                alternate-background-color: #556075;
                color: #eceff4;
            }
            
            QHeaderView::section {
                background-color: #5e81ac; /* Bleu d'en-tête */
                color: #eceff4;
                padding: 6px;
                border: 1px solid #3b4252;
                font-weight: bold;
            }

            /* Boutons généraux (par défaut vert/bleu pour les actions principales) */
            QPushButton {
                background-color: #a3be8c; /* Vert par défaut pour les actions positives */
                color: #2e3440;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4e39d;
            }
            
            /* Boutons spécifiques du taux de change */
            #ModTauxButton {
                background-color: #5e81ac; /* Bleu pour la modification */
                color: #eceff4;
            }
            #ModTauxButton:hover {
                background-color: #6a95c9;
            }
            
            /* Boutons de la section Facture */
            #LoadClientsButton {
                background-color: #5e81ac;
                color: #eceff4;
                margin-top: 10px;
            }
            #LoadClientsButton:hover {
                background-color: #6a95c9;
            }
            
            #GenerateFactureButton {
                background-color: #88c0d0; /* Bleu plus clair pour l'action finale */
                color: #2e3440;
            }
            #GenerateFactureButton:hover {
                background-color: #9cdbe0;
            }
            
            /* Bouton de suppression de toutes les factures (action critique) */
            #DeleteAllButton {
                background-color: #bf616a; /* Rouge pour l'action destructive */
                color: #eceff4;
                margin-top: 10px;
            }
            #DeleteAllButton:hover {
                background-color: #d0757d;
            }
            
            /* Bouton dans la table (PDF) */
            QTableWidget QPushButton {
                background-color: #88c0d0;
                color: #2e3440;
                padding: 4px;
                font-size: 12px;
            }
        """

    # ... (le reste des méthodes comme _make_request, ajouter_taux, etc. restent inchangées) ...

    def _make_request(self, method, endpoint, payload=None, params=None):
        try:
            url = f"{self.base_url}{endpoint}"
            if method == "POST":
                response = requests.post(url, json=payload, headers=self.headers)
            elif method == "PUT":
                response = requests.put(url, json=payload, headers=self.headers)
            elif method == "GET":
                response = requests.get(url, params=params, headers=self.headers)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", "Erreur inconnue")
            QMessageBox.critical(self, "Erreur API", f"Erreur {e.response.status_code}: {error_detail}")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Erreur de connexion", f"Erreur de connexion au serveur: {e}")
        return None

    def ajouter_taux(self):
        mois = self.taux_mois_edit.text()
        annee = self.taux_annee_edit.text()
        taux = self.taux_taux_edit.text()
        
        if not (mois and annee and taux):
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs.")
            return

        payload = {
            "mois": int(mois),
            "annee": int(annee),
            "taux": float(taux),
            "devise": "DT"
        }
        
        result = self._make_request("POST", "/factures/ajouter", payload=payload)
        if result:
            QMessageBox.information(self, "Succès", result.get("message"))
            self.taux_mois_edit.clear()
            self.taux_annee_edit.clear()
            self.taux_taux_edit.clear()

    def modifier_taux(self):
        mois = self.taux_mois_edit.text()
        annee = self.taux_annee_edit.text()
        nouveau_taux = self.taux_taux_edit.text()
        
        if not (mois and annee and nouveau_taux):
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs.")
            return

        payload = {
            "mois": int(mois),
            "annee": int(annee),
            "nouveau_taux": float(nouveau_taux)
        }
        
        result = self._make_request("PUT", "/factures/modifier_taux", payload=payload)
        if result:
            QMessageBox.information(self, "Succès", result.get("message"))
            self.taux_mois_edit.clear()
            self.taux_annee_edit.clear()
            self.taux_taux_edit.clear()

    def load_clients_a_facturer(self):
        self.client_combo_facture.clear()
        self.clients.clear()
        mois = self.facture_mois_edit.text()
        annee = self.facture_annee_edit.text()

        if not (mois and annee):
            QMessageBox.warning(self, "Erreur", "Veuillez spécifier le mois et l'année.")
            return

        params = {"mois": mois, "annee": annee}
        result = self._make_request("GET", "/factures/clients-non-factures/", params=params)

        if result:
            if not result:
                QMessageBox.information(self, "Information", "Aucun client à facturer pour cette période.")
                return

            self.client_combo_facture.addItem("Sélectionner un client")
            for client in result:
                self.clients[client["nom_client"]] = client["id_client"]
                self.client_combo_facture.addItem(client["nom_client"])

    def generer_facture(self):
        client_nom = self.client_combo_facture.currentText()
        client_id = self.clients.get(client_nom)

        if not client_id:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un client valide.")
            return
            
        mois = self.facture_mois_edit.text()
        annee = self.facture_annee_edit.text()
        remise = self.remise_edit.text()
        poids = self.poids_edit.text()
        
            # We replace the comma with a period before converting to float
        remise_float = float(remise.replace(',', '.')) if remise else 0.0
        poids_float = float(poids.replace(',', '.')) if poids else 0.0
    
        if not (mois and annee):
            QMessageBox.warning(self, "Erreur", "Veuillez spécifier le mois et l'année.")
            return

        payload = {
            "id_client": client_id,
            "mois": int(mois),
            "annee": int(annee),
            "remise": remise_float,  # Use the new float variable
            "poids": poids_float 
        }

        result = self._make_request("POST", "/factures/generer", payload=payload)
        if result:
            message = result.get("message")
            total_dt = result.get("montant_net_dt")
            total_lettre = result.get("total_en_lettre_dt")
            QMessageBox.information(
                self, "Succès",
                f"{message}\n\n"
                f"Montant net : {total_dt:.2f} DT\n"
                f"Total en lettre : {total_lettre}"
            )
            self.clear_form()
            self.load_clients_a_facturer()
            self.load_factures() # Refresh the list after a new invoice is generated

    def clear_form(self):
        self.client_combo_facture.clear()
        self.remise_edit.clear()
        self.poids_edit.clear()
        self.clients.clear()

    def load_factures(self):
        try:
            response = requests.get(f"{self.base_url}/factures/all", headers=self.headers)
            response.raise_for_status()
            factures_data = response.json()
            
            self.factures_table.setRowCount(len(factures_data))
            for i, facture in enumerate(factures_data):
                self.factures_table.setItem(i, 0, QTableWidgetItem(str(facture['id_facture'])))
                self.factures_table.setItem(i, 1, QTableWidgetItem(facture['date_facture']))
                self.factures_table.setItem(i, 2, QTableWidgetItem(facture['client_nom']))
                
                pdf_btn = QPushButton("PDF")
                pdf_btn.clicked.connect(lambda _, fid=facture['id_facture']: self.generer_pdf(fid))
                self.factures_table.setCellWidget(i, 3, pdf_btn)
                
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les factures: {e}")

    def generer_pdf(self, facture_id):
        url = f"{self.base_url}/factures/pdf/{facture_id}"
        webbrowser.open(url)
        
    def delete_all_factures(self):
        reply = QMessageBox.question(self, 'Confirmation de suppression',
                                    "Êtes-vous sûr de vouloir supprimer TOUTES les factures ? Cette action est irréversible.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                response = requests.delete(f"{self.base_url}/factures/all", headers=self.headers)
                response.raise_for_status()
                
                result = response.json()
                QMessageBox.information(self, "Succès", result.get("message"))
                self.load_factures() # Recharger la liste des factures
                
            except requests.exceptions.HTTPError as e:
                error_detail = e.response.json().get("detail", "Erreur inconnue")
                QMessageBox.critical(self, "Erreur API", f"Erreur {e.response.status_code}: {error_detail}")
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Erreur de connexion", f"Erreur de connexion au serveur: {e}")