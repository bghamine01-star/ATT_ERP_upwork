import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QAbstractItemView, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from config import API_BASE_URL

# --- WORKER THREAD (Performance) ---
class ApiWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url, params, headers):
        super().__init__()
        self.url = url
        self.params = params
        self.headers = headers

    def run(self):
        try:
            response = requests.get(self.url, params=self.params, headers=self.headers, timeout=5)
            if response.status_code == 200:
                self.finished.emit(response.json())
            else:
                self.error.emit(f"Erreur {response.status_code}")
        except Exception as e:
            self.error.emit(str(e))

# --- CLASSE PRINCIPALE (Visuel Rétabli) ---
class InventoryManager(QWidget):
    def __init__(self, token, role):
        super().__init__()
        self.token = token
        self.role = role
        self.api_url = API_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Cache Graphique
        self.red_color = QColor("#EF4444")
        self.green_bg = QColor("#F0FDF4")
        self.success_bg = QColor("#DCFCE7")
        self.grey_text = QColor("#6B7280")
        self.bold_font = QFont(); self.bold_font.setBold(True)
        self.italic_font = QFont(); self.italic_font.setItalic(True)

        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.init_ui()
        self.load_initial_data()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 30, 40, 30)
        self.layout.setSpacing(20)

        # Header
        title = QLabel("Consultation du Stock")
        title.setStyleSheet("font-size: 28px; font-weight: 600; color: #111827; letter-spacing: -0.02em;")
        self.layout.addWidget(title)

        # Barre de recherche (Ancien visuel rétabli)
        search_container = QFrame()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(15)

        input_style = """
            QLineEdit {
                padding: 10px 15px; border-radius: 8px;
                border: 1px solid #D1D5DB; background-color: white;
                font-size: 13px; min-width: 250px;
            }
            QLineEdit:focus { border: 2px solid #6366F1; }
        """
        
        self.search_ref = QLineEdit()
        self.search_ref.setPlaceholderText("Filtrer par Référence...")
        self.search_ref.setStyleSheet(input_style)
        self.search_ref.textChanged.connect(self.on_input_changed)
        
        self.search_name = QLineEdit()
        self.search_name.setPlaceholderText("Filtrer par Désignation")
        self.search_name.setStyleSheet(input_style)
        self.search_name.textChanged.connect(self.on_input_changed)

        self.btn_export = QPushButton("📥 Exporter CSV")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white; border-radius: 8px;
                padding: 10px 20px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_export.clicked.connect(self.export_to_csv)

        search_layout.addWidget(QLabel("Référence:"))
        search_layout.addWidget(self.search_ref)
        search_layout.addSpacing(20)
        search_layout.addWidget(QLabel("Désignation:"))
        search_layout.addWidget(self.search_name)
        search_layout.addStretch()
        search_layout.addWidget(self.btn_export)
        self.layout.addWidget(search_container)

        # Tableau (Ancien visuel rétabli)
        self.table_container = QFrame()
        self.table_container.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #E5E7EB;")
        table_layout = QVBoxLayout(self.table_container)
        
        self.stock_table = QTableWidget()
        self.stock_table.verticalHeader().setVisible(False)
        self.stock_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.stock_table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #F3F4F6; }
            QHeaderView::section { 
                background-color: white; padding: 12px; border: none;
                border-bottom: 2px solid #E5E7EB; font-weight: bold; color: #6B7280; font-size: 11px;
            }
        """)
        
        table_layout.addWidget(self.stock_table)
        self.layout.addWidget(self.table_container)

    def on_input_changed(self):
        self.search_timer.stop()
        self.search_timer.start(400)

    def load_initial_data(self):
        self.show_placeholder_message("Saisissez une référence ou une désignation pour afficher les articles.")

    def show_placeholder_message(self, message):
        """Affiche un message stylisé qui occupe tout le tableau."""
        self.stock_table.blockSignals(True)
        self.stock_table.clearSpans()
        
        headers = ["RÉFÉRENCE", "DÉSIGNATION", "CATÉGORIE", "EMPLACEMENT", "PRIX VENTE", "STOCK"]
        if self.role == "gerant": headers.append("PRIX ACHAT")
        
        self.stock_table.setColumnCount(len(headers))
        self.stock_table.setHorizontalHeaderLabels(headers)
        self.stock_table.setRowCount(1)
        self.stock_table.setSpan(0, 0, 1, len(headers))
        
        item = QTableWidgetItem(message)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setForeground(self.grey_text)
        item.setFont(self.italic_font)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.stock_table.setItem(0, 0, item)
        
        self.apply_header_styles()
        self.stock_table.blockSignals(False)

    def apply_header_styles(self):
        header = self.stock_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        if self.stock_table.columnCount() >= 6:
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            self.stock_table.setColumnWidth(4, 100) # Prix Vente
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
            self.stock_table.setColumnWidth(5, 80)  # Stock

    def perform_search(self):
        name = self.search_name.text().strip()
        ref = self.search_ref.text().strip()
        
        if not name and not ref:
            self.load_initial_data()
            return

        params = {'reference': ref, 'designation': name}
        self.worker = ApiWorker(f"{self.api_url}/articles/search_v2", params, self.headers)
        self.worker.finished.connect(self.handle_search_results)
        self.worker.error.connect(lambda e: self.show_placeholder_message(f"Erreur: {e}"))
        self.worker.start()

    def handle_search_results(self, articles):
        if not articles:
            self.show_placeholder_message("Aucun article ne correspond à votre recherche.")
        else:
            self.display_articles(articles)

    def display_articles(self, articles):
        self.stock_table.blockSignals(True)
        self.stock_table.clearSpans()
        
        is_gerant = (self.role == "gerant")
        headers = ["RÉFÉRENCE", "DÉSIGNATION", "CATÉGORIE", "EMPLACEMENT", "PRIX VENTE", "STOCK"]
        if is_gerant: headers.append("PRIX ACHAT")
            
        self.stock_table.setColumnCount(len(headers))
        self.stock_table.setHorizontalHeaderLabels(headers)
        self.stock_table.setRowCount(len(articles))

        for row_idx, art in enumerate(articles):
            ref_item = QTableWidgetItem(str(art.get('reference', '')))
            ref_item.setData(Qt.ItemDataRole.UserRole, art.get('id_article'))
            
            qty = int(art.get('quantite_disponible', 0))
            
            row_items = [
                ref_item,
                QTableWidgetItem(str(art.get('nom_article', ''))),
                QTableWidgetItem(str(art.get('categorie', '') or "N/A")),
                QTableWidgetItem(str(art.get('emplacement', '') or "N/A")),
                QTableWidgetItem(f"{float(art.get('prix_vente', 0)):.2f}"),
                QTableWidgetItem(str(qty))
            ]

            if is_gerant:
                pa = float(art.get('prix_achat', 0) if art.get('prix_achat') else 0)
                pa_item = QTableWidgetItem(f"{pa:.2f}")
                pa_item.setBackground(self.green_bg)
                row_items.append(pa_item)

            for col_idx, item in enumerate(row_items):
                if col_idx == 5: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if qty <= 0:
                    item.setForeground(self.red_color)
                    item.setFont(self.bold_font)
                
                # Droits d'édition
                if is_gerant and col_idx == 6:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    # On reconnecte le signal seulement quand on est en mode édition
                    try: self.stock_table.itemChanged.disconnect()
                    except: pass
                    self.stock_table.itemChanged.connect(self.on_item_changed)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

                self.stock_table.setItem(row_idx, col_idx, item)

        self.apply_header_styles()
        self.stock_table.blockSignals(False)

    def on_item_changed(self, item):
        # On ne réagit que si c'est la colonne du PRIX ACHAT (index 6)
        if item.column() == 6:
            row = item.row()
            # Sécurité : vérifier que l'ID de l'article est présent
            id_item = self.stock_table.item(row, 0)
            if not id_item: return
            
            article_id = id_item.data(Qt.ItemDataRole.UserRole)
            
            try:
                # 1. Nettoyage et validation du prix
                raw_text = item.text().replace(',', '.').strip()
                if not raw_text: return # Évite de traiter si la case est vidée par erreur
                
                new_val = float(raw_text)
                
                # 2. Sécurité : Empêcher les prix négatifs avant l'envoi
                if new_val < 0:
                    QMessageBox.warning(self, "Erreur", "Le prix d'achat ne peut pas être négatif.")
                    self.perform_search() # On recharge pour annuler visuellement la saisie
                    return

                # 3. Appel API
                res = requests.put(
                    f"{self.api_url}/articles/{article_id}/prix_achat", 
                    json={"prix_achat": new_val}, 
                    headers=self.headers, 
                    timeout=5
                )

                if res.status_code == 200:
                    # IMPORTANT : Bloquer les signaux pendant qu'on change le visuel
                    self.stock_table.blockSignals(True)
                    item.setBackground(self.success_bg) # Confirmation visuelle (vert clair)
                    item.setText(f"{new_val:.2f}")      # Formatage propre
                    self.stock_table.blockSignals(False)
                else:
                    # Si le serveur refuse (ex: 404 ou 422)
                    QMessageBox.warning(self, "Erreur Serveur", f"Impossible de mettre à jour : {res.text}")
                    self.perform_search() # On remet la valeur d'origine

            except ValueError:
                # En cas de saisie de texte au lieu d'un nombre
                QMessageBox.warning(self, "Format Invalide", "Veuillez saisir un nombre valide.")
                self.perform_search() 
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Problème de connexion : {str(e)}")
                self.perform_search()

    def export_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export", f"Stock_{datetime.now().strftime('%Y%m%d')}.csv", "CSV (*.csv)")
        if file_path:
            try:
                res = requests.get(f"{self.api_url}/articles/export/csv", headers=self.headers, timeout=10)
                if res.status_code == 200:
                    with open(file_path, 'wb') as f: f.write(res.content)
                    QMessageBox.information(self, "Succès", "Exportation terminée.")
            except: pass