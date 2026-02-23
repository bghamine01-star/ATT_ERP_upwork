# =============================================================================
# DEMO / PUBLIC SHOWCASE VERSION – CONFIDENTIAL IMPLEMENTATION REDACTED
# =============================================================================
#
# This file is a sanitized, non-functional skeleton of a real internal tool.
# 
# What has been removed / replaced:
#   • All real endpoint paths
#   • Business-specific field names (SE, apurement, articles, factures…)
#   • Real data shapes & response parsing logic
#   • Any sensitive variable names & constants
#   • Actual business rules & calculations
#
# What remains:
#   • General PyQt6 UI layout & styling pattern
#   • Search → fetch → display → local filter → action flow
#   • Authentication via Bearer token (pattern only)
#   • Typical error handling & user feedback style
#
# This version **does NOT work** and is published only to demonstrate:
#   • Qt interface design approach
#   • Modern PyQt6 + requests + clean layout usage
#   • Local client-side filtering pattern
#
# The real implementation remains private per NDA.
# Do NOT copy-paste or reuse this structure for similar business domains
# without explicit written permission.
#
# =============================================================================

import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# Fake constant – real value is confidential
API_BASE_URL = "https://example.com/api/v1"  # placeholder only


class ConfidentialDataManager(QWidget):
    """Showcase version – real logic intentionally hidden"""

    def __init__(self, auth_token: str):
        super().__init__()
        self.token = auth_token
        self.api_base = API_BASE_URL
        self._cached_data = None   # Placeholder for real response data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # ── Search bar ───────────────────────────────────────────────
        header = QHBoxLayout()
        
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Enter reference number (demo format: XXX-2024-123)…")
        self.search_field.setFixedHeight(40)
        self.search_field.setStyleSheet(
            "border: 1px solid #E5E7EB; border-radius: 8px; padding: 5px 15px;"
        )

        btn_search = QPushButton("🔍 Search")
        btn_search.setFixedHeight(40)
        btn_search.setStyleSheet(
            "background-color: #6366F1; color: white; border-radius: 8px; "
            "padding: 0 20px; font-weight: bold;"
        )
        btn_search.clicked.connect(self.on_search_clicked)

        header.addWidget(self.search_field)
        header.addWidget(btn_search)
        layout.addLayout(header)

        # ── Info / status card ───────────────────────────────────────
        self.card = QFrame()
        self.card.setStyleSheet("background-color: white; border: 1px solid #E5E7EB; border-radius: 12px;")
        self.card.setFixedHeight(120)
        
        card_layout = QHBoxLayout(self.card)
        self.status_label = QLabel("Search a reference to see summary")
        self.status_label.setStyleSheet("font-size: 16px; color: #4B5563;")
        
        self.action_button = QPushButton("Perform Action")
        self.action_button.setFixedSize(180, 40)
        self.action_button.setStyleSheet(
            "background-color: #10B981; color: white; border-radius: 8px; font-weight: bold;"
        )
        self.action_button.setVisible(False)
        self.action_button.clicked.connect(self.on_action_requested)

        card_layout.addWidget(self.status_label)
        card_layout.addStretch()
        card_layout.addWidget(self.action_button)
        layout.addWidget(self.card)

        # ── Two tables side by side ──────────────────────────────────
        tables_layout = QHBoxLayout()

        # Left table (main entities)
        left = QVBoxLayout()
        left.addWidget(QLabel("<b>📊 Main Entities Overview</b>"))
        self.table_main = self._create_table(["ID / Ref", "Initial", "Used", "Remaining"])
        self.table_main.itemSelectionChanged.connect(self.on_main_item_selected)
        left.addWidget(self.table_main)

        # Right table (related records)
        right = QVBoxLayout()
        right.addWidget(QLabel("<b>📋 Related Records</b>"))
        self.table_details = self._create_table(["Number", "Date", "Ref", "Quantity"])
        right.addWidget(self.table_details)

        tables_layout.addLayout(left, 3)
        tables_layout.addLayout(right, 2)
        layout.addLayout(tables_layout)

    def _create_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setStyleSheet("background-color: white; border: 1px solid #E5E7EB; border-radius: 8px;")
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

    def on_search_clicked(self):
        """Placeholder – real version calls protected API"""
        ref = self.search_field.text().strip()
        if not ref:
            return

        # ── Real version does something like this (redacted) ──
        # response = requests.get(f"{self.api_base}/ confidential/path/{ref}", ...)
        # self._cached_data = response.json()
        # self._update_ui(self._cached_data)

        QMessageBox.information(
            self, "Demo mode",
            "This is a showcase version.\n\nReal search & data loading logic is hidden for confidentiality reasons."
        )

    def _update_ui(self, data: dict):
        """Real update logic removed – UI skeleton only"""
        self.status_label.setText(
            "<b>Reference:</b> XXX-XXXX-XXX<br>"
            "<span style='color: #10B981;'>Status: example</span>"
        )
        self.action_button.setVisible(True)

        # Would fill tables here (removed)

    def on_main_item_selected(self):
        """Real client-side filtering logic removed"""
        # Would filter second table according to selected row (removed)
        pass

    def on_action_requested(self):
        """Real action (POST / close / etc.) removed"""
        QMessageBox.information(
            self, "Demo",
            "This action button would trigger a protected endpoint.\n\n"
            "Implementation hidden per client NDA."
        )


# ── Usage example (demo only) ────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = ConfidentialDataManager("fake-jwt-token-for-demo")
    window.setWindowTitle("Confidential Manager – Showcase Only")
    window.resize(1100, 750)
    window.show()
    sys.exit(app.exec())