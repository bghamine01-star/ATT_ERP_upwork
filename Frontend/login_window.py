import sys
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from config import API_BASE_URL
class LoginWindow(QWidget):
    # Signal envoyé quand la connexion réussit (transmet le token et le rôle)
    login_success = pyqtSignal(str, str) 

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connexion - ATT")
        self.setFixedSize(400, 500)
        self.setStyleSheet("background-color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        # Logo / Titre
        self.title = QLabel("Bienvenue")
        self.title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1F2937;")
        self.subtitle = QLabel("Connectez-vous à votre espace")
        self.subtitle.setStyleSheet("color: #6B7280; margin-bottom: 20px;")
        
        # Champs
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        # --- NOUVEAU : On connecte la touche Entrée sur les champs ---
        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)

        style_input = """
            QLineEdit {
                padding: 12px;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #F9FAFB;
            }
            QLineEdit:focus { border: 2px solid #6366F1; }
        """
        self.username_input.setStyleSheet(style_input)
        self.password_input.setStyleSheet(style_input)

        # Bouton Connexion
        self.login_btn = QPushButton("Se connecter")
        # Rendre le bouton réactif à la touche Entrée
        self.login_btn.setDefault(True)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #4F46E5; }
        """)
        self.login_btn.clicked.connect(self.handle_login)

        layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addSpacing(10)
        layout.addWidget(self.login_btn)
        layout.addStretch()
        

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # Correspond à votre route /token/
        payload = {"username": username, "password": password}
        try:
            response = requests.post(f"{API_BASE_URL}/token/", data=payload, timeout=20)
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                role = data["user_role"]
                self.login_success.emit(token, role)
            else:
                QMessageBox.warning(self, "Erreur", "Identifiants incorrects")
        except requests.exceptions.ConnectTimeout:
            print("Erreur : Le serveur Azure met trop de temps à répondre.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de contacter le serveur: {e}")