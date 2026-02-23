# =============================================================================
# DEMO / PUBLIC SHOWCASE VERSION – CONFIDENTIAL STOCK MOVEMENTS MANAGEMENT REDACTED
# =============================================================================
#
# This is a NON-FUNCTIONAL skeleton / style demonstration of a modern PyQt6
# stock movements / inventory adjustment interface using collapsible banners.
#
# Removed or generalized for NDA / confidentiality reasons:
#   • All real API endpoints and payload structures
#   • Business-specific concepts (SE lots, bon de livraison, prix achat/vente…)
#   • Domain field names (numero_se, fournisseur, emplacement, categorie…)
#   • Real validation rules, stock deduction logic, FIFO, date restrictions
#   • Exact error messages and success feedback tied to business
#
# Preserved to showcase your UI/UX & PyQt6 skills:
#   • Collapsible ManagementBanner pattern with toggle animation feel
#   • Expand/collapse sections with smooth UX
#   • Dynamic table + add/remove row pattern
#   • Role-based conditional section visibility
#   • Form + table + submit flow with visual feedback
#   • Clean, modern cards + consistent styling language
#
# This code DOES NOT WORK and is published ONLY to demonstrate:
#   • Modular collapsible form sections
#   • Professional inventory adjustment UX
#   • Dynamic table editing + live feedback
#   • Role-aware UI composition
#
# Real business logic, endpoints, stock rules, and transaction safety remain private.
# Do NOT reuse this structure, banner style, or naming for inventory/WMS/ERP tools
# without explicit written authorization.
#
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QScrollArea, QLineEdit, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor


# Placeholder – real base URL is confidential
API_BASE_URL = "https://example.com/api/v1"


class CollapsibleSection(QFrame):
    """Modern collapsible card/section with title + toggle button – demo only"""

    def __init__(self, title: str, icon: str = "◼", accent="#6366F1"):
        super().__init__()
        self.setStyleSheet("QFrame { background: white; border: 1px solid #E5E7EB; border-radius: 12px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QHBoxLayout()
        header.setContentsMargins(20, 16, 20, 16)

        title_lbl = QLabel(f"{icon}  {title}")
        title_lbl.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {accent};")

        self.toggle_btn = QPushButton("Open Tool")
        self.toggle_btn.setFixedWidth(120)
        self.toggle_btn.setStyleSheet("background: #F3F4F6; border-radius: 6px; padding: 8px; font-size: 13px;")
        self.toggle_btn.clicked.connect(self.toggle)

        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(self.toggle_btn)

        layout.addLayout(header)

        # Content area (initially hidden)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 0, 20, 20)
        self.content_layout.setSpacing(16)
        self.content.setVisible(False)
        layout.addWidget(self.content)

    def toggle(self):
        visible = self.content.isVisible()
        self.content.setVisible(not visible)
        self.toggle_btn.setText("Close" if not visible else "Open Tool")


class StockMovementsDemo(QWidget):
    """Public showcase – real stock management logic removed"""

    def __init__(self, auth_token: str, user_role: str = "user"):
        super().__init__()
        self.token = auth_token
        self.role = user_role.lower()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel("Stock Movements – Demo")
        title.setStyleSheet("font-size: 26px; font-weight: 600; color: #111827;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(24)

        # ── Section 1: Import / Add ─────────────────────────────────────
        self.section_add = CollapsibleSection("Import New Batch", "📥", "#10B981")
        self._setup_add_section()
        container_layout.addWidget(self.section_add)

        # ── Section 2: Modify ────────────────────────────────────────────
        self.section_modify = CollapsibleSection("Modify Existing Item", "📝", "#6366F1")
        self._setup_modify_section()
        container_layout.addWidget(self.section_modify)

        # ── Section 3: Remove ────────────────────────────────────────────
        self.section_remove = CollapsibleSection("Remove Batch", "🗑", "#EF4444")
        self._setup_remove_section()
        container_layout.addWidget(self.section_remove)

        # ── Section 4: Manager-only price adjustment ─────────────────────
        if self.role == "manager":
            self.section_prices = CollapsibleSection("Purchase Price Management (Manager)", "💰", "#F59E0B")
            self._setup_price_section()
            container_layout.addWidget(self.section_prices)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _setup_add_section(self):
        layout = self.section_add.content_layout

        # Header inputs
        hdr = QHBoxLayout()
        self.add_ref = QLineEdit(); self.add_ref.setPlaceholderText("Batch Ref")
        self.add_date = QDateEdit(QDate.currentDate()); self.add_date.setCalendarPopup(True)
        self.add_source = QLineEdit(); self.add_source.setPlaceholderText("Source")
        hdr.addWidget(QLabel("Ref:")); hdr.addWidget(self.add_ref)
        hdr.addWidget(QLabel("Date:")); hdr.addWidget(self.add_date)
        hdr.addWidget(QLabel("Source:")); hdr.addWidget(self.add_source)
        layout.addLayout(hdr)

        # Items table
        self.add_table = QTableWidget(1, 6)
        self.add_table.setHorizontalHeaderLabels(["Code", "Name", "Group", "Location", "Price", "Quantity"])
        self.add_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.add_table)

        # Action buttons
        btns = QHBoxLayout()
        add_row = QPushButton("+ Add Row"); add_row.clicked.connect(lambda: self.add_table.insertRow(self.add_table.rowCount()))
        del_row = QPushButton("- Remove Row"); del_row.clicked.connect(self._remove_selected_row_demo)
        submit = QPushButton("✔ Submit Import"); submit.setStyleSheet("background: #10B981; color: white;")
        submit.clicked.connect(self._submit_placeholder)
        btns.addWidget(add_row); btns.addWidget(del_row); btns.addStretch(); btns.addWidget(submit)
        layout.addLayout(btns)

    def _setup_modify_section(self):
        layout = self.section_modify.content_layout

        search = QHBoxLayout()
        ref_in = QLineEdit(); ref_in.setPlaceholderText("Batch Ref")
        item_in = QLineEdit(); item_in.setPlaceholderText("Item Code")
        load_btn = QPushButton("🔍 Load"); load_btn.clicked.connect(self._load_placeholder)
        search.addWidget(ref_in); search.addWidget(item_in); search.addWidget(load_btn)
        layout.addLayout(search)

        # Form fields (disabled until loaded)
        form = QFrame(); form.setEnabled(False)
        form_layout = QVBoxLayout(form)
        for lbl, ph in [
            ("Name:", "Item name…"),
            ("Group:", "Category…"),
            ("Location:", "Shelf…"),
            ("Price:", "0.00"),
            ("Source:", "Supplier…")
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(lbl))
            edit = QLineEdit(); edit.setPlaceholderText(ph)
            row.addWidget(edit)
            form_layout.addLayout(row)

        save = QPushButton("💾 Save Changes"); save.clicked.connect(self._save_placeholder)
        form_layout.addWidget(save)
        layout.addWidget(form)

    def _setup_remove_section(self):
        layout = self.section_remove.content_layout

        search = QHBoxLayout()
        num_in = QLineEdit(); num_in.setPlaceholderText("Enter batch ref…")
        inspect = QPushButton("🔎 Inspect Content"); inspect.clicked.connect(self._inspect_placeholder)
        search.addWidget(num_in); search.addWidget(inspect)
        layout.addLayout(search)

        preview = QTableWidget(0, 3)
        preview.setHorizontalHeaderLabels(["Code", "Name", "Quantity"])
        preview.setMaximumHeight(220)
        preview.setVisible(False)
        layout.addWidget(preview)

        delete_btn = QPushButton("🗑 Permanently Remove Batch")
        delete_btn.setEnabled(False)
        delete_btn.clicked.connect(self._delete_placeholder)
        layout.addWidget(delete_btn)

    def _setup_price_section(self):
        layout = self.section_prices.content_layout

        search = QHBoxLayout()
        batch_in = QLineEdit(); batch_in.setPlaceholderText("Batch ref for price update…")
        load = QPushButton("📊 Load Prices"); load.clicked.connect(self._load_prices_placeholder)
        search.addWidget(batch_in); search.addWidget(load)
        layout.addLayout(search)

        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Code", "Name", "Purchase Price (Editable)"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)

        save = QPushButton("✅ Save All Prices")
        save.setEnabled(False)
        save.clicked.connect(self._save_prices_placeholder)
        layout.addWidget(save)

    def _remove_selected_row_demo(self):
        row = self.add_table.currentRow()
        if row >= 0:
            self.add_table.removeRow(row)

    def _submit_placeholder(self):
        QMessageBox.information(self, "Demo", "This would submit the batch import.\nReal API call & validation hidden.")

    def _load_placeholder(self):
        QMessageBox.information(self, "Demo", "This would load item data for modification.")

    def _save_placeholder(self):
        QMessageBox.information(self, "Demo", "This would save changes to the item.")

    def _inspect_placeholder(self):
        QMessageBox.information(self, "Demo", "This would preview batch content before removal.")

    def _delete_placeholder(self):
        QMessageBox.information(self, "Demo", "This would permanently delete the batch.")

    def _load_prices_placeholder(self):
        QMessageBox.information(self, "Demo", "This would load prices for bulk edit (manager only).")

    def _save_prices_placeholder(self):
        QMessageBox.information(self, "Demo", "This would save all updated purchase prices.")


# ── Demo launcher ───────────────────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = StockMovementsDemo("fake-token", user_role="manager")
    w.setWindowTitle("Stock Movements – Showcase Only")
    w.resize(1100, 900)
    w.show()
    sys.exit(app.exec())