import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QGraphicsDropShadowEffect, QMessageBox, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from config import API_BASE_URL

class DashboardCard(QFrame):
    """Bouton stylisé sous forme de carte blanche avec ombre portée"""
    def __init__(self, title, icon_text, color="#6366F1", callback=None):
        super().__init__()
        self.setFixedSize(220, 240)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.callback = callback
        
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
            }
            QFrame:hover {
                background-color: #FBFBFF;
            }
        """)

        # Effet d'ombre
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet(f"font-size: 60px; color: {color}; margin-bottom: 10px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #1F2937;")
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)

    def mousePressEvent(self, event):
        if self.callback:
            self.callback()

class DashboardManager(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.api_url = API_BASE_URL
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(60, 60, 60, 60)
        
        header = QLabel("Tableau de Bord Analytique")
        header.setStyleSheet("font-size: 30px; font-weight: bold; color: #111827; margin-bottom: 40px;")
        self.main_layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)

        grid = QGridLayout()
        grid.setSpacing(50)

        # Carte Finance (Icône % comme dans l'image)
        self.card_finance = DashboardCard(
            "Situation Financière", "٪", "#6366F1", 
            callback=self.open_finance
        )
        """
        # Carte Clients (Icône Groupe)
        self.card_profit = DashboardCard(
            "Rentabilité Clients", "👥", "#10B981", 
            callback=self.open_profitability
        )
"""
        grid.addWidget(self.card_finance, 0, 0)
       # grid.addWidget(self.card_profit, 0, 1)

        self.main_layout.addLayout(grid)
        
        # Bouton de synchronisation
        self.btn_sync = QPushButton("🔄 Recalculer les statistiques")
        self.btn_sync.setStyleSheet("""
            QPushButton { 
                margin-top: 40px; padding: 12px 25px; border-radius: 8px;
                background-color: #F3F4F6; border: 1px solid #D1D5DB; font-weight: 500;
            }
            QPushButton:hover { background-color: #E5E7EB; }
        """)
        self.btn_sync.clicked.connect(self.sync_stats)
        self.main_layout.addWidget(self.btn_sync, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addStretch()

    def sync_stats(self):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            requests.get(f"{self.api_url}/dashboard/populate", headers=headers)
            QMessageBox.information(self, "Succès", "Données mises à jour.")
        except:
            QMessageBox.critical(self, "Erreur", "Connexion au serveur échouée.")

    def open_finance(self):
        from dashboard_stats import FinanceStatsWindow
        self.win_f = FinanceStatsWindow(self.token)
        self.win_f.show()

"""
    def open_profitability(self):
        from dashboard_stats import ClientStatsWindow
        self.win_p = ClientStatsWindow(self.token)
        self.win_p.show()
        """