import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QAbstractItemView, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

# Placeholder – real base URL is confidential
API_BASE_URL = "https://example.com/api/v1"


class BackgroundApiWorker(QThread):
    """Generic worker for async HTTP GET – demo only"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url, params=None, headers=None):
        super().__init__()
        self.url = url
        self.params = params or {}
        self.headers = headers or {}

    def run(self):
        try:
            resp = requests.get(self.url, params=self.params, headers=self.headers, timeout=6)
            if resp.status_code == 200:
                self.finished.emit(resp.json())
            else:
                self.error.emit(f"Server error {resp.status_code}")
        except Exception as e:
            self.error.emit(str(e))


class GenericItemListView(QWidget):
    """Showcase version – real inventory logic hidden"""

    def __init__(self, auth_token: str, user_role: str = "standard"):
        super().__init__()
        self.token = auth_token
        self.role = user_role.lower()
        self.api_base = API_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Visual helpers
        self.red = QColor("#EF4444")
        self.green_light = QColor("#F0FDF4")
        self.success_bg = QColor("#DCFCE7")
        self.grey = QColor("#6B7280")
        self.bold_font = QFont(); self.bold_font.setBold(True)
        self.italic_font = QFont(); self.italic_font.setItalic(True)

        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._execute_search)

        self.init_ui()
        self._show_initial_placeholder()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(24)

        # Title
        title = QLabel("Item Overview – Demo")
        title.setStyleSheet("font-size: 28px; font-weight: 600; color: #111827;")
        layout.addWidget(title)

        # Filters + export
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(16)

        input_style = """
            QLineEdit {
                padding: 10px 14px; border: 1px solid #D1D5DB; border-radius: 8px;
                background: white; font-size: 13px; min-width: 220px;
            }
            QLineEdit:focus { border-color: #6366F1; }
        """

        self.filter_field_1 = QLineEdit()
        self.filter_field_1.setPlaceholderText("Filter by code...")
        self.filter_field_1.setStyleSheet(input_style)
        self.filter_field_1.textChanged.connect(self._on_filter_changed)

        self.filter_field_2 = QLineEdit()
        self.filter_field_2.setPlaceholderText("Filter by name...")
        self.filter_field_2.setStyleSheet(input_style)
        self.filter_field_2.textChanged.connect(self._on_filter_changed)

        self.btn_export = QPushButton("Export CSV")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background: #10B981; color: white; border-radius: 8px;
                padding: 10px 22px; font-weight: 600;
            }
            QPushButton:hover { background: #059669; }
        """)
        self.btn_export.clicked.connect(self._export_placeholder)

        filter_bar.addWidget(QLabel("Code:"))
        filter_bar.addWidget(self.filter_field_1)
        filter_bar.addSpacing(16)
        filter_bar.addWidget(QLabel("Name:"))
        filter_bar.addWidget(self.filter_field_2)
        filter_bar.addStretch()
        filter_bar.addWidget(self.btn_export)

        layout.addLayout(filter_bar)

        # Table container
        table_frame = QFrame()
        table_frame.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E5E7EB;")
        table_vbox = QVBoxLayout(table_frame)
        table_vbox.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #F3F4F6; }
            QHeaderView::section {
                background: white; padding: 12px; border: none;
                border-bottom: 2px solid #E5E7EB; font-weight: bold;
                color: #6B7280; font-size: 11px;
            }
        """)

        table_vbox.addWidget(self.table)
        layout.addWidget(table_frame, stretch=1)

    def _on_filter_changed(self):
        self.debounce_timer.stop()
        self.debounce_timer.start(450)

    def _show_initial_placeholder(self):
        self._set_placeholder("Enter a code or name to view items.")

    def _set_placeholder(self, message: str):
        self.table.blockSignals(True)
        self.table.clearSpans()

        cols = ["CODE", "NAME", "GROUP", "LOCATION", "VALUE", "QUANTITY"]
        if self.role == "manager":
            cols.append("COST")

        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setRowCount(1)
        self.table.setSpan(0, 0, 1, len(cols))

        item = QTableWidgetItem(message)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setForeground(self.grey)
        item.setFont(self.italic_font)
        item.setFlags(Qt.ItemFlag.NoItemFlags)

        self.table.setItem(0, 0, item)
        self._apply_table_styles()
        self.table.blockSignals(False)

    def _apply_table_styles(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        if self.table.columnCount() >= 5:
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(4, 110)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(5, 90)

    def _execute_search(self):
        val1 = self.filter_field_1.text().strip()
        val2 = self.filter_field_2.text().strip()

        if not val1 and not val2:
            self._show_initial_placeholder()
            return

        # In real version: self.worker = BackgroundApiWorker(...)
        # Here we simulate
        QMessageBox.information(self, "Demo", 
                                "This would launch an async search.\n\n"
                                "Real API call & results parsing hidden.")

    def _export_placeholder(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export", f"Items_{datetime.now():%Y%m%d}.csv", "CSV (*.csv)"
        )
        if path:
            QMessageBox.information(self, "Demo", 
                                    "Export would be downloaded here.\n"
                                    "Real file generation hidden.")


# ── Demo launcher ───────────────────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = GenericItemListView("fake-token", user_role="manager")
    w.setWindowTitle("Item List – Showcase Only")
    w.resize(1180, 740)
    w.show()
    sys.exit(app.exec())