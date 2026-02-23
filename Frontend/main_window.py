from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
    QStackedWidget, QLabel, QFrame, QMenu
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint

from user_manager import UserManager
from client_manager import ClientManager
from inventory_manager import InventoryManager
from stock_management import StockManagement
#from config import API_BASE_URL

class NavGroup(QWidget):
    """Widget pour un bouton principal avec des sous-items extensibles"""
    def __init__(self, icon, text, parent_sidebar):
        super().__init__()
        self.parent_sidebar = parent_sidebar
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

        # Bouton Principal
        self.btn_main = QPushButton(f"{icon}   {text}")
        self.btn_main.setObjectName("nav_btn_main")
        self.btn_main.setCheckable(True)
        self.btn_main.setStyleSheet(self.get_main_style())
        self.btn_main.clicked.connect(self.toggle_sub_menu)
        
        # Container des sous-menus
        self.sub_menu_container = QFrame()
        self.sub_menu_layout = QVBoxLayout(self.sub_menu_container)
        self.sub_menu_layout.setContentsMargins(35, 0, 0, 0) # Décalage à droite (le trait de l'image)
        self.sub_menu_layout.setSpacing(2)
        self.sub_menu_container.setVisible(False)

        self.layout.addWidget(self.btn_main)
        self.layout.addWidget(self.sub_menu_container)

    def add_sub_item(self, text, callback):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: none;
                border-left: 2px solid #E5E7EB; /* Ligne verticale comme sur l'image */
                color: #6B7280;
                font-size: 13px;
                background: transparent;
            }
            QPushButton:hover { color: #6366F1; border-left: 2px solid #6366F1; }
        """)
        btn.clicked.connect(callback)
        self.sub_menu_layout.addWidget(btn)
        return btn

    def toggle_sub_menu(self):
        is_visible = self.sub_menu_container.isVisible()
        self.sub_menu_container.setVisible(not is_visible)
        # On peut ajouter une flèche de rotation ici si on le souhaite

    def get_main_style(self):
        return """
            QPushButton {
                text-align: left;
                padding: 12px;
                border: none;
                border-radius: 8px;
                color: #374151;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #EEF2FF; color: #6366F1; }
            QPushButton:checked { background-color: #EEF2FF; color: #6366F1; }
        """

class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, token, role):
        super().__init__()
        self.token = token
        self.role = role
        self.is_collapsed = False
        self.sidebar_width_expanded = 260
        self.sidebar_width_collapsed = 70
        
        # On appelle l'initialisation de l'interface
        self.init_ui()
        
        # On charge la page par défaut APRES que init_ui ait créé le content_stack
        self.show_initial_page()

    def init_ui(self):
        """Construction de toute la structure FIXE (Sidebar + Zone de contenu)"""
        # --- 1. CONFIGURATION DU WIDGET CENTRAL ---
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QHBoxLayout(self.main_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --- 2. CONSTRUCTION DE LA SIDEBAR ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(self.sidebar_width_expanded)
        self.sidebar.setStyleSheet("background-color: #F8F9FA; border-right: 1px solid #E5E7EB;")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 20, 10, 20)

        # Bouton Menu Toggle (≡)
        self.btn_toggle = self.create_nav_btn("≡", "Menu", is_critical=True)
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        self.sidebar_layout.addWidget(self.btn_toggle)

        # --- SECTION OPÉRATIONS ---
        self.add_section_label("OPÉRATIONS")

        # Module Articles (Sous-menu)
        self.group_articles = NavGroup("📦", "Articles", self)
        self.group_articles.add_sub_item("Consulter Stock", self.go_to_inventory)
        self.group_articles.add_sub_item("Gestion des Stocks", self.go_to_stock_management)
        self.sidebar_layout.addWidget(self.group_articles)
        
        # Module Ventes (Sous-menu)
        self.group_ventes = NavGroup("🛒", "Ventes", self)
        self.group_ventes.add_sub_item("Nouveau BL", self.go_to_create_bl)
        self.group_ventes.add_sub_item("Consulter BL", self.go_to_consult_bl)
        self.sidebar_layout.addWidget(self.group_ventes)
        
        self.btn_facturation = self.create_nav_btn("📄", "Facturation")
        self.btn_facturation.clicked.connect(self.go_to_billing)
        self.sidebar_layout.addWidget(self.btn_facturation)

        # Bouton Apurement (Simple)
        self.btn_apurement = self.create_nav_btn("⏳", "Apurement")
        self.btn_apurement.clicked.connect(self.go_to_apurement)
        self.sidebar_layout.addWidget(self.btn_apurement)

        # --- SECTION GESTION ---
        self.sidebar_layout.addSpacing(20)
        self.add_section_label("GESTION")
        
        # Bouton Clients
        self.btn_clients = self.create_nav_btn("👥", "Clients")
        self.btn_clients.clicked.connect(self.go_to_clients)
        self.sidebar_layout.addWidget(self.btn_clients)
        
        # --- AJOUT DE LA SECTION ANALYSE (RESERVÉE AU GÉRANT) ---
        if self.role == "gerant":
            self.sidebar_layout.addSpacing(20)
            self.add_section_label("ANALYSE")
            
            self.btn_dashboard = self.create_nav_btn("📊", "Dashboard")
            self.btn_dashboard.clicked.connect(self.go_to_dashboard)
            self.sidebar_layout.addWidget(self.btn_dashboard)

        # --- BAS DE SIDEBAR (PARAMÈTRES) ---
        self.sidebar_layout.addStretch() # Pousse tout vers le haut
        
        self.btn_settings = self.create_nav_btn("⚙️", "Paramètres")
        self.btn_settings.clicked.connect(self.show_settings_menu)
        self.sidebar_layout.addWidget(self.btn_settings)

        # --- 3. ZONE DE CONTENU (STACKED WIDGET) ---
        self.content_stack = QStackedWidget() 
        
        # --- 4. ASSEMBLAGE FINAL ---
        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.content_stack)

    def show_page(self, widget):
        """Affiche dynamiquement un widget dans la zone centrale"""
        # On ajoute le nouveau widget au stack
        self.content_stack.addWidget(widget)
        # On demande au stack de l'afficher immédiatement
        self.content_stack.setCurrentWidget(widget)

    # --- MÉTHODES DE NAVIGATION ---
    def show_initial_page(self):
        self.go_to_inventory()
        
    def go_to_create_bl(self):
        from sales_management import BLManagement
        self.show_page(BLManagement(self.token))

    def go_to_consult_bl(self):
        from bl_consultation import BLConsultation # Import de votre nouveau fichier
        self.show_page(BLConsultation(self.token))


    # --- MÉTHODES UTILITAIRES ---
    def create_nav_btn(self, icon_text, full_text="", is_critical=False):
        btn = QPushButton()
        btn.full_text = full_text
        btn.icon_char = icon_text
        btn.setText(f"{icon_text}   {full_text}")
        weight = "bold" if is_critical else "normal"
        btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left; padding: 12px; border: none; border-radius: 8px;
                color: #374151; font-weight: {weight}; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #EEF2FF; color: #6366F1; }}
        """)
        return btn

    def add_section_label(self, text):
        label = QLabel(text)
        label.setObjectName("section_label")
        label.setStyleSheet("font-size: 10px; color: #9CA3AF; font-weight: bold; margin: 10px 0 5px 10px;")
        self.sidebar_layout.addWidget(label)

    def change_page(self, index):
        self.content_stack.setCurrentIndex(index)

    def toggle_sidebar(self):
        # ... (Gardez votre logique d'animation ici)
        # Note : Il faudra adapter le masquage des sous-menus lors du collapse
        width = self.sidebar.width()
        new_width = self.sidebar_width_collapsed if width == self.sidebar_width_expanded else self.sidebar_width_expanded
        self.is_collapsed = (new_width == self.sidebar_width_collapsed)

        self.animation = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(width)
        self.animation.setEndValue(new_width)
        self.animation.start()
        self.sidebar.setMaximumWidth(new_width)
        
        

         # Mettre à jour le texte des boutons
        for i in range(self.sidebar_layout.count()):
            widget = self.sidebar_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton) and hasattr(widget, 'full_text'):
                widget.setText(widget.icon_char if self.is_collapsed else f"{widget.icon_char}   {widget.full_text}")
            if isinstance(widget, QLabel) and widget.objectName() == "section_label":
                widget.setVisible(not self.is_collapsed)
            

    def logout(self):
        """Cette méthode est celle appelée par le bouton déconnexion"""
        self.logout_requested.emit() # On prévient le controller
        self.close() 

    def show_settings_menu(self):
        """Affiche le menu contextuel à droite de la sidebar avec un style moderne"""
        self.menu = QMenu(self)
        
        # Style ultra-moderne (couleurs plus douces, ombres simulées par la bordure)
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 8px 4px;
            }
            QMenu::item {
                padding: 10px 30px 10px 20px;
                border-radius: 8px;
                margin: 2px 4px;
                color: #4B5563;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #F3F4F6;
                color: #6366F1;
            }
            QMenu::separator {
                height: 1px;
                background: #F3F4F6;
                margin: 6px 10px;
            }
        """)

        # Actions
        if self.role == "gerant":
            action_users = QAction("🔐  Gérer Utilisateurs", self)
            action_users.triggered.connect(self.go_to_users)
            self.menu.addAction(action_users)
            self.menu.addSeparator()

        action_logout = QAction("🚪  Se déconnecter", self)
        action_logout.triggered.connect(self.logout)
        self.menu.addAction(action_logout)

        # POSITIONNEMENT : 
        # On récupère la position du coin haut-droit du bouton
        # On ajoute un offset de 10px à droite pour le "décoller" de la sidebar
        button_pos = self.btn_settings.mapToGlobal(self.btn_settings.rect().topRight())
        display_pos = button_pos + QPoint(10, 0)
        
        self.menu.exec(display_pos)
        
    def go_to_users(self):
        # On crée l'instance du module si elle n'existe pas
        self.user_manager_page = UserManager(self.token)
        
        # On l'ajoute au QStackedWidget (index 3 par exemple)
        self.content_stack.addWidget(self.user_manager_page)
        self.content_stack.setCurrentWidget(self.user_manager_page)
      
    

    # Dans MainWindow, connectez le bouton Clients :
    def go_to_clients(self):
        """Affiche le module de gestion des clients"""
        # 1. Créer l'instance du module Client
        self.client_page = ClientManager(self.token)
        
        # 2. L'ajouter au stack (le QStackedWidget qui contient vos pages)
        self.content_stack.addWidget(self.client_page)
        
        # 3. Changer la vue pour afficher cette page
        self.content_stack.setCurrentWidget(self.client_page)
        
        # optionnel : Mettre à jour le style du bouton pour montrer qu'il est actif
        #self.update_active_button(self.btn_clients)  

    def setup_initial_view(self):
        # Appelée juste après self.show() dans le contrôleur
        self.go_to_inventory()

    def go_to_inventory(self):
        """Affiche l'interface de consultation de stock"""
        self.inventory_page = InventoryManager(self.token, self.role)
        self.content_stack.addWidget(self.inventory_page)
        self.content_stack.setCurrentWidget(self.inventory_page)
        
    def go_to_stock_management(self):
        self.stock_mgmt_page = StockManagement(self.token, self.role) # On passe le role
        self.content_stack.addWidget(self.stock_mgmt_page)
        self.content_stack.setCurrentWidget(self.stock_mgmt_page)

    def go_to_create_bl(self):
        """Ouvre l'interface de création (votre fichier sales_management.py)"""
        from sales_management import BLManagement
        # On crée une nouvelle instance pour vider le formulaire à chaque fois
        page = BLManagement(self.token)
        self.content_stack.addWidget(page)
        self.content_stack.setCurrentWidget(page)

    def go_to_consult_bl(self):
        """Ouvre l'interface de liste/filtres (votre fichier bl_consultation.py)"""
        from bl_consultation import BLConsultation
        page = BLConsultation(self.token)
        self.content_stack.addWidget(page)
        self.content_stack.setCurrentWidget(page)
        
    def go_to_billing(self):
        from billing_manager import BillingManager
        self.billing_page = BillingManager(self.token)
        self.show_page(self.billing_page)
        
    def go_to_dashboard(self):
        from dashboard_manager import DashboardManager
        # On affiche le manager de dashboard (celui avec les deux cartes blanches)
        self.show_page(DashboardManager(self.token))
        
    def go_to_apurement(self):
        """Affiche le module d'apurement"""
        from apurement_manager import ApurementManager
        self.apurement_page = ApurementManager(self.token)
        self.content_stack.addWidget(self.apurement_page)
        self.content_stack.setCurrentWidget(self.apurement_page)
    
        