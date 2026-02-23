import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QScrollArea, QMessageBox, QFrame, QComboBox, QTextEdit,
    QDialog
)
from PyQt6.QtCore import Qt

# Fake constant – real URL is confidential
API_BASE_URL = "https://example.com/api/v1"


class EntityRow(QFrame):
    """Styled row for displaying an entity with actions – showcase only"""

    def __init__(self, entity_data, delete_callback):
        super().__init__()
        self.entity_data = entity_data
        self.entity_id = entity_data.get('id')
        self.display_name = entity_data.get('name', 'Unnamed')

        self.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 1px solid #F3F4F6;
                padding: 14px 16px;
            }
            QFrame:hover { background: #F9FAFB; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main info
        info = QVBoxLayout()
        name_lbl = QLabel(self.display_name)
        name_lbl.setStyleSheet("font-weight: 600; font-size: 14px; color: #111827;")

        sub = f"Ref: {entity_data.get('ref', '—')} | {entity_data.get('extra', '—')}"
        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet("color: #6B7280; font-size: 12px;")

        info.addWidget(name_lbl)
        info.addWidget(sub_lbl)

        # Details button
        btn_details = QPushButton("Details")
        btn_details.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_details.setStyleSheet("""
            QPushButton {
                color: #6366F1; background: white; border: 1px solid #E0E7FF;
                padding: 6px 14px; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background: #F0F4FF; }
        """)
        btn_details.clicked.connect(self.show_details)

        # Status badge (demo)
        status = entity_data.get('status', 'Active')
        status_lbl = QLabel(status)
        color = "#10B981" if status == "Active" else "#F59E0B"
        bg = "#D1FAE5" if status == "Active" else "#FEF3C7"
        status_lbl.setStyleSheet(f"""
            color: {color}; background: {bg};
            padding: 4px 10px; border-radius: 12px;
            font-size: 11px; font-weight: bold;
        """)

        # Delete button
        btn_delete = QPushButton("Delete")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setStyleSheet("""
            QPushButton {
                color: #DC2626; background: white; border: 1px solid #FEE2E2;
                padding: 6px 14px; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background: #DC2626; color: white; }
        """)
        btn_delete.clicked.connect(lambda: delete_callback(self.entity_id, self.display_name))

        layout.addLayout(info, 1)
        layout.addStretch()
        layout.addWidget(btn_details)
        layout.addSpacing(12)
        layout.addWidget(status_lbl)
        layout.addSpacing(16)
        layout.addWidget(btn_delete)


    def show_details(self):
        """Simple read-only details view – real data shape hidden"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Entity — {self.display_name}")
        dialog.setMinimumSize(420, 340)

        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("""
            QTextEdit {
                background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 8px;
                padding: 16px; font-size: 13px; line-height: 1.5;
            }
        """)

        # Fake sanitized content
        content = f"""
        <b>IDENTITY</b><br>
        Name: {self.entity_data.get('name')}<br>
        Reference: {self.entity_data.get('ref', '—')}<br>
        Status: {self.entity_data.get('status', '—')}<br><br>

        <b>CONTACT</b><br>
        Email: {self.entity_data.get('email', '—')}<br>
        Phone: {self.entity_data.get('phone', '—')}<br>
        Location: {self.entity_data.get('location', '—')}
        """

        text.setHtml(content)
        layout.addWidget(text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        close_btn.setStyleSheet("background: #6366F1; color: white; padding: 10px; border-radius: 6px;")
        layout.addWidget(close_btn)

        dialog.exec()


class EntityManager(QWidget):
    """Showcase version – real client/CRM logic removed"""

    def __init__(self, auth_token: str):
        super().__init__()
        self.token = auth_token
        self.api_base = API_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.init_ui()
        # self._load_entities()  # commented — would call API in real version

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # Title
        title = QLabel("Entity Directory – Demo")
        title.setStyleSheet("font-size: 28px; font-weight: 600; color: #111827;")
        layout.addWidget(title)

        # Search
        search = QLineEdit()
        search.setPlaceholderText("Search by name or reference…")
        search.setStyleSheet("""
            padding: 10px 16px; border: 1px solid #E5E7EB; border-radius: 20px;
            background: white; font-size: 14px;
        """)
        search.textChanged.connect(self._filter_rows)
        layout.addWidget(search)

        # Two-column content
        content = QHBoxLayout()
        content.setSpacing(28)

        # Left: scrollable list
        list_card = QFrame()
        list_card.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E5E7EB;")
        list_vbox = QVBoxLayout(list_card)

        header = QLabel("All Entities")
        header.setStyleSheet("padding: 16px; font-weight: bold; font-size: 16px; color: #111827; border-bottom: 1px solid #E5E7EB;")
        list_vbox.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_widget)
        list_vbox.addWidget(scroll)

        # Right: add form
        form_card = QFrame()
        form_card.setFixedWidth(360)
        form_card.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E5E7EB;")

        form_vbox = QVBoxLayout(form_card)
        form_vbox.setSpacing(12)

        form_title = QLabel("Add New Entity")
        form_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #111827;")

        input_style = "padding: 9px; border: 1px solid #D1D5DB; border-radius: 6px; background: #F9FAFB;"

        self.name_field    = QLineEdit(); self.name_field.setPlaceholderText("Name");    self.name_field.setStyleSheet(input_style)
        self.ref_field     = QLineEdit(); self.ref_field.setPlaceholderText("Reference"); self.ref_field.setStyleSheet(input_style)
        self.email_field   = QLineEdit(); self.email_field.setPlaceholderText("Email");   self.email_field.setStyleSheet(input_style)
        self.phone_field   = QLineEdit(); self.phone_field.setPlaceholderText("Phone");   self.phone_field.setStyleSheet(input_style)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive"])
        self.status_combo.setStyleSheet(input_style)

        self.note_field = QTextEdit()
        self.note_field.setPlaceholderText("Notes / address...")
        self.note_field.setMaximumHeight(90)
        self.note_field.setStyleSheet(input_style)

        btn_save = QPushButton("Save Entity")
        btn_save.setStyleSheet("background: #6366F1; color: white; padding: 12px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(self._add_entity_placeholder)

        for w in [form_title, self.name_field, self.ref_field, self.email_field,
                  self.phone_field, self.status_combo, self.note_field, btn_save]:
            form_vbox.addWidget(w)

        content.addWidget(list_card, 2)
        content.addWidget(form_card, 1)

        layout.addLayout(content)

    def _filter_rows(self, text):
        text = text.lower().strip()
        for i in range(self.list_layout.count()):
            item = self.list_layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if isinstance(w, EntityRow):
                match = text in w.display_name.lower() or text in str(w.entity_id)
                w.setVisible(match)

    def _load_entities_placeholder(self):
        """In real version: fetch from API and populate rows"""
        # Example of what would happen:
        # resp = requests.get(f"{self.api_base}/entities/", headers=self.headers)
        # for item in resp.json():
        #     row = EntityRow(item, self._delete_entity)
        #     self.list_layout.insertWidget(0, row)

        QMessageBox.information(self, "Demo", "Entity list would be loaded here.\nReal API call & data redacted.")

    def _add_entity_placeholder(self):
        """Placeholder – real creation logic removed"""
        if not self.name_field.text().strip():
            QMessageBox.warning(self, "Required", "Name is required.")
            return

        QMessageBox.information(self, "Demo", "This would create a new entity.\nAll validation & API logic hidden.")
        # Would clear form + reload list in real version

    def _delete_entity(self, eid, name):
        reply = QMessageBox.question(self, "Confirm", f"Delete {name} ?")
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Demo", "Delete action simulated.\nReal DELETE request redacted.")


# ── Demo ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = EntityManager("fake-jwt-for-demo")
    w.setWindowTitle("Entity Manager – Showcase Only")
    w.resize(1100, 720)
    w.show()
    sys.exit(app.exec())