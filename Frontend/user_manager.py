import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QScrollArea, QMessageBox, QFrame, QComboBox
)
from PyQt6.QtCore import Qt
from config import API_BASE_URL

class UserRow(QFrame):
    """Représente une ligne de profil stylisée comme dans l'image"""
    def __init__(self, nom, role, delete_callback):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #F3F4F6;
                padding: 10px;
            }
            QFrame:hover { background-color: #F9FAFB; }
        """)
        layout = QHBoxLayout(self)
        
        # Info Profil (Nom et Rôle)
        info_layout = QVBoxLayout()
        name_lbl = QLabel(nom)
        name_lbl.setStyleSheet("font-weight: 600; color: #111827; font-size: 14px; border: none;")
        
        role_lbl = QLabel(role.upper())
        role_lbl.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: bold; border: none;")
        
        info_layout.addWidget(name_lbl)
        info_layout.addWidget(role_lbl)
        
        # Bouton Supprimer (Cadrant embelli rouge)
        btn_del = QPushButton("Supprimer")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                color: #DC2626;
                background-color: white;
                border: 1px solid #FEE2E2;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #DC2626;
                color: white;
            }
        """)
        btn_del.clicked.connect(lambda: delete_callback(nom))
        
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(btn_del)

class UserManager(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.api_url = API_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.init_ui()
        self.load_users()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(25)

        # TITRE PRINCIPAL (Inter, 28px, 600)
        title = QLabel("Gestion des Utilisateurs")
        title.setStyleSheet("""
            font-family: 'Inter', sans-serif; font-size: 28px;
            font-weight: 600; letter-spacing: -0.02em; color: #111827;
        """)
        self.main_layout.addWidget(title)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)

        # 1. ZONE GAUCHE : DÉTAILS DES PROFILS (Style Image)
        self.list_container = QFrame()
        self.list_container.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #E5E7EB;")
        list_vbox = QVBoxLayout(self.list_container)
        list_vbox.setContentsMargins(0, 0, 0, 0)

        header_label = QLabel("Détails des profils")
        header_label.setStyleSheet("""
            padding: 20px; font-weight: bold; font-size: 16px; 
            color: #111827; border-bottom: 1px solid #E5E7EB;
        """)
        list_vbox.addWidget(header_label)

        # Scroll Area avec barre invisible
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        self.scroll.verticalScrollBar().setStyleSheet("QScrollBar { width: 0px; }") # Barre invisible
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.addStretch() # Pousse les éléments vers le haut
        
        self.scroll.setWidget(self.scroll_widget)
        list_vbox.addWidget(self.scroll)

        # 2. ZONE DROITE : FORMULAIRE (Similaire à l'image)
# 2. ZONE DROITE : FORMULAIRE (Réduit en hauteur)
        self.right_column = QVBoxLayout() # On crée une colonne verticale à droite
        
        self.form_card = QFrame()
        self.form_card.setFixedWidth(320)
        # On ne fixe pas la hauteur, mais on laisse le contenu décider
        self.form_card.setStyleSheet("""
            QFrame {
                background-color: white; 
                border-radius: 12px; 
                border: 1px solid #E5E7EB;
            }
        """)
        
        form_vbox = QVBoxLayout(self.form_card)
        form_vbox.setContentsMargins(20, 25, 20, 25)
        form_vbox.setSpacing(15) # Un peu d'espace entre les champs
        
        f_title = QLabel("Nouvel Utilisateur")
        f_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #111827; border:none;")
        
        input_css = """
            QLineEdit, QComboBox {
                padding: 10px; 
                border: 1px solid #D1D5DB; 
                border-radius: 6px; 
                background: #F9FAFB;
                color: #374151;
            }
            QLineEdit:focus { border: 2px solid #6366F1; }
        """
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nom complet")
        self.name_input.setStyleSheet(input_css)
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Mot de passe")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setStyleSheet(input_css)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["employe", "gerant"])
        self.role_combo.setStyleSheet(input_css)
        
        btn_add = QPushButton("Créer le compte")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { 
                background-color: #6366F1; color: white; padding: 12px; 
                border-radius: 6px; font-weight: bold; border:none; 
            }
            QPushButton:hover { background-color: #4F46E5; }
        """)
        btn_add.clicked.connect(self.add_user)

        # Ajout des widgets au layout du formulaire
        form_vbox.addWidget(f_title)
        form_vbox.addWidget(QLabel("Nom"))
        form_vbox.addWidget(self.name_input)
        form_vbox.addWidget(QLabel("Mot de passe"))
        form_vbox.addWidget(self.pass_input)
        form_vbox.addWidget(QLabel("Rôle"))
        form_vbox.addWidget(self.role_combo)
        form_vbox.addSpacing(10)
        form_vbox.addWidget(btn_add)

        # --- LA CLÉ POUR RÉDUIRE LA TAILLE ---
        self.right_column.addWidget(self.form_card) # On ajoute la carte
        self.right_column.addStretch() # On ajoute un ressort vide en dessous qui pousse la carte vers le haut
        
        # On ajoute la colonne au layout principal au lieu de la carte directement
        content_layout.addWidget(self.list_container, stretch=2)
        content_layout.addLayout(self.right_column, stretch=1)
        self.main_layout.addLayout(content_layout)

    def load_users(self):
        """Charge les profils dans la zone défilante"""
        try:
            # Nettoyer le layout actuel
            for i in reversed(range(self.scroll_layout.count() - 1)): 
                self.scroll_layout.itemAt(i).widget().setParent(None)

            response = requests.get(f"{self.api_url}/users/", headers=self.headers)
            if response.status_code == 200:
                for user in response.json():
                    row = UserRow(user['nom'], user['role'], self.delete_user)
                    self.scroll_layout.insertWidget(0, row) # Ajouter en haut
        except Exception as e:
            print(f"Erreur : {e}")

    def add_user(self):
        payload = {
            "nom": self.name_input.text(),
            "mot_de_passe": self.pass_input.text(),
            "role": self.role_combo.currentText()
        }
        res = requests.post(f"{self.api_url}/users/", json=payload, headers=self.headers)
        if res.status_code == 200:
            self.load_users()
            self.name_input.clear()
            self.pass_input.clear()

    def delete_user(self, nom):
        if QMessageBox.question(self, "Confirmer", f"Supprimer {nom} ?") == QMessageBox.StandardButton.Yes:
            requests.delete(f"{self.api_url}/users/{nom}", headers=self.headers)
            self.load_users()