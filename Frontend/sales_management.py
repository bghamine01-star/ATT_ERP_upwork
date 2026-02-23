from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import requests
from datetime import datetime, date
from config import API_BASE_URL

class BLManagement(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.api_url = API_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.init_ui()

    def init_ui(self):
        # Layout principal de la page
        outer_layout = QVBoxLayout(self)
        
        # On crée un Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        self.main_layout = QVBoxLayout(container) # C'est ici qu'on met tout le contenu
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        # --- TITRE ---
        title = QLabel("Création de Bon de Livraison")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        self.main_layout.addWidget(title)

        # --- ENTÊTE : CLIENT & DATE ---
        header_card = QFrame()
        header_card.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #E5E7EB;")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(20, 20, 20, 20)

        # Partie Gauche : Client
        client_sub_layout = QVBoxLayout()
        # Nouveau champ de saisie avec autocomplétion
        self.client_input = QLineEdit()
        self.client_input.setPlaceholderText("Saisir le nom du client (min. 4 lettres)...")
        self.client_input.setMinimumWidth(300)
        
        # Initialisation du Completer pour le client
        self.client_completer = QCompleter(self)
        self.client_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.client_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        # Cela empêche le completer de modifier le texte du QLineEdit tant qu'on n'a pas validé
        self.client_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.client_input.setCompleter(self.client_completer)
        
        # Variable pour stocker le client sélectionné (ID et infos)
        self.selected_client_data = None

        # Signaux
        self.client_input.textChanged.connect(self.on_client_search_changed)
        # Se déclenche quand l'utilisateur choisit une suggestion
        self.client_completer.activated.connect(self.on_client_selected)
        self.client_input.returnPressed.connect(self.handle_client_return_pressed)

        self.lbl_client_details = QLabel("Saisissez un nom pour voir les détails")
        self.lbl_client_details.setStyleSheet("color: #6B7280; font-size: 13px;")
        
        client_sub_layout.addWidget(QLabel("<b>DESTINATAIRE</b>"))
        client_sub_layout.addWidget(self.client_input)
        client_sub_layout.addWidget(self.lbl_client_details)
        header_layout.addLayout(client_sub_layout, 2)

        header_layout.addStretch(1)

        # Partie Droite : Date
        date_sub_layout = QVBoxLayout()
        # AJOUT : Champ Numéro de BL
        self.num_bl_edit = QLineEdit()
        self.num_bl_edit.setPlaceholderText("Ex: BL-2024-001")
        self.num_bl_edit.setMinimumWidth(150)
        
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumWidth(150)
        
        date_sub_layout.addWidget(QLabel("<b>NUMÉRO DU BON</b>")) 
        date_sub_layout.addWidget(self.num_bl_edit)
        date_sub_layout.addWidget(QLabel("<b>DATE DU BON</b>"))
        date_sub_layout.addWidget(self.date_edit)
        date_sub_layout.addStretch()
        header_layout.addLayout(date_sub_layout, 1)

        self.main_layout.addWidget(header_card)

        # --- TABLEAU DES ARTICLES ---
        table_container = QFrame()
        table_container.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #E5E7EB;")
        table_layout = QVBoxLayout(table_container)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Référence", "Désignation", "Dispo.", "Qté", "Remise %", "Total Ligne"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("border: none; gridline-color: #F3F4F6;")
        self.table.setFixedHeight(350)

        # Création d'un layout horizontal pour les boutons d'action sous le tableau
        buttons_layout = QHBoxLayout()
        
        btn_add_row = QPushButton("+ Ajouter une ligne")
        btn_add_row.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_row.setStyleSheet("background-color: #F3F4F6; color: #374151; padding: 8px; border-radius: 5px; font-weight: bold;")
        btn_add_row.clicked.connect(self.add_line)

        table_layout.addWidget(self.table)
        table_layout.addWidget(btn_add_row, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Nouveau bouton supprimer
        btn_remove_row = QPushButton("- Supprimer la ligne")
        btn_remove_row.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_remove_row.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2; 
                color: #991B1B; 
                padding: 8px; 
                border-radius: 5px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FECACA; }
        """)
        btn_remove_row.clicked.connect(self.remove_selected_row)

        buttons_layout.addWidget(btn_add_row)
        buttons_layout.addWidget(btn_remove_row)
        buttons_layout.addStretch() # Pousse les boutons vers la gauche

        table_layout.addLayout(buttons_layout)
        
        self.main_layout.addWidget(table_container)

        # --- RÉSUMÉ ET VALIDATION ---
        # --- SECTION TOTAUX (CORRIGÉE) ---
        totals_container = QWidget()
        totals_h_layout = QHBoxLayout(totals_container)
        totals_h_layout.setContentsMargins(0, 0, 0, 0)
        
        # On crée la carte des totaux
        self.totals_card = QFrame()
        self.totals_card.setFixedWidth(350) # Un peu plus large pour éviter l'effet entassé
        self.totals_card.setStyleSheet("background-color: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 10px; padding: 15px;")
        
        totals_form = QFormLayout(self.totals_card)
        totals_form.setSpacing(10) # Plus d'espace entre les lignes
        
        self.lbl_total_brut = QLabel("0.00 DT")
        self.lbl_total_remise = QLabel("0.00 DT") # Somme chiffrée des remises
        self.lbl_total_final = QLabel("0.00 DT")
        self.lbl_total_final.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")

        totals_form.addRow("Total Brut :", self.lbl_total_brut)
        totals_form.addRow("Total Remises (Indication) :", self.lbl_total_remise)
        totals_form.addRow(QLabel("<hr>"), QLabel("<hr>"))
        totals_form.addRow("<b>NET À PAYER (BL) :</b>", self.lbl_total_final)

        totals_h_layout.addStretch()
        totals_h_layout.addWidget(self.totals_card)
        self.main_layout.addWidget(totals_container)

        # --- BOUTON DE VALIDATION ---
        self.btn_validate = QPushButton("🚀 Valider et Générer le Bon de Livraison")
        self.btn_validate.setMinimumHeight(55)
        self.btn_validate.setStyleSheet("""
            QPushButton { 
                background-color: #111827; color: white; font-weight: bold; 
                border-radius: 8px; font-size: 16px; margin-top: 10px;
            }
            QPushButton:hover { background-color: #374151; }
        """)
        self.btn_validate.clicked.connect(self.submit_bl)
        self.main_layout.addWidget(self.btn_validate)

        # Finalisation du Scroll Area
        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        # Chargement initial
        #self.on_client_search_changed()

    # --- LOGIQUE BACKEND ---
    
     
    def on_client_search_changed(self, text):
        """Déclenche la recherche API seulement si ce n'est pas une navigation clavier"""
        # Si le completer est en train d'insérer une suggestion, on ne fait rien
        if self.client_completer.completionMode() == QCompleter.CompletionMode.PopupCompletion and \
        self.client_input.signalsBlocked():
            return

        if len(text) >= 4:
            try:
                url = f"{self.api_url}/clients/search" 
                params = {"q": text}
                res = requests.get(url, params=params, headers=self.headers, timeout=1.0)
                
                if res.status_code == 200:
                    new_list = res.json()
                    if not new_list:
                        self.lbl_client_details.setText("❌ Aucun client trouvé")
                        return

                    # OPTIMISATION CRUCIALE : 
                    # On ne met à jour le modèle QUE si la liste a réellement changé
                    names = [c['nom_client'] for c in new_list]
                    
                    # Accéder au modèle actuel pour comparer
                    current_model = self.client_completer.model()
                    if current_model is None or current_model.stringList() != names:
                        self.current_clients_list = new_list
                        model = QStringListModel(names)
                        self.client_completer.setModel(model)
                        # On ne force pas .complete() ici si on est déjà en train de naviguer
            except Exception as e:
                print(f"Erreur recherche client: {e}")
                
    def handle_client_return_pressed(self):
        """Gère l'appui sur Entrée dans le champ client"""
        text = self.client_input.text().strip()
        if text and hasattr(self, 'current_clients_list'):
            # Si un seul client correspond exactement ou commence par, on le sélectionne
            match = next((c for c in self.current_clients_list if c['nom_client'].lower() == text.lower()), None)
            if match:
                self.on_client_selected(match['nom_client'])
         
    def remove_selected_row(self):
        """Supprime la ligne sélectionnée et met à jour les totaux"""
        current_row = self.table.currentRow()
        
        if current_row >= 0:
            # Demander confirmation (optionnel mais recommandé)
            # res = QMessageBox.question(self, "Confirmation", "Supprimer cette ligne ?", 
            #                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            # if res == QMessageBox.StandardButton.Yes:
            
            self.table.removeRow(current_row)
            # TRÈS IMPORTANT : Recalculer le total après la suppression
            self.update_row_total()
        else:
            QMessageBox.warning(self, "Sélection", "Veuillez cliquer sur une ligne pour la supprimer.")

    def on_client_selected(self, name):
        """Récupère les infos du client une fois sélectionné dans la liste"""
        if not hasattr(self, 'current_clients_list') or not self.current_clients_list:
            return

        # On retrouve l'objet client complet
        client = next((c for c in self.current_clients_list if c['nom_client'] == name), None)
        
        if client:
            self.selected_client_data = client
            adresse = client.get('adresse') or "Non renseignée"
            tel = client.get('telephone') or "Non renseigné"
            
            self.lbl_client_details.setText(f"📍 {adresse}  |  📞 {tel}")
            self.lbl_client_details.setStyleSheet("color: #10B981; font-weight: bold; font-size: 13px;")    

    def add_line(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 1. Référence
        ref_input = QLineEdit()
        ref_input.setPlaceholderText("Saisir réf...")
        
        
        completer = QCompleter(self) # On lie le completer à la fenêtre
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        
        # Utilisation d'une QListView standard
        popup = QListView()
        completer.setPopup(popup)
        
        # IMPORTANT : On ne touche pas au FocusPolicy ici pour ne pas bloquer le QLineEdit
        ref_input.setCompleter(completer)
        
        # Signaux
        ref_input.textChanged.connect(lambda text: self.update_completer_data(text, completer))
        ref_input.editingFinished.connect(lambda: self.check_article_stock(row))
        
        self.table.setCellWidget(row, 0, ref_input)

        # Initialisation des colonnes fixes (Désignation, Dispo, Total)
        # Il est crucial d'initialiser ces items pour éviter des erreurs plus tard
        self.table.setItem(row, 1, QTableWidgetItem("-"))
        self.table.setItem(row, 2, QTableWidgetItem("0"))
        self.table.setItem(row, 5, QTableWidgetItem("0.00"))

        # 3. Quantité
        qty_spin = QSpinBox()
        qty_spin.setRange(1, 99999)
        qty_spin.valueChanged.connect(self.update_row_total)
        self.table.setCellWidget(row, 3, qty_spin)

        # 4. Remise
        remise_spin = QDoubleSpinBox()
        remise_spin.setRange(0, 100)
        remise_spin.setSuffix(" %")
        remise_spin.valueChanged.connect(self.update_row_total)
        self.table.setCellWidget(row, 4, remise_spin)
        
        # Ajustement automatique de la largeur des colonnes
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(3, 80)
        
        # Forcer le focus sur la nouvelle ligne créée
        ref_input.setFocus()

        # Permet de passer à la cellule suivante avec Entrée/Tab
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.AnyKeyPressed)
        
    def update_completer_data(self, text, completer):
        if len(text) < 2:
            return
        try:
            # On ne recrée pas le modèle si les suggestions sont identiques
            res = requests.get(f"{self.api_url}/articles/search-refs?q={text}", 
                            headers=self.headers, timeout=0.5)
            if res.status_code == 200:
                suggestions = [item['reference'] for item in res.json()]
                
                # Mise à jour intelligente du modèle
                current_model = completer.model()
                if not current_model or current_model.stringList() != suggestions:
                    model = QStringListModel(suggestions)
                    completer.setModel(model)
                    # Important pour que les flèches fonctionnent immédiatement après l'apparition
                    completer.complete() 
        except Exception as e:
            print(f"Erreur Autocomplete: {e}")

    def check_article_stock(self, row):
        """Vérifie l'existence et le stock de l'article via la nouvelle route /ref/"""
        ref_widget = self.table.cellWidget(row, 0)
        if not ref_widget: return
        ref = ref_widget.text().strip()
        if not ref: return

        try:
            # Appel de la nouvelle route
            res = requests.get(f"{self.api_url}/articles/ref/{ref}", headers=self.headers)
            
            # On s'assure que l'item de désignation (col 1) existe bien en mémoire
            if not self.table.item(row, 1):
                self.table.setItem(row, 1, QTableWidgetItem(""))
            if not self.table.item(row, 2):
                self.table.setItem(row, 2, QTableWidgetItem("0"))

            if res.status_code == 200:
                art = res.json()
                # 1. Remplir le nom
                self.table.item(row, 1).setText(art['nom_article'])
                # 2. Stocker le prix pour les calculs (UserRole)
                self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, art['prix_vente'])
                # 3. Afficher la disponibilité
                self.table.item(row, 2).setText(str(art['quantite_disponible']))
                
                # Feedback visuel si stock épuisé
                if art['quantite_disponible'] <= 0:
                    self.table.item(row, 2).setForeground(QColor("#EF4444"))
                else:
                    self.table.item(row, 2).setForeground(QColor("#10B981"))
                
                self.update_row_total()
            else:
                # Si non trouvé (404)
                self.table.item(row, 1).setText("⚠️ Réf Inconnue")
                self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, 0.0)
                self.table.item(row, 2).setText("0")
                
        except Exception as e:
            print(f"Erreur réseau: {e}")

    
        
    def update_row_total(self):
            total_brut_gen = 0.0
            total_remise_gen = 0.0

            for row in range(self.table.rowCount()):
                pu = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole) or 0.0
                qty = self.table.cellWidget(row, 3).value()
                remise_pct = self.table.cellWidget(row, 4).value()

                brut_ligne = float(pu) * qty
                montant_remise_ligne = brut_ligne * (remise_pct / 100)
                
                # Affichage : Le total ligne reste BRUT pour le BL
                self.table.item(row, 5).setText(f"{brut_ligne:,.2f}")
                
                total_brut_gen += brut_ligne
                total_remise_gen += montant_remise_ligne

            # Mise à jour des labels (Le design est "entassé" ? On augmente le spacing)
            self.lbl_total_brut.setText(f"{total_brut_gen:,.2f} DT")
            # On affiche la remise en chiffre comme indicateur (ex: 45.00 DT)
            self.lbl_total_remise.setText(f"{total_remise_gen:,.2f} DT") 
            self.lbl_total_remise.setStyleSheet("color: #6B7280; font-style: italic;")
            
            # Pour le BL, le Net à Payer = Total Brut
            self.lbl_total_final.setText(f"{total_brut_gen:,.2f} DT")
        

    def submit_bl(self):
        """Envoie les données au backend pour création du BL (Logique FIFO)"""
        # 1. Récupération du numéro de BL
        numero_bl = self.num_bl_edit.text().strip()
        
        # 2. Vérification si un client a été sélectionné via la recherche dynamique
        if not self.selected_client_data:
            QMessageBox.critical(self, "Erreur", "Veuillez sélectionner un client valide dans la liste de recherche.")
            return

        # 3. Vérification du numéro de BL
        if not numero_bl:
            QMessageBox.critical(self, "Erreur", "Veuillez saisir un numéro de bon de livraison.")
            return

        # 4. Construction de la liste des articles
        # 4. Construction de la liste des articles et vérification des doublons
        articles_vends = []
        references_saisies = set() # Pour suivre les doublons

        for row in range(self.table.rowCount()):
            ref_widget = self.table.cellWidget(row, 0)
            if not ref_widget:
                continue
                
            ref = ref_widget.text().strip()
            if not ref:
                continue

            # --- DÉTECTION DE DOUBLONS ---
            if ref in references_saisies:
                QMessageBox.warning(self, "Doublon détecté", 
                                    f"L'article avec la référence '{ref}' a été ajouté plusieurs fois.\n"
                                    "Veuillez regrouper les quantités sur une seule ligne ou supprimer la ligne en trop.")
                return
            
            references_saisies.add(ref)
            # -----------------------------

            qty = self.table.cellWidget(row, 3).value()
            remise = self.table.cellWidget(row, 4).value()
            
            try:
                dispo = int(self.table.item(row, 2).text())
            except (ValueError, AttributeError):
                dispo = 0

            if qty > dispo:
                QMessageBox.critical(self, "Erreur Stock", f"Quantité demandée pour {ref} supérieure au stock ({dispo})")
                return

            articles_vends.append({
                "reference": ref,
                "quantite": qty,
                "remise": remise
            })

        if not articles_vends:
            QMessageBox.warning(self, "Vide", "Ajoutez au moins un article.")
            return

        # 5. Construction du Payload selon CreerVenteSchema
        payload = {
            "client_id": self.selected_client_data['id_client'],
            "date_bl": self.date_edit.date().toString("yyyy-MM-dd"),
            "numero_bl": numero_bl,
            "articles": articles_vends
        }

        # 6. Envoi au Backend
        try:
            self.btn_validate.setEnabled(False)
            res = requests.post(f"{self.api_url}/ventes/", json=payload, headers=self.headers)
            
            if res.status_code == 200:
                data = res.json()
                QMessageBox.information(self, "Succès", f"Bon de Livraison {data['numero_bl']} créé avec succès.")
                
                # --- Nettoyage complet de l'interface ---
                self.table.setRowCount(0)
                self.num_bl_edit.clear()
                self.client_input.clear() # Le QLineEdit de recherche client
                self.selected_client_data = None # Reset de l'objet client
                self.lbl_client_details.setText("Saisissez un nom pour voir les détails")
                self.update_row_total()
            else:
                error_detail = res.json().get('detail', 'Erreur inconnue')
                QMessageBox.critical(self, "Erreur Backend", f"Échec de la vente : {error_detail}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de connexion : {str(e)}")
        finally:
            self.btn_validate.setEnabled(True)
            
    def verifier_date_bl(self):
        date_selectionnee = self.input_date_bl.date().toPyDate()
        today = date.today()
        premier_jour_actuel = date(today.year, today.month, 1)

        if date_selectionnee < premier_jour_actuel:
            QMessageBox.warning(self, "Date invalide", "Vous ne pouvez pas créer de BL pour un mois passé.")
            self.input_date_bl.setDate(QDate.currentDate()) # Remet à aujourd'hui
    