from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QSizePolicy, QGraphicsDropShadowEffect, QPushButton
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QCursor, QColor, QFont

from .widgets.heatmap_widget import HeatmapWidget
from .widgets.apps_widget import AppsWidget


# --- 辅助工具 ---
def format_duration_precise(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"


# --------------------------------------------------------
# 通用面板 (支持 交互式 Hover 或 纯静态展示)
# --------------------------------------------------------
class HoverPanel(QFrame):
    def __init__(self, parent=None, base_bg="rgba(10, 14, 23, 220)", hover_bg="rgba(18, 24, 35, 235)",
                 border_color="rgba(48, 54, 61, 200)", highlight_color="#1f6feb", radius=10,
                 interactive=True):
        super().__init__(parent)
        self.base_bg, self.hover_bg = base_bg, hover_bg
        self.border_color, self.highlight_color = border_color, highlight_color
        self.radius = radius
        self.interactive = interactive

        self._hovered, self._forced_highlight = False, False
        self._base_geometry = None

        if self.interactive:
            self.setAttribute(Qt.WA_Hover, True)
            self.setCursor(QCursor(Qt.PointingHandCursor))

            # 阴影
            self._shadow = QGraphicsDropShadowEffect(self)
            self._shadow.setBlurRadius(24)
            self._shadow.setOffset(0, 8)
            self._shadow.setColor(QColor(self.highlight_color).lighter(150))
            self._shadow.setEnabled(False)
            self.setGraphicsEffect(self._shadow)

            # 动画
            self._anim = QPropertyAnimation(self, b"geometry", self)
            self._anim.setDuration(130)
            self._anim.setEasingCurve(QEasingCurve.OutQuad)
        else:
            self.setAttribute(Qt.WA_Hover, False)
            self.setCursor(QCursor(Qt.ArrowCursor))

        self._apply_style()

    def setHighlightColor(self, color_str: str):
        self.highlight_color = color_str
        if self.interactive:
            self._shadow.setColor(QColor(color_str).lighter(150))
        self._apply_style()

    def setForcedHighlight(self, on: bool):
        self._forced_highlight = on
        if self.interactive:
            self._shadow.setEnabled(on or self._hovered)
        self._apply_style()

    def _apply_style(self):
        if not self.interactive:
            bg = self.base_bg
            border = self.border_color
        elif self._forced_highlight:
            border = self.highlight_color
            bg = self.hover_bg
        elif self._hovered:
            border = "#8b949e"
            bg = self.hover_bg
        else:
            border = self.border_color
            bg = self.base_bg

        self.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border-radius: {self.radius}px; border: 1px solid {border}; }}")

    def _start_scale_anim(self, scale: float):
        if not self.interactive or not self.isVisible() or self._base_geometry is None: return
        base = self._base_geometry
        if scale == 1.0:
            target = base
        else:
            dw, dh = int(base.width() * (scale - 1) / 2), int(base.height() * (scale - 1) / 2)
            target = QRect(base.x() - dw, base.y() - dh, base.width() + 2 * dw, base.height() + 2 * dh)
        self._anim.stop()
        self._anim.setStartValue(self.geometry());
        self._anim.setEndValue(target);
        self._anim.start()

    def enterEvent(self, event):
        if self.interactive:
            self._hovered = True
            if self._forced_highlight: self._shadow.setEnabled(True)
            self._apply_style()
            self._start_scale_anim(1.01)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.interactive:
            self._hovered = False
            self._shadow.setEnabled(self._forced_highlight)
            self._apply_style()
            self._start_scale_anim(1.0)
        super().leaveEvent(event)

    def showEvent(self, event):
        super().showEvent(event);
        self._base_geometry = self.geometry()


# --------------------------------------------------------
# StatCard (只有这三个小卡片保留 interactive=True)
# --------------------------------------------------------
class StatCard(HoverPanel):
    clicked = Signal()

    def __init__(self, title, value, color, parent=None):
        super().__init__(parent, "rgba(13, 17, 23, 230)", "rgba(18, 24, 35, 245)", "rgba(60, 68, 77, 210)", color, 12,
                         interactive=True)
        # 修复挤压
        self.setMinimumHeight(85)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(
            "color: #8b949e; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(
            "color: #f0f6fc; font-size: 24px; font-weight: 700; border: none; background: transparent;")

        # 优化数字字体
        vf = QFont("Segoe UI", 24)
        vf.setBold(True)
        vf.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        self.lbl_value.setFont(vf)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

    def set_selected(self, selected): self.setForcedHighlight(selected)

    def update_value(self, new_value): self.lbl_value.setText(new_value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.clicked.emit()
        super().mousePressEvent(event)


# --------------------------------------------------------
# DashboardPage
# --------------------------------------------------------
class DashboardPage(QWidget):
    navigate_to_detail = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 【关键修复】初始化 current_metric
        self.current_metric = "Screen Time"

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 30)
        self.main_layout.setSpacing(25)

        # 0. Status Bar
        status_layout = QHBoxLayout()
        self.indicator = QLabel("●")
        self.indicator.setStyleSheet("color: #238636; font-size: 14px; margin-right: -5px;")
        self.status_msg = QLabel("Live Tracking Active")
        self.status_msg.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 500;")
        self.period_msg = QLabel("|  Stats since 00:00 AM")
        self.period_msg.setStyleSheet("color: #484f58; font-size: 12px;")
        status_layout.addWidget(self.indicator)
        status_layout.addWidget(self.status_msg)
        status_layout.addWidget(self.period_msg)

        # Settings Button
        status_layout.addStretch()

        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8b949e;
                font-size: 18px;
                border: none;
                padding: 4px;
                border-radius: 4px;
            }
            QPushButton:hover {
                color: #e6edf3;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        status_layout.addWidget(self.btn_settings)

        self.main_layout.addLayout(status_layout)

        # 1. Stats Cards
        stats_row = QHBoxLayout()
        stats_row.setSpacing(18)
        self.card_clicks = StatCard("Clicks", "0", "#1f6feb")
        self.card_screen_time = StatCard("Screen Time", "0s", "#238636")
        self.card_keystrokes = StatCard("Keystrokes", "0", "#d29922")
        self.card_clicks.clicked.connect(lambda: self.switch_heatmap_mode("Clicks", "#1f6feb"))
        self.card_screen_time.clicked.connect(lambda: self.switch_heatmap_mode("Screen Time", "#238636"))
        self.card_keystrokes.clicked.connect(lambda: self.switch_heatmap_mode("Keystrokes", "#d29922"))
        stats_row.addWidget(self.card_clicks)
        stats_row.addWidget(self.card_screen_time)
        stats_row.addWidget(self.card_keystrokes)
        self.main_layout.addLayout(stats_row)

        # 2. Heatmap Container
        self.heatmap_container = HoverPanel(
            base_bg="rgba(9, 12, 20, 235)",
            highlight_color="rgba(48, 54, 61, 255)",
            radius=12,
            interactive=False
        )
        h_layout = QVBoxLayout(self.heatmap_container)
        h_layout.setContentsMargins(20, 18, 20, 20)
        header = QHBoxLayout()
        self.lbl_activity = QLabel("Activity Heatmap")
        self.lbl_activity.setStyleSheet("font-size: 16px; font-weight: 600; color: #f0f6fc; border: none;")
        self.year_combo = QComboBox()
        self.year_combo.setFixedWidth(80)
        header.addWidget(self.lbl_activity)
        header.addStretch()
        header.addWidget(self.year_combo)
        h_layout.addLayout(header)
        self.heatmap = HeatmapWidget()
        self.heatmap.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.heatmap.date_clicked.connect(self.on_heatmap_date_clicked)
        h_layout.addWidget(self.heatmap)
        self.main_layout.addWidget(self.heatmap_container)

        # 3. Bottom Row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)

        # Top Apps
        self.apps_container = HoverPanel(
            base_bg="rgba(9, 12, 20, 235)",
            highlight_color="rgba(48, 54, 61, 255)",
            radius=12,
            interactive=False
        )
        apps_v = QVBoxLayout(self.apps_container)
        apps_v.setContentsMargins(0, 0, 0, 0)
        self.apps_widget = AppsWidget()
        apps_v.addWidget(self.apps_widget)
        bottom_row.addWidget(self.apps_container, 3)

        # Achievements
        self.achieve_frame = HoverPanel(
            base_bg="rgba(9, 12, 20, 235)",
            highlight_color="rgba(48, 54, 61, 255)",
            radius=12,
            interactive=False
        )
        ach_v = QVBoxLayout(self.achieve_frame)
        ach_v.setContentsMargins(20, 18, 20, 20)
        ach_lbl = QLabel("Achievements")
        ach_lbl.setStyleSheet("color: #f0f6fc; font-weight: 600; font-size: 15px; border: none;")
        ach_v.addWidget(ach_lbl)
        ach_v.addStretch()
        lock_lbl = QLabel("🔒")
        lock_lbl.setAlignment(Qt.AlignCenter)
        lock_lbl.setStyleSheet("font-size: 32px; color: #30363d;")
        tip_lbl = QLabel("Track 4h to unlock today's badge")
        tip_lbl.setAlignment(Qt.AlignCenter)
        tip_lbl.setStyleSheet("color: #484f58; font-size: 11px;")
        ach_v.addWidget(lock_lbl)
        ach_v.addWidget(tip_lbl)
        ach_v.addStretch()

        bottom_row.addWidget(self.achieve_frame, 1)
        self.main_layout.addLayout(bottom_row)

        self.update_cards_selection("Screen Time")

    def switch_heatmap_mode(self, metric, color):
        self.current_metric = metric
        self.lbl_activity.setText(f"Activity: {metric}")

        if hasattr(self.heatmap, "set_metric"):
            self.heatmap.set_metric(metric, color)

        self.update_cards_selection(metric)

    def update_cards_selection(self, active_metric):
        self.card_clicks.set_selected(active_metric == "Clicks")
        self.card_screen_time.set_selected(active_metric == "Screen Time")
        self.card_keystrokes.set_selected(active_metric == "Keystrokes")

    def update_stats(self, time_sec, clicks, keys):
        self.card_screen_time.update_value(format_duration_precise(time_sec))
        self.card_clicks.update_value(f"{clicks:,}")
        self.card_keystrokes.update_value(f"{keys:,}")

    def update_heatmap_data(self, data, year): self.heatmap.set_data(data, year)

    def update_apps_data(self, apps_data): self.apps_widget.update_data(apps_data)

    def on_heatmap_date_clicked(self, date_str): self.navigate_to_detail.emit(date_str, self.current_metric)