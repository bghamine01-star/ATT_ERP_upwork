import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QScrollArea, QMessageBox, QFrame, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QTextEdit, QPushButton
from config import API_BASE_URL

class ClientRow(QFrame):
    """Ligne de client stylisée avec détails et bouton suppression"""
    def __init__(self, client_data, delete_callback):
        super().__init__()
        self.client_data = client_data
        self.client_id = client_data.get('id_client')
        self.nom = client_data.get('nom_client')
        
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #F3F4F6;
                padding: 12px;
            }
            QFrame:hover { background-color: #F9FAFB; }
        """)
        layout = QHBoxLayout(self)
        
        # Section Infos
        info_layout = QVBoxLayout()
        name_lbl = QLabel(self.nom)
        name_lbl.setStyleSheet("font-weight: 600; color: #111827; font-size: 14px; border: none;")
        
        # On affiche le code et le téléphone en sous-titre
        matricule = client_data.get('matricule_fiscal') or "N/A"
        sub_info = f"Code: {client_data.get('code_client')} | MF: {matricule} | 📞 {client_data.get('telephone')}"
        details_lbl = QLabel(sub_info)
        details_lbl.setStyleSheet("color: #6B7280; font-size: 11px; border: none;")
        
        info_layout.addWidget(name_lbl)
        info_layout.addWidget(details_lbl)
        
        # --- NOUVEAU : Bouton Détails ---
        btn_details = QPushButton("Détails")
        btn_details.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_details.setStyleSheet("""
            QPushButton {
                color: #6366F1; background-color: white; border: 1px solid #E0E7FF;
                padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 12px;
            }
            QPushButton:hover { background-color: #F5F7FF; }
        """)
        btn_details.clicked.connect(self.show_full_details)
        
        # Badge de Statut
        status_val = client_data.get('statut')
        status_lbl = QLabel(status_val)
        color = "#10B981" if status_val == "Resident" else "#F59E0B"
        bg_color = "#D1FAE5" if status_val == "Resident" else "#FEF3C7"
        status_lbl.setStyleSheet(f"""
            color: {color}; background-color: {bg_color}; 
            padding: 4px 8px; border-radius: 12px; 
            font-size: 10px; font-weight: bold; border: none;
        """)
        
        # Bouton Supprimer
        btn_del = QPushButton("Supprimer")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                color: #DC2626; background-color: white; border: 1px solid #FEE2E2;
                padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 12px;
            }
            QPushButton:hover { background-color: #DC2626; color: white; }
        """)
        btn_del.clicked.connect(lambda: delete_callback(self.client_id, self.nom))
        
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(btn_details) # Ajout du bouton détails
        layout.addSpacing(10)
        layout.addWidget(status_lbl)
        layout.addSpacing(15)
        layout.addWidget(btn_del)
        

    def show_full_details(self):
        """Affiche une fiche client sobre et sélectionnable"""
        d = self.client_data
        
        # Création d'une boîte de dialogue personnalisée
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Fiche Client - {self.nom}")
        dialog.setMinimumSize(400, 350)
        layout = QVBoxLayout(dialog)

        # Zone de texte riche pour permettre la sélection/copie
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setStyleSheet("""
            QTextEdit {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #374151;
                line-height: 1.6;
            }
        """)

        # Construction du contenu textuel (Format sobre)
        content = f"""
        <p><b>IDENTIFICATION</b><br>
        Nom : {d.get('nom_client')}<br>
        Code : {d.get('code_client')}<br>
        Matricule Fiscal : {d.get('matricule_fiscal') or 'Non renseigné'}<br>
        Statut : {d.get('statut')}</p>

        <p><b>COORDONNÉES</b><br>
        Email : {d.get('email')}<br>
        Téléphone : {d.get('telephone')}<br>
        Adresse : {d.get('adresse')}</p>
        """
        
        text_area.setHtml(content)
        layout.addWidget(text_area)

        # Bouton de fermeture
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(dialog.accept)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #6366F1; color: white; padding: 8px; 
                border-radius: 6px; font-weight: 600; border: none;
            }
            QPushButton:hover { background-color: #4F46E5; }
        """)
        layout.addWidget(btn_close)

        dialog.exec()

class ClientManager(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.api_url = API_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.init_ui()
        self.load_clients()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(25)

        # Titre conforme à vos paramètres
        title = QLabel("Gestion des Clients")
        title.setStyleSheet("""
            font-family: 'Inter', sans-serif; font-size: 28px;
            font-weight: 600; letter-spacing: -0.02em; color: #111827;
        """)
        self.main_layout.addWidget(title)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        # --- Barre de Recherche ---
        search_layout = QHBoxLayout()
        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("🔍 Rechercher un client par nom")
        self.search_in.setStyleSheet("""
            padding: 10px 15px; 
            border: 1px solid #E5E7EB; 
            border-radius: 20px; 
            background: white;
            font-size: 14px;
        """)
        # Connecte le changement de texte à la fonction de recherche
        self.search_in.textChanged.connect(self.filter_clients)
        search_layout.addWidget(self.search_in)
        self.main_layout.addLayout(search_layout)

        # 1. LISTE DES CLIENTS (Gauche)
        self.list_container = QFrame()
        self.list_container.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #E5E7EB;")
        list_vbox = QVBoxLayout(self.list_container)
        list_vbox.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Répertoire Clients")
        header.setStyleSheet("padding: 20px; font-weight: bold; font-size: 16px; color: #111827; border-bottom: 1px solid #E5E7EB;")
        list_vbox.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        self.scroll.verticalScrollBar().setStyleSheet("QScrollBar { width: 0px; }")
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.addStretch()
        
        self.scroll.setWidget(self.scroll_widget)
        list_vbox.addWidget(self.scroll)

        # 2. FORMULAIRE D'AJOUT (Droite - Compact)
        self.right_col = QVBoxLayout()
        self.form_card = QFrame()
        self.form_card.setFixedWidth(350)
        self.form_card.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #E5E7EB;")
        
        form_vbox = QVBoxLayout(self.form_card)
        form_vbox.setSpacing(12)
        
        f_title = QLabel("Nouveau Client")
        f_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #111827; border: none; margin-bottom: 5px;")
        
        input_style = "padding: 8px; border: 1px solid #D1D5DB; border-radius: 6px; background: #F9FAFB;"
        
        self.name_in = QLineEdit(); self.name_in.setPlaceholderText("Nom du client"); self.name_in.setStyleSheet(input_style)
        self.code_in = QLineEdit(); self.code_in.setPlaceholderText("Code client (Unique)"); self.code_in.setStyleSheet(input_style)
        self.mf_in = QLineEdit(); self.mf_in.setPlaceholderText("Matricule Fiscal"); self.mf_in.setStyleSheet(input_style)
        self.email_in = QLineEdit(); self.email_in.setPlaceholderText("Email"); self.email_in.setStyleSheet(input_style)
        self.phone_in = QLineEdit(); self.phone_in.setPlaceholderText("Téléphone"); self.phone_in.setStyleSheet(input_style)
        
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(["Resident", "Non_Resident"])
        self.statut_combo.setStyleSheet(input_style)
        
        self.addr_in = QTextEdit()
        self.addr_in.setPlaceholderText("Adresse complète...")
        self.addr_in.setMaximumHeight(80)
        self.addr_in.setStyleSheet(input_style)
        
        btn_add = QPushButton("Enregistrer le client")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background-color: #6366F1; color: white; padding: 12px; border-radius: 6px; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #4F46E5; }
        """)
        btn_add.clicked.connect(self.add_client)

        form_vbox.addWidget(f_title)
        form_vbox.addWidget(self.name_in); form_vbox.addWidget(self.code_in)
        form_vbox.addWidget(self.mf_in)
        form_vbox.addWidget(self.email_in); form_vbox.addWidget(self.phone_in)
        form_vbox.addWidget(self.statut_combo)
        form_vbox.addWidget(self.addr_in)
        form_vbox.addWidget(btn_add)

        self.right_col.addWidget(self.form_card)
        self.right_col.addStretch()

        content_layout.addWidget(self.list_container, stretch=2)
        content_layout.addLayout(self.right_col, stretch=1)
        self.main_layout.addLayout(content_layout)
        
    

    def filter_clients(self):
        search_text = self.search_in.text().lower()
        
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            
            if isinstance(widget, ClientRow):
                # On s'assure de chercher dans des chaînes de caractères (str)
                nom = str(widget.nom).lower()
                # Si tu veux chercher aussi par l'ID, transforme-le en string d'abord
                id_str = str(widget.client_id) 
                
                match = (search_text in nom or search_text in id_str)
                widget.setVisible(match)
                
    def load_clients(self):
        try:
            # On utilise la route /clients/ qui renvoie une liste
            response = requests.get(f"{self.api_url}/clients/", headers=self.headers)
            if response.status_code == 200:
                # Nettoyage
                for i in reversed(range(self.scroll_layout.count() - 1)):
                    self.scroll_layout.itemAt(i).widget().setParent(None)
                
                for client in response.json():
                    row = ClientRow(client, self.delete_client)
                    self.scroll_layout.insertWidget(0, row)
        except Exception as e:
            print(f"Erreur chargement clients: {e}")
            
    def format_api_errors(self, error_data):
        """Transforme les erreurs techniques Pydantic en français clair"""
        if not isinstance(error_data, dict) or "detail" not in error_data:
            return "Une erreur de validation est survenue."

        details = error_data["detail"]
        if not isinstance(details, list):
            return str(details)

        translated_messages = []
        
        # Dictionnaire de traduction des erreurs types de Pydantic
        translations = {
            "value_error.missing": "est obligatoire",
            "string_too_short": "ne peut pas être vide",
            "value_is_not_a_valid_email": "n'est pas une adresse email valide",
            "enum": "n'est pas une option valide",
            "less_than_at_least": "doit avoir au moins 1 caractère"
        }

        for err in details:
            # 1. On récupère le nom du champ (ex: nom_client)
            # loc est souvent ['body', 'nom_client']
            field_name = err.get("loc", [""])[-1]
            field_name = field_name.replace("_", " ").capitalize() # 'nom_client' -> 'Nom client'
            
            # 2. On récupère le message technique
            raw_msg = err.get("msg", "")
            error_type = err.get("type", "")

            # 3. On cherche une traduction
            clean_msg = "donnée invalide" # Message par défaut
            
            if "at least 1 character" in raw_msg or error_type == "string_too_short":
                clean_msg = "ne peut pas être vide"
            elif "valid email" in raw_msg:
                clean_msg = "doit être un email valide"
            elif error_type == "value_error.missing":
                clean_msg = "est obligatoire"
            
            translated_messages.append(f"• <b>{field_name}</b> : {clean_msg}")

        return "<br>".join(translated_messages)

    def add_client(self):
        payload = {
            "nom_client": self.name_in.text(),
            "code_client": self.code_in.text(),
            "matricule_fiscal": self.mf_in.text(),
            "email": self.email_in.text(),
            "telephone": self.phone_in.text(),
            "statut": self.statut_combo.currentText(),
            "adresse": self.addr_in.toPlainText()
        }
        
        try:
            res = requests.post(f"{self.api_url}/clients/", json=payload, headers=self.headers)
            if res.status_code == 201:
                self.load_clients()
                self.clear_form()
                QMessageBox.information(self, "Succès", "Client enregistré avec succès !")
            
            elif res.status_code == 422: # Erreur de validation Pydantic
                error_msg = self.format_api_errors(res.json())
                QMessageBox.warning(self, "Erreur de saisie", error_msg)
                
            elif res.status_code == 400: # Erreur d'intégrité (ex: doublon)
                detail = res.json().get('detail', "Erreur de doublon")
                QMessageBox.warning(self, "Donnée existante", detail)
                
            else:
                QMessageBox.critical(self, "Erreur", f"Erreur serveur ({res.status_code})")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur de connexion", f"Impossible de joindre le serveur : {str(e)}")

    def delete_client(self, client_id, nom):
        if QMessageBox.question(self, "Confirmation", f"Supprimer le client {nom} ?") == QMessageBox.StandardButton.Yes:
            res = requests.delete(f"{self.api_url}/clients/{client_id}", headers=self.headers)
            if res.status_code == 200:
                self.load_clients()
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de supprimer le client, ce dernier possède des ventes associées")

    def clear_form(self):
        self.name_in.clear(); self.code_in.clear()
        self.mf_in.clear()
        self.email_in.clear(); self.phone_in.clear()
        self.addr_in.clear()