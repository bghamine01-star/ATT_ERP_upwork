import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, 
    QScrollArea, QHBoxLayout, QLineEdit, QDateEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from config import API_BASE_URL

class ManagementBanner(QFrame):
    def __init__(self, title, icon, color="#6366F1"):
        super().__init__()
        self.setStyleSheet("""
            QFrame#Banner {
                background-color: white; border: 1px solid #E5E7EB; border-radius: 12px;
            }
        """)
        self.setObjectName("Banner")
        self.layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        self.title_label = QLabel(f"{icon}  {title}")
        self.title_label.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {color};")
        
        self.btn_toggle = QPushButton("Ouvrir l'outil")
        self.btn_toggle.setFixedWidth(110)
        self.btn_toggle.setStyleSheet("QPushButton { background-color: #F3F4F6; border-radius: 6px; padding: 6px; font-size: 12px; }")

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_toggle)
        self.layout.addLayout(header_layout)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_widget.setVisible(False)
        self.layout.addWidget(self.content_widget)

        self.btn_toggle.clicked.connect(self.toggle_content)

    def toggle_content(self):
        is_visible = self.content_widget.isVisible()
        self.content_widget.setVisible(not is_visible)
        self.btn_toggle.setText("Fermer" if not is_visible else "Ouvrir l'outil")

class StockManagement(QWidget):
    def __init__(self, token, role):
        super().__init__()
        self.token = token
        self.role = role
        self.api_url = API_BASE_URL
        self.container_layout = None
        self.init_ui()
        

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Gestion des Mouvements de Stock")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #111827; margin-bottom: 10px;")
        self.main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        self.container_layout = QVBoxLayout(container)
        self.container_layout.setSpacing(20)

        # --- SECTION 1 : AJOUT ---
        self.banner_add = ManagementBanner("Importer un nouveau Lot SE", "📥", "#10B981")
        self.setup_add_form()
        self.container_layout.addWidget(self.banner_add)

        # --- SECTION 2 : UPDATE (À remplir plus tard) ---
        self.banner_update = ManagementBanner("Modifier un article existant", "📝", "#6366F1")
        self.setup_update_form()
        self.container_layout.addWidget(self.banner_update)

        # --- SECTION 3 : DELETE (À remplir plus tard) ---
        self.banner_delete = ManagementBanner("Supprimer un Lot SE", "🗑️", "#EF4444")
        self.setup_delete_form()
        self.container_layout.addWidget(self.banner_delete)
        
        # --- SECTION 4 : PRIX D'ACHAT (GÉRANT UNIQUEMENT) ---
        # On appelle la méthode ici, elle vérifiera elle-même le rôle
        self.setup_purchase_price_section(self.role)

        self.container_layout.addStretch()
        scroll.setWidget(container)
        self.main_layout.addWidget(scroll)
        

    def setup_add_form(self):
        layout = self.banner_add.content_layout
        
        # Formulaire Header
        form_grid = QHBoxLayout()
        self.input_num_se = QLineEdit(); self.input_num_se.setPlaceholderText("N° SE")
        self.input_date = QDateEdit(QDate.currentDate()); self.input_date.setCalendarPopup(True)
        self.input_vendor = QLineEdit(); self.input_vendor.setPlaceholderText("Fournisseur")
        
        form_grid.addWidget(QLabel("N° SE:")); form_grid.addWidget(self.input_num_se)
        form_grid.addWidget(QLabel("Date:")); form_grid.addWidget(self.input_date)
        form_grid.addWidget(QLabel("Fournisseur:")); form_grid.addWidget(self.input_vendor)
        layout.addLayout(form_grid)

        # Tableau des articles
        self.add_table = QTableWidget(1, 6)
        self.add_table.setHorizontalHeaderLabels(["Référence", "Désignation", "Catégorie", "Emplacement", "Prix Vente", "Quantité"])
        self.add_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # AJOUT : On connecte le signal de changement de cellule
        self.add_table.cellChanged.connect(self.on_reference_changed)
        layout.addWidget(self.add_table)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_add_row = QPushButton("+ Ligne"); btn_add_row.clicked.connect(lambda: self.add_table.insertRow(self.add_table.rowCount()))
        # --- NOUVEAU BOUTON SUPPRIMER ---
        btn_del_row = QPushButton("- Supprimer Ligne")
        btn_del_row.setStyleSheet("color: #EF4444;") # Rouge
        btn_del_row.clicked.connect(self.remove_selected_row)
        self.btn_submit = QPushButton("🚀 Valider l'importation")
        self.btn_submit.setStyleSheet("background-color: #10B981; color: white; padding: 10px; font-weight: bold; border-radius: 6px;")
        self.btn_submit.clicked.connect(self.submit_data)
        
        btn_layout.addWidget(btn_add_row); btn_layout.addWidget(btn_del_row); btn_layout.addStretch(); btn_layout.addWidget(self.btn_submit)
        layout.addLayout(btn_layout)
        
    def remove_selected_row(self):
        """Supprime la ligne actuellement sélectionnée"""
        current_row = self.add_table.currentRow()
        if current_row >= 0:
            self.add_table.removeRow(current_row)
        else:
            QMessageBox.information(self, "Info", "Veuillez cliquer sur une ligne pour la supprimer.")



    def submit_data(self):
        # Reset des couleurs du tableau avant de valider
        for r in range(self.add_table.rowCount()):
            for c in range(self.add_table.columnCount()):
                item = self.add_table.item(r, c)
                if item:
                    item.setBackground(QColor("white"))

        num_se = self.input_num_se.text().strip()
        if not num_se:
            QMessageBox.warning(self, "Données manquantes", "Le N° SE est obligatoire.")
            return

        articles = []
        has_error = False

        for row in range(self.add_table.rowCount()):
            # On récupère les items (attention, ils peuvent être None si jamais touchés)
            items = [self.add_table.item(row, col) for col in range(6)]
            
            # Extraction des textes avec sécurité
            ref = items[0].text().strip() if items[0] else ""
            nom = items[1].text().strip() if items[1] else ""
            prix_txt = items[4].text().strip() if items[4] else ""
            qte_txt = items[5].text().strip() if items[5] else ""

            # --- VALIDATION STRICTE ---
            line_error = False
            
            # 1. Vérifier si la ligne est totalement vide (on l'ignore simplement)
            if not any([ref, nom, prix_txt, qte_txt]):
                continue

            # 2. Vérifier les champs obligatoires
            if not ref: self.mark_error(row, 0); line_error = True
            if not nom: self.mark_error(row, 1); line_error = True
            
            # 3. Vérifier le Prix (doit être float > 0)
            try:
                prix = float(prix_txt.replace(',', '.'))
                if prix <= 0: raise ValueError()
            except ValueError:
                self.mark_error(row, 4)
                line_error = True

            # 4. Vérifier la Quantité (doit être int >= 0 et NON VIDE)
            try:
                if qte_txt == "": raise ValueError() # Force l'erreur si vide
                qte = int(qte_txt)
                if qte < 0: raise ValueError()
            except ValueError:
                self.mark_error(row, 5)
                line_error = True

            if line_error:
                has_error = True
                continue

            articles.append({
                "reference": ref,
                "nom_article": nom,
                "categorie": items[2].text() if items[2] else "",
                "emplacement": items[3].text() if items[3] else "",
                "prix_vente": prix,
                "quantite_dans_stock": qte
            })

        if has_error:
            QMessageBox.warning(self, "Erreur de saisie", "Certaines cases (en rouge) sont invalides ou vides.")
            return

        if not articles:
            QMessageBox.warning(self, "Tableau vide", "Veuillez saisir au moins un article complet.")
            return


        # 4. Envoi à l'API (Inchangé)
        payload = {
            "numero_se": num_se,
            "date_importation": self.input_date.date().toString("yyyy-MM-dd"),
            "fournisseur": self.input_vendor.text(),
            "articles": articles
        }

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            res = requests.post(f"{self.api_url}/stock_se/", json=payload, headers=headers)
            if res.status_code == 200:
                QMessageBox.information(self, "Succès", "Stock SE créé avec succès !")
                
                # --- RAFAICHISSEMENT ICI ---
                self.reset_add_form()
                #self.banner_add.toggle_content() # Fermer la bannière
            else:
                QMessageBox.warning(self, "Erreur", f"Erreur serveur: {res.text}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            
    def mark_error(self, row, col):
        """Colorie la cellule en rouge clair pour indiquer une erreur"""
        item = self.add_table.item(row, col)
        if not item: # Si la cellule était vide, on crée un item pour pouvoir le colorer
            item = QTableWidgetItem("")
            self.add_table.setItem(row, col, item)
        item.setBackground(QColor("#FFCCCC"))
            
    def setup_update_form(self):
        layout = self.banner_update.content_layout
        
        # --- Zone de recherche (Le sélecteur) ---
        search_layout = QHBoxLayout()
        self.upd_search_num_se = QLineEdit()
        self.upd_search_num_se.setPlaceholderText("N° SE")
        self.upd_search_ref = QLineEdit()
        self.upd_search_ref.setPlaceholderText("Référence Article")
        
        btn_load = QPushButton("🔍 Charger l'article")
        btn_load.clicked.connect(self.load_article_for_update)
        btn_load.setStyleSheet("background-color: #6366F1; color: white; border-radius: 4px; padding: 5px 15px;")

        search_layout.addWidget(QLabel("Cible :"))
        search_layout.addWidget(self.upd_search_num_se)
        search_layout.addWidget(self.upd_search_ref)
        search_layout.addWidget(btn_load)
        layout.addLayout(search_layout)

        # --- Zone du formulaire (Champs modifiables) ---
        # On utilise un style de "grille" pour la clarté
        self.upd_form_container = QFrame()
        self.upd_form_container.setEnabled(False) # Désactivé tant qu'on n'a pas chargé d'article
        form_layout = QVBoxLayout(self.upd_form_container)

        self.upd_name = QLineEdit()
        self.upd_cat = QLineEdit()
        self.upd_loc = QLineEdit()
        self.upd_price = QLineEdit()
        self.upd_vendor = QLineEdit()

        # Labels et inputs
        fields = [
            ("Désignation Article:", self.upd_name),
            ("Catégorie:", self.upd_cat),
            ("Emplacement:", self.upd_loc),
            ("Prix de Vente:", self.upd_price),
            ("Fournisseur (Stock):", self.upd_vendor)
        ]

        for label_text, widget in fields:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(130)
            row.addWidget(lbl)
            row.addWidget(widget)
            form_layout.addLayout(row)

        self.btn_save_upd = QPushButton("💾 Enregistrer les modifications")
        self.btn_save_upd.clicked.connect(self.submit_update)
        self.btn_save_upd.setStyleSheet("""
            QPushButton { background-color: #6366F1; color: white; font-weight: bold; padding: 10px; border-radius: 6px; margin-top: 10px; }
            QPushButton:hover { background-color: #4F46E5; }
        """)
        form_layout.addWidget(self.btn_save_upd)
        
        layout.addWidget(self.upd_form_container)
    
    def reset_add_form(self):
        """Remet à zéro le formulaire d'ajout après un succès"""
        # 1. Vider les inputs du header
        self.input_num_se.clear()
        self.input_vendor.clear()
        self.input_date.setDate(QDate.currentDate())
        
        # 2. Réinitialiser le tableau
        self.add_table.setRowCount(0) # On supprime tout
        self.add_table.insertRow(0)   # On remet une ligne vide propre
        
        # 3. Optionnel : Redonner le focus au premier champ
        self.input_num_se.setFocus()
        
    def load_article_for_update(self):
        """Charge TOUTES les données de l'article pour modification"""
        num_se = self.upd_search_num_se.text().strip()
        ref = self.upd_search_ref.text().strip()
        
        if not num_se or not ref:
            QMessageBox.warning(self, "Champs manquants", "Veuillez saisir le N° SE et la Référence.")
            return

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            res_se = requests.get(f"{self.api_url}/stock_se/details/{num_se}", headers=headers)
            
            if res_se.status_code == 200:
                data_se = res_se.json()
                
                # On cherche l'article dans la liste
                articles_list = data_se.get('articles', [])
                article_data = next((a for a in articles_list if a['reference'] == ref), None)
                
                if article_data:
                    # Remplissage de TOUS les champs
                    # On utilise .get() avec des valeurs par défaut pour éviter les erreurs
                    self.upd_name.setText(str(article_data.get('nom_article', '')))
                    self.upd_cat.setText(str(article_data.get('categorie', '') or ''))
                    self.upd_loc.setText(str(article_data.get('emplacement', '') or ''))
                    self.upd_vendor.setText(str(data_se.get('fournisseur', '')))
                    
                    # Gestion précise du prix
                    # Vérifie si la clé est bien 'prix_vente' dans ton modèle Pydantic/SQLAlchemy
                    prix = article_data.get('prix_vente')
                    if prix is not None:
                        self.upd_price.setText(str(prix))
                    else:
                        self.upd_price.setText("0")

                    # Activer le formulaire
                    self.upd_form_container.setEnabled(True)
                    self.upd_form_container.setStyleSheet("QFrame { background-color: #ffffff; }")
                else:
                    QMessageBox.warning(self, "Introuvable", f"L'article '{ref}' n'existe pas dans le lot '{num_se}'.")
                    self.upd_form_container.setEnabled(False)
            else:
                QMessageBox.warning(self, "Erreur SE", f"Le lot SE '{num_se}' n'existe pas.")
                self.upd_form_container.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement : {str(e)}")

   
    def submit_update(self):
        num_se = self.upd_search_num_se.text().strip()
        ref = self.upd_search_ref.text().strip()
        
        # Préparation du payload (Reflet de ArticleMetadataUpdate)
        try:
            payload = {
                "nom_article": self.upd_name.text().strip() or None,
                "prix_vente": float(self.upd_price.text().replace(',', '.')) if self.upd_price.text() else None,
                "categorie": self.upd_cat.text().strip() or None,
                "emplacement": self.upd_loc.text().strip() or None,
                "fournisseur_stock": self.upd_vendor.text().strip() or None
            }
            
            # Validation locale rapide avant envoi
            if payload["prix_vente"] is not None and payload["prix_vente"] <= 0:
                QMessageBox.warning(self, "Erreur", "Le prix doit être supérieur à 0.")
                return

            url = f"{self.api_url}/stock/{num_se}/article/{ref}/safe-update"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            res = requests.patch(url, json=payload, headers=headers)
            
            if res.status_code == 200:
                QMessageBox.information(self, "Succès", "Mise à jour effectuée avec succès !")
                # Optionnel : Verrouiller le formulaire après succès
                self.upd_form_container.setEnabled(False)
            else:
                error_detail = res.json().get('detail', res.text)
                QMessageBox.warning(self, "Erreur Serveur", f"Détail : {error_detail}")
                
        except ValueError:
            QMessageBox.warning(self, "Format invalide", "Veuillez vérifier le format du prix.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            
    def setup_delete_form(self):
        layout = self.banner_delete.content_layout
        self.target_id_se = None # Stockera l'ID interne pour la suppression finale

        # Zone de recherche
        search_layout = QHBoxLayout()
        self.input_del_numero = QLineEdit()
        self.input_del_numero.setPlaceholderText("Entrez le N° SE (ex: 2024-001)")
        
        btn_inspect = QPushButton("🔎 Vérifier le contenu")
        btn_inspect.clicked.connect(self.inspect_stock_before_delete)
        btn_inspect.setStyleSheet("background-color: #6B7280; color: white; padding: 5px;")
        
        search_layout.addWidget(self.input_del_numero)
        search_layout.addWidget(btn_inspect)
        layout.addLayout(search_layout)

        # Tableau de prévisualisation (caché par défaut)
        self.del_preview_table = QTableWidget(0, 3)
        self.del_preview_table.setHorizontalHeaderLabels(["Référence", "Désignation", "Quantité"])
        self.del_preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.del_preview_table.setMaximumHeight(200)
        self.del_preview_table.setVisible(False)
        layout.addWidget(self.del_preview_table)
        
        # --- MODIFICATION ICI : Encapsuler le bouton pour le style ---
        self.btn_final_delete = QPushButton("🗑️ Supprimer définitivement ce lot")
        self.btn_final_delete.setEnabled(False)
        self.btn_final_delete.clicked.connect(self.confirm_deletion)
        self.btn_final_delete.setMinimumHeight(45) # Évite l'écrasement du texte
        self.btn_final_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # On place le bouton dans un layout centré pour qu'il ne s'étire pas sur toute la largeur
        btn_container_layout = QHBoxLayout()
        btn_container_layout.addStretch()
        btn_container_layout.addWidget(self.btn_final_delete, 3) # Le bouton prend 3 parts sur le vide
        btn_container_layout.addStretch()
        
        layout.addWidget(self.del_preview_table)
        layout.addLayout(btn_container_layout)

        # --- GESTION DU RESET LORS DE LA FERMETURE ---
        # On connecte le clic du bouton de la bannière à une fonction de nettoyage
        self.banner_delete.btn_toggle.clicked.connect(self.reset_delete_form_on_close)
        
        
        
    def reset_delete_form_on_close(self):
        """Nettoie le formulaire quand on ferme la bannière"""
        # Si la bannière vient d'être fermée (donc content_widget n'est plus visible)
        if not self.banner_delete.content_widget.isVisible():
            self.input_del_numero.clear()
            self.del_preview_table.setRowCount(0)
            self.del_preview_table.setVisible(False)
            self.btn_final_delete.setEnabled(False)
            self.target_id_se = None
    
    def inspect_stock_before_delete(self):
        """Cherche le lot et affiche son contenu dans le tableau"""
        numero = self.input_del_numero.text()
        if not numero: return

        try:
            res = requests.get(f"{self.api_url}/stock_se/details/{numero}", 
                               headers={"Authorization": f"Bearer {self.token}"})
            if res.status_code == 200:
                data = res.json()
                self.target_id_se = data['id_se'] # On garde l'ID précieusement
                
                # Remplir le tableau
                self.del_preview_table.setRowCount(0)
                for art in data['articles']:
                    row = self.del_preview_table.rowCount()
                    self.del_preview_table.insertRow(row)
                    self.del_preview_table.setItem(row, 0, QTableWidgetItem(art['reference']))
                    self.del_preview_table.setItem(row, 1, QTableWidgetItem(art['nom_article']))
                    self.del_preview_table.setItem(row, 2, QTableWidgetItem(str(art['quantite'])))
                
                self.del_preview_table.setVisible(True)
                self.btn_final_delete.setEnabled(True)
            else:
                QMessageBox.warning(self, "Erreur", "Numéro SE non trouvé.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def confirm_deletion(self):
        """Utilise l'ID récupéré lors de l'inspection pour supprimer"""
        if not self.target_id_se: return

        reply = QMessageBox.question(
            self, 'Confirmation critique',
            f"Confirmez-vous la suppression du lot {self.input_del_numero.text()} ?\n"
            "Les stocks des articles listés seront décrémentés.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # On utilise l'ID interne pour la route DELETE existante
                res = requests.delete(f"{self.api_url}/stock-se/{self.target_id_se}", 
                                      headers={"Authorization": f"Bearer {self.token}"})
                
                if res.status_code == 200:
                    QMessageBox.information(self, "Succès", "Lot supprimé avec succès.")
                    self.input_del_numero.clear()
                    self.del_preview_table.setVisible(False)
                    self.btn_final_delete.setEnabled(False)
                    self.target_id_se = None
                else:
                    QMessageBox.warning(self, "Action impossible", res.json().get('detail'))
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))
                
    def setup_purchase_price_section(self, role):
        # On ne crée la bannière que si l'utilisateur est gérant
        if role != "gerant":
            return

        self.banner_prices = ManagementBanner("Gestion des Prix d'Achat (Gérant)", "💰", "#F59E0B")
        layout = self.banner_prices.content_layout
        self.container_layout.addWidget(self.banner_prices) # Ajout à la page

        # Barre de recherche
        search_layout = QHBoxLayout()
        self.input_price_se = QLineEdit()
        self.input_price_se.setPlaceholderText("N° SE pour mise à jour des prix...")
        
        btn_load = QPushButton("📊 Charger les prix")
        btn_load.clicked.connect(self.load_prices_for_editing)
        btn_load.setStyleSheet("background-color: #F59E0B; color: white; padding: 5px;")
        
        search_layout.addWidget(self.input_price_se)
        search_layout.addWidget(btn_load)
        layout.addLayout(search_layout)

        # Tableau éditable
        self.price_table = QTableWidget(0, 3)
        self.price_table.setHorizontalHeaderLabels(["Référence", "Désignation", "Prix d'Achat (Modifiable)"])
        self.price_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.price_table)

        # Bouton de sauvegarde
        self.btn_save_prices = QPushButton("✅ Enregistrer tous les prix d'achat")
        self.btn_save_prices.setEnabled(False)
        
        # On définit les propriétés COMMUNES en dehors des pseudo-états
        # et les propriétés SPECIFIQUES à l'intérieur
        self.btn_save_prices.setStyleSheet("""
            QPushButton {
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                min-height: 20px; /* Force une hauteur minimale constante */
            }
            QPushButton:enabled { 
                background-color: #F59E0B; 
                color: white; 
            }
            QPushButton:disabled { 
                background-color: #F3F4F6; 
                color: #9CA3AF; /* Texte gris pour éviter qu'il soit invisible */
                border: 1px solid #E5E7EB;
            }
            QPushButton:hover:enabled {
                background-color: #D97706;
            }
        """)
        self.btn_save_prices.clicked.connect(self.submit_purchase_prices_bulk)
        layout.addWidget(self.btn_save_prices)

    def load_prices_for_editing(self):
        numero = self.input_price_se.text().strip()
        if not numero: return

        try:
            res = requests.get(f"{self.api_url}/stock_se/details/{numero}", 
                            headers={"Authorization": f"Bearer {self.token}"})
            
            if res.status_code == 200:
                data = res.json()
                self.price_table.setRowCount(0)
                
                for art in data['articles']:
                    row = self.price_table.rowCount()
                    self.price_table.insertRow(row)
                    
                    ref_item = QTableWidgetItem(art['reference'])
                    ref_item.setData(Qt.ItemDataRole.UserRole, art['id_article'])
                    ref_item.setFlags(ref_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    
                    name_item = QTableWidgetItem(art['nom_article'])
                    name_item.setFlags(name_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    
                    current_price = str(art.get('prix_achat', '0.00'))
                    price_item = QTableWidgetItem(current_price)
                    price_item.setBackground(QColor("#FFFBEB"))
                    
                    self.price_table.setItem(row, 0, ref_item)
                    self.price_table.setItem(row, 1, name_item)
                    self.price_table.setItem(row, 2, price_item)
                
                self.btn_save_prices.setEnabled(True)
            else:
                # Ajout du warning si le numéro SE est inexistant ou erreur
                QMessageBox.warning(self, "Attention", f"Numéro SE '{numero}' inexistant.")
                self.price_table.setRowCount(0)
                self.btn_save_prices.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    
    def submit_purchase_prices_bulk(self):
        rows = self.price_table.rowCount()
        if rows == 0: return

        # 1. Préparer la liste globale
        updates_list = []
        for row in range(rows):
            try:
                # Récupération sécurisée de l'ID et du prix
                item_id = self.price_table.item(row, 0)
                if not item_id: continue
                
                article_id = item_id.data(Qt.ItemDataRole.UserRole)
                price_text = self.price_table.item(row, 2).text().replace(',', '.')
                
                if not price_text: continue
                
                updates_list.append({
                    "article_id": article_id,
                    "prix_achat": float(price_text)
                })
            except ValueError:
                continue

        if not updates_list: return

        # 2. Envoyer tout le lot d'un seul coup (URL corrigée)
        try:
            # L'URL est maintenant /bulk/prix_achat sans ID spécifique
            url = f"{self.api_url}/articles/bulk/prix_achat"
            
            response = requests.put(
                url, 
                json=updates_list, 
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                QMessageBox.information(self, "Succès", "Mise à jour groupée réussie (Transaction sécurisée).")
                self.price_table.setRowCount(0)
                self.input_price_se.clear()
            else:
                QMessageBox.warning(self, "Erreur", f"Le serveur a refusé le lot : {response.text}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur Réseau", f"Impossible de joindre le serveur : {str(e)}")
                
    def on_reference_changed(self, row, column):
        if column == 0:
            item = self.add_table.item(row, column)
            if not item: return
            
            ref = item.text().strip()
            if not ref: return

            self.add_table.blockSignals(True)
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                res = requests.get(f"{self.api_url}/articles/refv2/{ref}", headers=headers)
                
                if res.status_code == 200 and res.json():
                    data = res.json()
                    
                    # --- LOGIQUE INTELLIGENTE : On ne remplit que si c'est vide ---
                    def set_if_empty(col_index, key):
                        current_item = self.add_table.item(row, col_index)
                        # Si la case est vide ou n'existe pas, on met la valeur de la DB
                        if not current_item or not current_item.text().strip():
                            new_val = str(data.get(key, "")) if data.get(key) else ""
                            self.add_table.setItem(row, col_index, QTableWidgetItem(new_val))

                    set_if_empty(1, "nom_article")
                    set_if_empty(2, "categorie")
                    set_if_empty(3, "emplacement")
                    set_if_empty(4, "prix_vente")
                    
                    # On ne touche jamais à la quantité (colonne 5) car elle est propre au lot
                    
                    # Optionnel : Si l'utilisateur vient de taper la ref, on l'envoie vers la quantité
                    self.add_table.setCurrentCell(row, 5)

            except Exception as e:
                print(f"Erreur recherche auto: {e}")
            
            self.add_table.blockSignals(False)

'''
        # Bouton de suppression finale
        self.btn_final_delete = QPushButton("🗑️ Supprimer définitivement ce lot")
        self.btn_final_delete.setEnabled(False)
        self.btn_final_delete.setStyleSheet("""
            QPushButton:enabled { background-color: #EF4444; color: white; font-weight: bold; padding: 10px; border-radius: 6px; }
            QPushButton:disabled { background-color: #F3F4F6; color: #9CA3AF; }
        """)
        self.btn_final_delete.clicked.connect(self.confirm_deletion)
        layout.addWidget(self.btn_final_delete)
'''

'''
def submit_purchase_prices(self):
        """Boucle sur le tableau et appelle la route par article_id"""
        headers = {"Authorization": f"Bearer {self.token}"}
        rows = self.price_table.rowCount()
        
        if rows == 0: return

        success_count = 0
        errors = []

        for row in range(rows):
            article_id = self.price_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            ref = self.price_table.item(row, 0).text()
            
            try:
                # 2. Récupérer le prix saisi
                price_item = self.price_table.item(row, 2)
                price_text = price_item.text().replace(',', '.')
                
                # Vérification du format avant conversion
                try:
                    new_price = float(price_text)
                except ValueError:
                    # Alerte immédiate sur le format
                    QMessageBox.warning(self, "Format invalide", f"Le prix pour l'article {ref} n'est pas un nombre valide.")
                    price_item.setBackground(QColor("#FFCCCC")) # Optionnel : colorier en rouge l'erreur
                    return # On arrête tout pour que l'utilisateur corrige

                # 3. Appel API
                url = f"{self.api_url}/articles/{article_id}/prix_achat"
                payload = {"prix_achat": new_price}
                
                response = requests.put(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    errors.append(f"Erreur pour {ref}: {response.text}")
                    
            except Exception as e:
                errors.append(f"Erreur réseau pour {ref}: {str(e)}")

        # Rapport final et Rafraîchissement
        if not errors:
            QMessageBox.information(self, "Succès", f"Tous les prix ({success_count}) ont été mis à jour.")
            # Rafraîchir après succès : vider le tableau et l'input
            self.price_table.setRowCount(0)
            self.input_price_se.clear()
            self.btn_save_prices.setEnabled(False)
        else:
            error_report = "\n".join(errors[:5])
            QMessageBox.warning(self, "Mise à jour partielle", 
                                f"{success_count} réussis.\n\nErreurs :\n{error_report}")
            # Note : On ne vide pas le tableau ici pour permettre la correction des erreurs
            '''