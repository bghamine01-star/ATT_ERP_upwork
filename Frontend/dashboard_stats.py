import requests
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Fake base – real URL is confidential
API_BASE_URL = "https://example.com/api/v1"

# Matplotlib global style (clean & modern)
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


class KPICard(QFrame):
    """Modern KPI card with left accent bar and shadow – showcase only"""

    def __init__(self, title: str, initial_value: str = "—", accent="#6366F1"):
        super().__init__()
        self.setMinimumHeight(130)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 14px;
                border: 1px solid #E5E7EB;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 20, 0)

        # Accent bar
        bar = QFrame()
        bar.setFixedWidth(6)
        bar.setStyleSheet(f"background-color: {accent}; border-radius: 14px 0 0 14px;")

        # Text content
        text_box = QVBoxLayout()
        text_box.setContentsMargins(24, 16, 12, 16)

        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet("color: #6B7280; font-size: 12px; font-weight: 700; letter-spacing: 0.4px;")

        self.lbl_value = QLabel(initial_value)
        self.lbl_value.setStyleSheet("color: #1F2937; font-size: 26px; font-weight: 800;")

        text_box.addWidget(lbl_title)
        text_box.addWidget(self.lbl_value)

        layout.addWidget(bar)
        layout.addLayout(text_box)
        layout.addStretch()

    def set_value(self, text: str):
        self.lbl_value.setText(text)


class DashboardDemo(QMainWindow):
    """Public showcase – real financial analytics redacted"""

    def __init__(self, auth_token: str):
        super().__init__()
        self.token = auth_token
        self.api_base = API_BASE_URL

        self.setWindowTitle("Analytics Dashboard – Demo")
        self.resize(1180, 820)
        self.setStyleSheet("background-color: #F8FAFC;")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(48, 32, 48, 48)
        layout.setSpacing(28)

        # Header + year selector
        hdr = QHBoxLayout()
        title_box = QVBoxLayout()
        main_title = QLabel("Performance Overview")
        main_title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A;")
        sub = QLabel("Monthly & yearly summary")
        sub.setStyleSheet("font-size: 14px; color: #64748B;")
        title_box.addWidget(main_title)
        title_box.addWidget(sub)

        self.year_combo = QComboBox()
        self.year_combo.addItems([str(y) for y in range(2023, 2031)])
        self.year_combo.setCurrentText("2025")
        self.year_combo.setFixedSize(130, 42)
        self.year_combo.setStyleSheet("""
            QComboBox {
                padding-left: 16px; border-radius: 10px; border: 1px solid #CBD5E1;
                background: white; font-weight: 600; color: #334155;
            }
            QComboBox::drop-down { width: 32px; border: none; }
        """)
        self.year_combo.currentTextChanged.connect(self.refresh)

        hdr.addLayout(title_box)
        hdr.addStretch()
        hdr.addWidget(self.year_combo)
        layout.addLayout(hdr)

        # KPI cards row
        cards = QHBoxLayout()
        cards.setSpacing(24)

        self.card_a = KPICard("Metric A", "—", "#6366F1")
        self.card_b = KPICard("Metric B", "—", "#10B981")
        self.card_c = KPICard("Metric C", "—", "#F59E0B")

        cards.addWidget(self.card_a)
        cards.addWidget(self.card_b)
        cards.addWidget(self.card_c)
        layout.addLayout(cards)

        # Chart area
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #E2E8F0;
            }
        """)
        chart_vbox = QVBoxLayout(chart_frame)
        chart_vbox.setContentsMargins(24, 24, 24, 24)

        self.figure = Figure(figsize=(10, 5.2), facecolor='none')
        self.canvas = FigureCanvas(self.figure)
        chart_vbox.addWidget(self.canvas)

        layout.addWidget(chart_frame, stretch=1)

        # Hover annotation support
        self.line = None
        self.tooltip = None

        self.refresh()  # initial load

    def refresh(self):
        """Placeholder – real data fetch removed"""
        year = self.year_combo.currentText()

        # Fake / demo values (real version would call API)
        demo_values = {
            "a": 1245000.75,
            "b":  428000.20,
            "c":   15750.80
        }

        self.card_a.set_value(f"{demo_values['a']:,.2f}")
        self.card_b.set_value(f"{demo_values['b']:,.2f}")
        self.card_c.set_value(f"{demo_values['c']:,.2f}")

        # Build fake monthly data for chart
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        values = [120, 180, 240, 310, 420, 510, 480, 390, 340, 290, 220, 150]

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        self.line, = ax.plot(months, values, color="#4F46E5", linewidth=3.5,
                             marker='o', markersize=8, markerfacecolor='white',
                             markeredgewidth=2.2, zorder=3)

        ax.fill_between(months, values, color="#6366F1", alpha=0.10, zorder=1)

        ax.yaxis.grid(True, linestyle='--', color='#E2E8F0', alpha=0.7)
        ax.set_axisbelow(True)

        for spine in ['top', 'right', 'left']:
            ax.spines[spine].set_visible(False)
        ax.spines['bottom'].set_color('#CBD5E1')

        ax.tick_params(axis='both', labelsize=10, colors='#64748B')

        # Tooltip setup
        self.tooltip = ax.annotate(
            "", xy=(0,0), xytext=(14,14), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#4F46E5", lw=1.2),
            arrowprops=dict(arrowstyle="->", color="#4F46E5"),
            fontsize=11, fontweight='bold'
        )
        self.tooltip.set_visible(False)

        self.canvas.mpl_connect("motion_notify_event", self.on_hover)
        self.figure.tight_layout()
        self.canvas.draw()

    def on_hover(self, event):
        if event.inaxes != self.figure.axes[0]:
            return

        if self.line is None:
            return

        cont, ind = self.line.contains(event)
        if cont:
            idx = ind["ind"][0]
            x, y = self.line.get_data()
            val = y[idx]

            self.tooltip.xy = (x[idx], y[idx])
            self.tooltip.set_text(f"{val:,.1f}")
            self.tooltip.set_visible(True)
            self.canvas.draw_idle()
        else:
            if self.tooltip.get_visible():
                self.tooltip.set_visible(False)
                self.canvas.draw_idle()


# ── Demo launcher ───────────────────────────────────────────────────────
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = DashboardDemo("fake-auth-token")
    window.show()
    sys.exit(app.exec())