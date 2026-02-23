from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QFrame, QMenu
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal
from PyQt6.QtGui import QAction


class NavSection(QWidget):
    """Collapsible navigation group with main button + sub-items – demo only"""

    def __init__(self, icon: str, label: str, sidebar):
        super().__init__()
        self.sidebar = sidebar
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Main toggle button
        self.btn = QPushButton(f"{icon}   {label}")
        self.btn.setCheckable(True)
        self.btn.setStyleSheet(self._main_btn_style())
        self.btn.clicked.connect(self.toggle_children)

        # Sub-items container
        self.children_frame = QFrame()
        self.children_layout = QVBoxLayout(self.children_frame)
        self.children_layout.setContentsMargins(32, 4, 0, 4)
        self.children_layout.setSpacing(2)
        self.children_frame.setVisible(False)

        layout.addWidget(self.btn)
        layout.addWidget(self.children_frame)

    def add_child(self, text: str, callback):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 16px;
                border: none;
                border-left: 2px solid transparent;
                color: #6B7280;
                font-size: 13px;
                background: transparent;
            }
            QPushButton:hover {
                color: #6366F1;
                border-left: 2px solid #6366F1;
                background: #F8FAFC;
            }
        """)
        btn.clicked.connect(callback)
        self.children_layout.addWidget(btn)
        return btn

    def toggle_children(self):
        visible = self.children_frame.isVisible()
        self.children_frame.setVisible(not visible)
        self.btn.setChecked(not visible)

    def _main_btn_style(self):
        return """
            QPushButton {
                text-align: left;
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                color: #374151;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #EEF2FF;
                color: #6366F1;
            }
            QPushButton:checked {
                background: #EEF2FF;
                color: #6366F1;
            }
        """


class ApplicationShell(QMainWindow):
    """Public demo – real dashboard shell redacted"""

    logout_requested = pyqtSignal()

    def __init__(self, auth_token: str, user_role: str = "user"):
        super().__init__()
        self.token = auth_token
        self.role = user_role.lower()
        self.sidebar_expanded = 240
        self.sidebar_collapsed = 68
        self.is_collapsed = False

        self.init_ui()
        self.show_default_content()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(self.sidebar_expanded)
        self.sidebar.setStyleSheet("background: #F9FAFB; border-right: 1px solid #E5E7EB;")
        sidebar_vbox = QVBoxLayout(self.sidebar)
        sidebar_vbox.setContentsMargins(12, 24, 12, 24)
        sidebar_vbox.setSpacing(8)

        # Toggle button
        self.btn_toggle = self._nav_button("≡", "")
        self.btn_toggle.clicked.connect(self.toggle_sidebar_width)
        sidebar_vbox.addWidget(self.btn_toggle)

        # ── Sections ─────────────────────────────────────────────────────
        self._add_section_title("Core Features")

        self.group_1 = NavSection("◼", "Module A", self)
        self.group_1.add_child("View List", self._placeholder_nav)
        self.group_1.add_child("Manage Items", self._placeholder_nav)
        sidebar_vbox.addWidget(self.group_1)

        self.group_2 = NavSection("◼", "Module B", self)
        self.group_2.add_child("Create Entry", self._placeholder_nav)
        self.group_2.add_child("Review Entries", self._placeholder_nav)
        sidebar_vbox.addWidget(self.group_2)

        self.btn_single = self._nav_button("◼", "Single Feature")
        self.btn_single.clicked.connect(self._placeholder_nav)
        sidebar_vbox.addWidget(self.btn_single)

        # Conditional section (manager only)
        if self.role == "manager":
            sidebar_vbox.addSpacing(24)
            self._add_section_title("Analytics")
            self.btn_analytics = self._nav_button("◼", "Overview")
            self.btn_analytics.clicked.connect(self._placeholder_nav)
            sidebar_vbox.addWidget(self.btn_analytics)

        # Bottom section
        sidebar_vbox.addStretch()
        self.btn_settings = self._nav_button("⚙", "Settings")
        self.btn_settings.clicked.connect(self._show_settings_menu)
        sidebar_vbox.addWidget(self.btn_settings)

        # ── Content Area ─────────────────────────────────────────────────
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_stack, stretch=1)

    def _nav_button(self, icon: str, text: str):
        btn = QPushButton(f"{icon}   {text}")
        btn.full_text = text
        btn.icon_only = icon
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                color: #374151;
                font-size: 14px;
            }
            QPushButton:hover { background: #EEF2FF; color: #6366F1; }
        """)
        return btn

    def _add_section_title(self, text: str):
        lbl = QLabel(text.upper())
        lbl.setStyleSheet("font-size: 10px; color: #9CA3AF; font-weight: bold; margin: 12px 0 4px 12px;")
        self.sidebar.layout().addWidget(lbl)

    def toggle_sidebar_width(self):
        current = self.sidebar.width()
        target = self.sidebar_collapsed if current == self.sidebar_expanded else self.sidebar_expanded
        self.is_collapsed = (target == self.sidebar_collapsed)

        anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
        anim.setDuration(240)
        anim.setStartValue(current)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()

        self.sidebar.setMaximumWidth(target)

        # Update button texts
        for i in range(self.sidebar.layout().count()):
            w = self.sidebar.layout().itemAt(i).widget()
            if isinstance(w, QPushButton) and hasattr(w, 'full_text'):
                w.setText(w.icon_only if self.is_collapsed else f"{w.icon_only}   {w.full_text}")
            elif isinstance(w, QLabel):
                w.setVisible(not self.is_collapsed)

    def _show_settings_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 6px;
            }
            QMenu::item {
                padding: 10px 32px 10px 20px;
                border-radius: 6px;
                color: #4B5563;
            }
            QMenu::item:selected {
                background: #F3F4F6;
                color: #6366F1;
            }
        """)

        if self.role == "manager":
            menu.addAction("Manage Users", self._placeholder_nav)
            menu.addSeparator()

        menu.addAction("Sign Out", self.logout_requested.emit)

        pos = self.btn_settings.mapToGlobal(self.btn_settings.rect().topRight()) + QPoint(12, 0)
        menu.exec(pos)

    def show_default_content(self):
        lbl = QLabel("Welcome – Select a feature from the sidebar")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 18px; color: #6B7280;")
        self.content_stack.addWidget(lbl)
        self.content_stack.setCurrentIndex(0)

    def _placeholder_nav(self):
        """Simulate page switch"""
        lbl = QLabel("Feature page placeholder\n\nReal content loading hidden")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 20px; color: #9CA3AF;")
        self.content_stack.addWidget(lbl)
        self.content_stack.setCurrentWidget(lbl)


# ── Demo ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = ApplicationShell("fake-token", user_role="manager")
    w.setWindowTitle("Application Shell – Showcase")
    w.resize(1280, 800)
    w.show()
    sys.exit(app.exec())