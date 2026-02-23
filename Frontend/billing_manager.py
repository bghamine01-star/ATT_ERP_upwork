from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QLineEdit, QDoubleSpinBox, QMessageBox, QDialog, 
    QFormLayout, QTabWidget, QFileDialog, QSpinBox
)
from PyQt6.QtCore import Qt
from datetime import datetime, date
import requests

# Placeholder only – real base URL is confidential
API_BASE_URL = "https://example.com/api/v1"


class ConfidentialBillingInterface(QWidget):
    """Showcase version – real billing & invoicing logic hidden"""

    def __init__(self, auth_token: str):
        super().__init__()
        self.token = auth_token
        self.api_base = API_BASE_URL
        self.selected_entity_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        title = QLabel("Monthly Record Manager – Demo")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E5E7EB; background: white; border-radius: 8px; }
            QTabBar::tab { padding: 12px 25px; font-weight: bold; font-size: 14px; 
                           background: #F3F4F6; border: 1px solid #E5E7EB;
                           border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: white; color: #6366F1; border-bottom: 2px solid #6366F1; }
        """)
        layout.addWidget(self.tabs)

        # Tab 1 – Create new
        self.tab_create = QWidget()
        self._setup_create_ui()
        self.tabs.addTab(self.tab_create, "🆕 New Entry")

        # Tab 2 – History & export
        self.tab_history = QWidget()
        self._setup_history_ui()
        self.tabs.addTab(self.tab_history, "📂 History & Export")

    def _setup_create_ui(self):
        layout = QVBoxLayout(self.tab_create)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Config button (example: rate or parameter setup)
        top_bar = QHBoxLayout()
        btn_config = QPushButton("⚙️ Configure Parameter")
        btn_config.clicked.connect(self._open_config_dialog)
        top_bar.addStretch()
        top_bar.addWidget(btn_config)
        layout.addLayout(top_bar)

        # Filter controls
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 10px;")
        f_layout = QHBoxLayout(filter_frame)

        self.combo_month = QComboBox()
        self.combo_month.addItems(["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        self.combo_month.setCurrentIndex(date.today().month - 1)

        self.spin_year = QSpinBox()
        self.spin_year.setRange(2020, 2030)
        self.spin_year.setValue(datetime.now().year)

        btn_load = QPushButton("🔍 Load Eligible Entries")
        btn_load.setStyleSheet("background: #6366F1; color: white; padding: 10px 20px;")
        btn_load.clicked.connect(self._load_eligible_items)

        f_layout.addWidget(QLabel("Month:"))
        f_layout.addWidget(self.combo_month)
        f_layout.addWidget(QLabel("Year:"))
        f_layout.addWidget(self.spin_year)
        f_layout.addStretch()
        f_layout.addWidget(btn_load)
        layout.addWidget(filter_frame)

        # Main table
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(4)
        self.table_items.setHorizontalHeaderLabels(["Name", "Code", "Status", "Select"])
        self.table_items.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_items)

        # Detail / action panel (appears after selection)
        self.detail_panel = QFrame()
        self.detail_panel.setVisible(False)
        self.detail_panel.setStyleSheet("background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 10px; padding: 15px;")
        p_layout = QHBoxLayout(self.detail_panel)

        self.field_ref = QLineEdit()
        self.field_ref.setPlaceholderText("Reference / Number")

        self.spin_discount = QDoubleSpinBox()
        self.spin_discount.setSuffix(" %")
        self.spin_discount.setRange(0, 100)

        self.combo_term = QComboBox()
        self.combo_term.addItems(["Term A", "Term B", "Term C"])
        self.combo_term.setEditable(True)

        self.spin_weight = QDoubleSpinBox()
        self.spin_weight.setSuffix(" unit")
        self.spin_weight.setRange(0, 20000)

        btn_generate = QPushButton("✔ Confirm & Generate")
        btn_generate.setStyleSheet("background: #10B981; color: white; font-weight: bold;")
        btn_generate.clicked.connect(self._process_creation)

        for lbl, w in [
            ("Ref:", self.field_ref),
            ("Discount:", self.spin_discount),
            ("Term:", self.combo_term),
            ("Weight:", self.spin_weight),
        ]:
            p_layout.addWidget(QLabel(lbl))
            p_layout.addWidget(w)
        p_layout.addWidget(btn_generate)
        layout.addWidget(self.detail_panel)

    def _setup_history_ui(self):
        layout = QVBoxLayout(self.tab_history)
        layout.setContentsMargins(20, 20, 20, 20)

        # Filter
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 10px;")
        f_layout = QHBoxLayout(filter_frame)

        self.hist_month = QComboBox()
        self.hist_month.addItems(["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        self.hist_month.setCurrentIndex(date.today().month - 1)

        self.hist_year = QSpinBox()
        self.hist_year.setRange(2020, 2030)
        self.hist_year.setValue(datetime.now().year)

        btn_load_hist = QPushButton("🔍 Search Records")
        btn_load_hist.setStyleSheet("background: #4B5563; color: white;")
        btn_load_hist.clicked.connect(self._load_history)

        f_layout.addWidget(QLabel("Month:"))
        f_layout.addWidget(self.hist_month)
        f_layout.addWidget(QLabel("Year:"))
        f_layout.addWidget(self.hist_year)
        f_layout.addStretch()
        f_layout.addWidget(btn_load_hist)
        layout.addWidget(filter_frame)

        # History table
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(5)
        self.table_history.setHorizontalHeaderLabels(["Ref", "Date", "Entity", "Value", "Actions"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_history)

    def _open_config_dialog(self):
        """Showcase config dialog – real parameter logic hidden"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Parameter Configuration")
        layout = QVBoxLayout(dialog)

        lbl = QLabel(f"Settings for: {self.combo_month.currentText()} {self.spin_year.value()}")
        lbl.setStyleSheet("font-weight: bold; color: #6366F1;")
        layout.addWidget(lbl)

        spin_value = QDoubleSpinBox()
        spin_value.setRange(0, 1000)
        spin_value.setDecimals(4)
        spin_value.setValue(1.2345)

        form = QFormLayout()
        form.addRow("Value to configure:", spin_value)
        layout.addLayout(form)

        btn = QPushButton("Save")
        btn.clicked.connect(lambda: QMessageBox.information(dialog, "Demo", "Configuration saved (placeholder)."))
        layout.addWidget(btn)

        dialog.exec()

    def _load_eligible_items(self):
        """Placeholder – real eligibility check & API call removed"""
        self.detail_panel.setVisible(False)
        self.table_items.setRowCount(0)

        # In real version: API call + validation of period closure
        QMessageBox.information(self, "Demo mode", 
                                "This would load eligible records from server.\n\n"
                                "Period validation & real data fetch hidden for confidentiality.")

    def _process_creation(self):
        """Placeholder – real generation logic removed"""
        if not self.field_ref.text().strip():
            QMessageBox.warning(self, "Required", "Reference is required.")
            return

        QMessageBox.information(self, "Demo", 
                                "This would generate & save a new record.\n"
                                "All business rules and API calls are redacted.")

        self.detail_panel.setVisible(False)
        self.field_ref.clear()

    def _load_history(self):
        """Placeholder – real history fetch removed"""
        self.table_history.setRowCount(0)
        QMessageBox.information(self, "Demo", 
                                "This would load historical records.\n"
                                "Real filtering, amounts & export logic hidden.")

    # Download placeholders (real file content & naming hidden)
    def _download_document(self, doc_type: str, record_id):
        QMessageBox.information(self, "Export demo", 
                                f"This would download a {doc_type.upper()} file for record #{record_id}.\n"
                                "Actual file generation & content redacted.")


# ── Demo launch ───────────────────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = ConfidentialBillingInterface("fake-token")
    w.setWindowTitle("Billing Interface – Showcase Only")
    w.resize(1100, 780)
    w.show()
    sys.exit(app.exec())