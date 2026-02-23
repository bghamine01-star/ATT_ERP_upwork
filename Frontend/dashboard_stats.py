import requests
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from config import API_BASE_URL

# --- CONFIGURATION DU STYLE MATPLOTLIB ---
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class StatCard(QFrame):
    """Carte KPI avec indicateur de couleur vertical et ombre douce"""
    def __init__(self, title, value, accent_color="#6366F1"):
        super().__init__()
        self.setMinimumHeight(120)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E5E7EB;
            }}
        """)
        
        # Ombre portée élégante
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 20, 0)

        # Barre d'accentuation à gauche
        self.accent_bar = QFrame()
        self.accent_bar.setFixedWidth(6)
        self.accent_bar.setStyleSheet(f"background-color: {accent_color}; border-top-left-radius: 12px; border-bottom-left-radius: 12px; border: none;")
        
        # Conteneur de texte
        text_container = QVBoxLayout()
        text_container.setContentsMargins(20, 15, 10, 15)
        
        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; border: none;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("color: #1F2937; font-size: 24px; font-weight: 800; border: none;")
        
        text_container.addWidget(self.lbl_title)
        text_container.addWidget(self.lbl_value)
        
        layout.addWidget(self.accent_bar)
        layout.addLayout(text_container)
        layout.addStretch()

    def update_value(self, text):
        self.lbl_value.setText(text)

class FinanceStatsWindow(QMainWindow):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.api_url = API_BASE_URL
        self.setWindowTitle("Tableau de Bord Financier")
        self.resize(1200, 850)
        self.setStyleSheet("background-color: #F8FAFC;") # Fond légèrement bleuté/gris
        
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(40, 30, 40, 40)
        self.main_layout.setSpacing(25)

        # --- HEADER ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_vbox = QVBoxLayout()
        header_title = QLabel("Vue d'ensemble Financière")
        header_title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A;")
        header_subtitle = QLabel("Suivi du Chiffre d'Affaires et de la rentabilité")
        header_subtitle.setStyleSheet("font-size: 14px; color: #64748B;")
        title_vbox.addWidget(header_title)
        title_vbox.addWidget(header_subtitle)

        self.combo_year = QComboBox()
        self.combo_year.addItems([str(y) for y in range(2024, 2031)])
        self.combo_year.setCurrentText("2025")
        self.combo_year.setFixedSize(120, 40)
        self.combo_year.setStyleSheet("""
            QComboBox { 
                padding-left: 15px; border-radius: 10px; border: 1px solid #CBD5E1; 
                background: white; font-weight: 600; color: #334155;
            }
            QComboBox::drop-down { border: none; width: 30px; }
        """)
        self.combo_year.currentTextChanged.connect(self.load_data)

        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        header_layout.addWidget(self.combo_year)
        self.main_layout.addWidget(header_widget)

        # --- CARDS KPI ---
        self.cards_layout = QHBoxLayout()
        self.card_ca = StatCard("Chiffre d'Affaires", "0.000 DT", "#6366F1") # Indigo
        self.card_marge = StatCard("Marge Brute", "0.000 DT", "#10B981")    # Emeraude
        self.card_panier = StatCard("Panier Moyen", "0.000 DT", "#F59E0B")   # Ambre
        
        self.cards_layout.addWidget(self.card_ca)
        self.cards_layout.addWidget(self.card_marge)
        self.cards_layout.addWidget(self.card_panier)
        self.main_layout.addLayout(self.cards_layout)

        # --- ZONE GRAPHIQUE ---
        self.graph_frame = QFrame()
        self.graph_frame.setStyleSheet("""
            QFrame {
                background-color: white; 
                border-radius: 20px; 
                border: 1px solid #E2E8F0;
            }
        """)
        graph_vbox = QVBoxLayout(self.graph_frame)
        graph_vbox.setContentsMargins(20, 20, 20, 20)
        
        # Création de la figure avec un fond transparent/blanc
        self.fig = Figure(figsize=(10, 5), facecolor='none')
        self.canvas = FigureCanvas(self.fig)
        graph_vbox.addWidget(self.canvas)
        self.main_layout.addWidget(self.graph_frame)
        
        # Ajout d'une variable pour stocker les points du graphique pour l'interactivité
        self.line_plot = None
        self.annot = None

        self.load_data()

    def load_data(self):
        year = self.combo_year.currentText()
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 1. Récupération KPIs
            res_y = requests.get(f"{self.api_url}/dashboard/yearly-revenue", params={"annee": year}, headers=headers).json()
            self.card_ca.update_value(f"{res_y['total_revenue']:,.3f} DT".replace(",", " "))
            self.card_marge.update_value(f"{res_y['total_gross_margin']:,.3f} DT".replace(",", " "))
            self.card_panier.update_value(f"{res_y['average_cart']:,.3f} DT".replace(",", " "))

            # 2. Récupération Graphique
            res_m = requests.get(f"{self.api_url}/dashboard/monthly-revenue/{year}", headers=headers).json()
            
            months_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
            revs = [0.0] * 12
            for r in res_m:
                revs[r['month'] - 1] = float(r['revenue'])
            
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            
           # Stylisation de la courbe
            self.line_plot, = ax.plot(months_names, revs, color="#4F46E5", linewidth=4, marker='o', 
                                    markersize=8, markerfacecolor='white', markeredgewidth=2, zorder=3)
            
            ax.fill_between(months_names, revs, color="#6366F1", alpha=0.12, zorder=2)
            
            # Grille et axes
            ax.yaxis.grid(True, linestyle='--', which='major', color='#F1F5F9', alpha=0.8)
            ax.set_axisbelow(True)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_color('#E2E8F0')
            
            ax.tick_params(axis='both', which='major', labelsize=10, colors='#64748B')
            
            # --- AJOUT DE L'ANNOTATION (L'infobulle) ---
            self.annot = ax.annotate("", xy=(0,0), xytext=(10,10),
                                    textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="white", ec="#4F46E5", lw=1),
                                    arrowprops=dict(arrowstyle="->", color="#4F46E5"),
                                    fontsize=10, fontweight='bold')
            self.annot.set_visible(False)

            # Connexion de l'événement de mouvement de souris
            self.canvas.mpl_connect("motion_notify_event", self.hover)

            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"Erreur Dashboard: {e}")
            
    def update_annot(self, ind):
        """Met à jour le texte et la position de l'infobulle pour une Line2D"""
        # Récupérer l'index du point survolé
        idx = ind["ind"][0]
        
        # Récupérer les données X et Y de la ligne
        xdata, ydata = self.line_plot.get_data()
        
        # Définir la position de l'infobulle sur le point exact
        self.annot.xy = (xdata[idx], ydata[idx])
        
        # Formater le texte avec la valeur Y
        y_val = ydata[idx]
        text = f"{y_val:,.3f} DT".replace(",", " ")
        
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.9)

    def hover(self, event):
        """Détecte si la souris survole un point de la courbe"""
        vis = self.annot.get_visible()
        if event.inaxes == self.fig.axes[0]:
            # Vérifier si la souris est sur la ligne
            cont, ind = self.line_plot.contains(event)
            if cont:
                self.update_annot(ind)
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.canvas.draw_idle()
"""            
class ClientStatsWindow(QMainWindow):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.api_url = API_BASE_URL
        self.setWindowTitle("Rentabilité par Client")
        self.resize(1000, 750)
        self.setStyleSheet("background-color: #F9FAFB;")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 20, 30, 30)

        # Header
        top = QHBoxLayout()
        title = QLabel("Classement des Clients")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #111827;")
        
        self.combo_year = QComboBox()
        self.combo_year.addItems([str(y) for y in range(2024, 2031)])
        self.combo_year.currentTextChanged.connect(self.load_data)
        
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.combo_year)
        layout.addLayout(top)

        # Graphique
        self.graph_frame = QFrame()
        self.graph_frame.setStyleSheet("background-color: white; border-radius: 15px; border: 1px solid #F3F4F6;")
        v_graph = QVBoxLayout(self.graph_frame)
        self.canvas = FigureCanvas(Figure(figsize=(7, 5)))
        v_graph.addWidget(self.canvas)
        layout.addWidget(self.graph_frame)

        self.load_data()
        
    def load_data(self):
        year = self.combo_year.currentText()
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            resp = requests.get(
                f"{self.api_url}/dashboard/client-profitability",
                params={"annee": year},
                headers=headers
            ).json()

            top_7 = resp[:7]  # plus proche du rendu de l’image
            names = [c['client_name'] for c in top_7]
            margins = [float(c['total_gross_margin']) for c in top_7]

            self.canvas.figure.clear()
            ax = self.canvas.figure.add_subplot(111)

            # Couleurs : une barre mise en avant
            main_color = "#4F46E5"      # indigo
            faded_color = "#E0E7FF"     # indigo clair

            max_index = margins.index(max(margins))
            colors = [
                main_color if i == max_index else faded_color
                for i in range(len(margins))
            ]

            bars = ax.bar(
                range(len(names)),
                margins,
                color=colors,
                width=0.6
            )

            # Valeurs au-dessus des barres
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + max(margins) * 0.03,
                    f"{height:,.0f} DT".replace(",", " "),
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                    color="#111827" if i == max_index else "#6B7280"
                )

            # Labels clients
            ax.set_xticks(range(len(names)))
            ax.set_xticklabels(names, rotation=0, fontsize=10)

            # Nettoyage total des axes (style dashboard)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.yaxis.set_visible(False)
            ax.grid(False)

            ax.set_title(
                "Top Clients par Marge",
                fontsize=14,
                fontweight="bold",
                color="#111827",
                pad=20
            )

            self.canvas.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print("Erreur ClientStats:", e)

"""