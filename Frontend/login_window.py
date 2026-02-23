import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

# Placeholder – real base URL is confidential
API_BASE_URL = "https://example.com/api/v1"


class AuthDemoWindow(QWidget):
    """Showcase version – real login logic removed"""

    # Signal: (token: str, role: str) on successful auth
    auth_success = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign In – Demo")
        self.setFixedSize(420, 520)
        self.setStyleSheet("background-color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(16)

        # Header
        title = QLabel("Welcome")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1F2937;")
        subtitle = QLabel("Sign in to continue")
        subtitle.setStyleSheet("color: #6B7280; font-size: 14px; margin-bottom: 24px;")

        # Inputs
        input_style = """
            QLineEdit {
                padding: 12px 14px;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #F9FAFB;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #6366F1;
                background-color: white;
            }
        """

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet(input_style)
        self.username.returnPressed.connect(self.attempt_login)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setStyleSheet(input_style)
        self.password.returnPressed.connect(self.attempt_login)

        # Login button
        self.btn_login = QPushButton("Sign In")
        self.btn_login.setDefault(True)  # Reacts to Enter key
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                padding: 14px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
            QPushButton:pressed {
                background-color: #4338CA;
            }
        """)
        self.btn_login.clicked.connect(self.attempt_login)

        # Assemble
        layout.addStretch(1)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(24)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addSpacing(16)
        layout.addWidget(self.btn_login)
        layout.addStretch(2)

    def attempt_login(self):
        """Placeholder – real authentication flow hidden"""
        username = self.username.text().strip()
        password = self.password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Required", "Please fill in both fields.")
            return

        # In real version: POST to /auth or /token endpoint
        # Here we simulate success/failure for demo purposes
        try:
            # Fake call — would be requests.post(f"{API_BASE_URL}/auth", ...)
            QMessageBox.information(
                self, "Demo Mode",
                "This would attempt authentication.\n\n"
                "Real credentials check, token retrieval, and role handling are hidden."
            )

            # Simulate success (for testing UI flow)
            fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake"
            fake_role = "user"  # or "admin", "manager", etc.
            self.auth_success.emit(fake_token, fake_role)

            # Optional: self.close() or hide() after success

        except Exception as e:
            QMessageBox.critical(self, "Error", 
                                 "Connection failed (simulated).\n\n"
                                 "Real error handling hidden.")


# ── Standalone demo ─────────────────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = AuthDemoWindow()
    window.show()
    sys.exit(app.exec())