import requests
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QLineEdit, QDateEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QCompleter, QSpinBox, QDoubleSpinBox, QMessageBox,
    QFormLayout
)
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QColor


# Placeholder – real base URL is confidential
API_BASE_URL = "https://example.com/api/v1"


class DocumentCreationForm(QWidget):
    """Showcase version – real delivery/sales creation logic hidden"""

    def __init__(self, auth_token: str):
        super().__init__()
        self.token = auth_token
        self.api_base = API_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.selected_entity = None
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        # Title
        title = QLabel("New Document")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #111827;")
        main_layout.addWidget(title)

        # Header card (entity + date + ref)
        header = QFrame()
        header.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E5E7EB;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 24, 24, 24)

        # Left: entity search
        left = QVBoxLayout()
        self.entity_input = QLineEdit()
        self.entity_input.setPlaceholderText("Search entity (min 4 chars)…")
        self.entity_input.setMinimumWidth(320)

        completer = QCompleter(self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.entity_input.setCompleter(completer)

        self.entity_input.textChanged.connect(self._on_entity_search)
        completer.activated.connect(self._on_entity_chosen)
        self.entity_input.returnPressed.connect(self._try_select_entity)

        details_lbl = QLabel("Enter name to see details")
        details_lbl.setStyleSheet("color: #6B7280; font-size: 13px;")

        left.addWidget(QLabel("<b>RECIPIENT</b>"))
        left.addWidget(self.entity_input)
        left.addWidget(details_lbl)
        h_layout.addLayout(left, 2)

        h_layout.addStretch()

        # Right: document ref + date
        right = QVBoxLayout()
        self.doc_ref = QLineEdit()
        self.doc_ref.setPlaceholderText("Ref: DOC-202X-XXX")
        self.doc_ref.setMinimumWidth(160)

        self.doc_date = QDateEdit(date.today())
        self.doc_date.setCalendarPopup(True)
        self.doc_date.setMinimumWidth(160)

        right.addWidget(QLabel("<b>DOCUMENT REF</b>"))
        right.addWidget(self.doc_ref)
        right.addWidget(QLabel("<b>DATE</b>"))
        right.addWidget(self.doc_date)
        h_layout.addLayout(right, 1)

        main_layout.addWidget(header)

        # Items table
        table_frame = QFrame()
        table_frame.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E5E7EB;")
        table_vbox = QVBoxLayout(table_frame)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Code", "Description", "Avail.", "Qty", "Discount %", "Line Total"])
        #self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("border: none; gridline-color: #F3F4F6;")
        self.table.setFixedHeight(380)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Add Line")
        add_btn.setStyleSheet("background: #F3F4F6; color: #374151; padding: 10px; border-radius: 6px;")
        add_btn.clicked.connect(self._add_item_row)

        remove_btn = QPushButton("- Remove Selected")
        remove_btn.setStyleSheet("background: #FEE2E2; color: #991B1B; padding: 10px; border-radius: 6px;")
        remove_btn.clicked.connect(self._remove_selected_row)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()

        table_vbox.addWidget(self.table)
        table_vbox.addLayout(btn_row)

        main_layout.addWidget(table_frame)

        # Totals summary
        totals_widget = QWidget()
        totals_h = QHBoxLayout(totals_widget)
        totals_card = QFrame()
        totals_card.setFixedWidth(380)
        totals_card.setStyleSheet("background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px;")

        form = QFormLayout(totals_card)
        form.setSpacing(10)

        self.lbl_gross = QLabel("0.00")
        self.lbl_discount = QLabel("0.00")
        self.lbl_net = QLabel("0.00")
        self.lbl_net.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")

        form.addRow("Gross Total:", self.lbl_gross)
        form.addRow("Total Discount:", self.lbl_discount)
        form.addRow("Net Amount:", self.lbl_net)

        totals_h.addStretch()
        totals_h.addWidget(totals_card)
        main_layout.addWidget(totals_widget)

        # Submit
        submit_btn = QPushButton("✔ Create Document")
        submit_btn.setMinimumHeight(52)
        submit_btn.setStyleSheet("background: #111827; color: white; font-weight: bold; font-size: 16px; border-radius: 8px;")
        submit_btn.clicked.connect(self._submit_document)
        main_layout.addWidget(submit_btn)

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _on_entity_search(self, text):
        if len(text) < 4:
            return
        # Placeholder – real async client search hidden
        pass

    def _on_entity_chosen(self, name):
        # Placeholder – real entity selection hidden
        self.lbl_client_details.setText(f"Selected: {name}")

    def _try_select_entity(self):
        pass

    def _add_item_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Code with completer
        code_edit = QLineEdit()
        code_edit.setPlaceholderText("Enter code…")
        completer = QCompleter(self)
        code_edit.setCompleter(completer)
        code_edit.textChanged.connect(lambda t: self._update_item_completer(t, completer))
        code_edit.editingFinished.connect(lambda: self._check_item(row))
        self.table.setCellWidget(row, 0, code_edit)

        # Init other cells
        for col in [1, 2, 5]:
            it = QTableWidgetItem("-" if col == 1 else "0")
            self.table.setItem(row, col, it)

        qty = QSpinBox()
        qty.setRange(1, 99999)
        qty.valueChanged.connect(self._recalculate_totals)
        self.table.setCellWidget(row, 3, qty)

        disc = QDoubleSpinBox()
        disc.setRange(0, 100)
        disc.setSuffix(" %")
        disc.valueChanged.connect(self._recalculate_totals)
        self.table.setCellWidget(row, 4, disc)

        code_edit.setFocus()

    def _remove_selected_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self._recalculate_totals()
        else:
            QMessageBox.warning(self, "Selection", "Select a row first.")

    def _update_item_completer(self, text, completer):
        pass  # Placeholder – real async item search hidden

    def _check_item(self, row):
        pass  # Placeholder – real item lookup & stock check hidden

    def _recalculate_totals(self):
        gross = 0.0
        disc_total = 0.0

        for r in range(self.table.rowCount()):
            price = 0.0  # Would come from data role
            qty = self.table.cellWidget(r, 3).value()
            disc_pct = self.table.cellWidget(r, 4).value()

            line_gross = price * qty
            line_disc = line_gross * (disc_pct / 100)

            self.table.item(r, 5).setText(f"{line_gross:,.2f}")

            gross += line_gross
            disc_total += line_disc

        self.lbl_gross.setText(f"{gross:,.2f}")
        self.lbl_discount.setText(f"{disc_total:,.2f}")
        self.lbl_net.setText(f"{gross:,.2f}")  # In demo: no net adjustment

    def _submit_document(self):
        QMessageBox.information(self, "Demo", 
                                "This would create & send the document.\n\n"
                                "Real validation, payload, and backend call hidden.")


# ── Demo ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = DocumentCreationForm("fake-token")
    w.setWindowTitle("Document Creation – Showcase")
    w.resize(1100, 850)
    w.show()
    sys.exit(app.exec())