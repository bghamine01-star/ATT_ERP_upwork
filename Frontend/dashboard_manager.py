import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

# Placeholder – real base URL is confidential
API_BASE_URL = "https://example.com/api/v1"


class ShowcaseCard(QFrame):
    """Modern clickable card with shadow and hover – demo only"""

    def __init__(self, title: str, icon: str, accent_color="#6366F1", on_click=None):
        super().__init__()
        self.setFixedSize(240, 260)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.on_click = on_click

        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
            }
            QFrame:hover {
                background-color: #F8F9FF;
            }
        """)

        # Soft shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        # Icon (emoji or symbol)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 64px; color: {accent_color};")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1F2937;
            text-align: center;
        """)
        title_lbl.setWordWrap(True)

        layout.addStretch(1)
        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addStretch(1)

    def mousePressEvent(self, event):
        if self.on_click:
            self.on_click()


class DashboardShowcase(QWidget):
    """Public demo version – real analytics dashboard redacted"""

    def __init__(self, auth_token: str):
        super().__init__()
        self.token = auth_token
        self.api_base = API_BASE_URL
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(40)

        # Header
        header = QLabel("Analytics Overview – Demo")
        header.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #111827;
            letter-spacing: -0.5px;
        """)
        layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)

        # Card grid
        grid = QGridLayout()
        grid.setSpacing(60)

        # Example card 1 (Finance-like)
        card_1 = ShowcaseCard(
            "Key Metrics",
            "📊",
            "#6366F1",
            on_click=self._open_example_view_1
        )
        grid.addWidget(card_1, 0, 0)

        # Example card 2 (commented pattern – add more as needed)
        # card_2 = ShowcaseCard("Performance", "⚡", "#10B981", self._open_example_view_2)
        # grid.addWidget(card_2, 0, 1)

        layout.addLayout(grid)

        # Refresh / sync button
        btn_refresh = QPushButton("↻ Refresh Data")
        btn_refresh.setStyleSheet("""
            QPushButton {
                padding: 14px 32px;
                font-size: 15px;
                font-weight: 500;
                border-radius: 10px;
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        btn_refresh.clicked.connect(self._refresh_placeholder)
        layout.addWidget(btn_refresh, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    def _refresh_placeholder(self):
        """Placeholder – real stats recalculation hidden"""
        try:
            # In real version: requests.get(f"{self.api_base}/admin/refresh-stats", ...)
            QMessageBox.information(self, "Demo", "Data refresh simulated.\nReal endpoint & logic redacted.")
        except Exception:
            QMessageBox.critical(self, "Demo", "Connection simulation failed.")

    def _open_example_view_1(self):
        """Placeholder for opening a detailed view"""
        QMessageBox.information(self, "Demo", 
                                "This would open a detailed statistics window.\n"
                                "Real sub-window & data visualization hidden.")

    # def _open_example_view_2(self):
    #     QMessageBox.information(self, "Demo", "Another view placeholder.")


# ── Standalone demo ─────────────────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = DashboardShowcase("fake-token-for-demo")
    window.setWindowTitle("Dashboard – Showcase Only")
    window.resize(1000, 800)
    window.show()
    sys.exit(app.exec())