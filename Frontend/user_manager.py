import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QScrollArea, QMessageBox, QFrame, QComboBox
)
from PyQt6.QtCore import Qt


# Placeholder – real base URL is confidential
API_BASE_URL = "https://example.com/api/v1"


class EntityRow(QFrame):
    """Styled row for displaying an entity with delete action – showcase only"""

    def __init__(self, name: str, tag: str, delete_callback):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 1px solid #F3F4F6;
                padding: 12px 16px;
            }
            QFrame:hover { background: #F9FAFB; }
        """)
        layout = QHBoxLayout(self)

        info = QVBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-weight: 600; font-size: 14px; color: #111827;")

        tag_lbl = QLabel(tag.upper())
        tag_lbl.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: bold;")

        info.addWidget(name_lbl)
        info.addWidget(tag_lbl)

        del_btn = QPushButton("Remove")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                color: #DC2626; background: white; border: 1px solid #FEE2E2;
                padding: 6px 14px; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background: #DC2626; color: white; }
        """)
        del_btn.clicked.connect(lambda: delete_callback(name))

        layout.addLayout(info, 1)
        layout.addStretch()
        layout.addWidget(del_btn)


class UserDirectoryDemo(QWidget):
    """Public showcase – real user/role management logic hidden"""

    def __init__(self, auth_token: str):
        super().__init__()
        self.token = auth_token
        self.api_base = API_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.init_ui()
        # self._load_entities()  # commented – would call API in real version

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(28)

        # Title
        title = QLabel("User Directory – Demo")
        title.setStyleSheet("""
            font-size: 28px; font-weight: 600; color: #111827;
            letter-spacing: -0.4px;
        """)
        layout.addWidget(title)

        content = QHBoxLayout()
        content.setSpacing(32)

        # Left: scrollable list
        list_card = QFrame()
        list_card.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E5E7EB;")
        list_vbox = QVBoxLayout(list_card)

        header = QLabel("Profiles")
        header.setStyleSheet("""
            padding: 20px; font-weight: bold; font-size: 16px;
            color: #111827; border-bottom: 1px solid #E5E7EB;
        """)
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

        # Right: creation form
        form_card = QFrame()
        form_card.setFixedWidth(340)
        form_card.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E5E7EB;")

        form_vbox = QVBoxLayout(form_card)
        form_vbox.setContentsMargins(24, 28, 24, 28)
        form_vbox.setSpacing(16)

        form_title = QLabel("New User")
        form_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #111827;")

        input_style = """
            QLineEdit, QComboBox {
                padding: 10px; border: 1px solid #D1D5DB; border-radius: 6px;
                background: #F9FAFB; color: #374151;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #6366F1;
            }
        """

        self.name_field = QLineEdit(); self.name_field.setPlaceholderText("Full name")
        self.name_field.setStyleSheet(input_style)

        self.pass_field = QLineEdit(); self.pass_field.setPlaceholderText("Password")
        self.pass_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_field.setStyleSheet(input_style)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Standard", "Administrator"])
        self.role_combo.setStyleSheet(input_style)

        create_btn = QPushButton("Create Account")
        create_btn.setStyleSheet("""
            QPushButton {
                background: #6366F1; color: white; padding: 12px;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #4F46E5; }
        """)
        create_btn.clicked.connect(self._create_placeholder)

        for w in [form_title, QLabel("Name"), self.name_field,
                  QLabel("Password"), self.pass_field,
                  QLabel("Role"), self.role_combo,
                  create_btn]:
            form_vbox.addWidget(w)

        content.addWidget(list_card, 2)
        content.addWidget(form_card, 1)

        layout.addLayout(content)

    def _load_entities(self):
        """Placeholder – real user list fetch removed"""
        # Would be: requests.get(f"{self.api_base}/users/", ...)
        # For demo: add dummy rows
        dummy_users = [
            ("Alex Dupont", "Standard"),
            ("Marie Laurent", "Administrator"),
            ("Thomas Moreau", "Standard"),
        ]
        for name, role in dummy_users:
            row = EntityRow(name, role, self._delete_placeholder)
            self.list_layout.insertWidget(0, row)

    def _create_placeholder(self):
        if not self.name_field.text().strip():
            QMessageBox.warning(self, "Required", "Name is required.")
            return
        QMessageBox.information(self, "Demo", 
                                "This would create a new user account.\n"
                                "Real API call, password hashing, role assignment hidden.")
        # Would clear form + reload list

    def _delete_placeholder(self, name: str):
        reply = QMessageBox.question(self, "Confirm", f"Remove {name} ?")
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Demo", 
                                    "Delete action simulated.\n"
                                    "Real DELETE request & list refresh hidden.")


# ── Demo ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = UserDirectoryDemo("fake-jwt-token")
    w.setWindowTitle("User Directory – Showcase Only")
    w.resize(1100, 720)
    w.show()
    sys.exit(app.exec())