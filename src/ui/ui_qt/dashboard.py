from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QCursor, QColor

from .widgets.heatmap_widget import HeatmapWidget
from .widgets.apps_widget import AppsWidget


# --------------------------------------------------------
# 通用 Hover Panel（玻璃卡片 + 缩放 + 阴影 + 高亮边框）
# --------------------------------------------------------
class HoverPanel(QFrame):
    """
    一个可复用的“玻璃卡片”基类：
    """

    def __init__(
            self,
            parent=None,
            base_bg="rgba(10, 14, 23, 220)",
            hover_bg="rgba(18, 24, 35, 235)",
            border_color="rgba(48, 54, 61, 200)",
            highlight_color="#1f6feb",
            radius=10,
    ):
        super().__init__(parent)

        self.base_bg = base_bg
        self.hover_bg = hover_bg
        self.border_color = border_color
        self.highlight_color = highlight_color
        self.radius = radius

        self._hovered = False
        self._forced_highlight = False
        self._base_geometry: QRect | None = None

        # 打开 hover 事件
        self.setAttribute(Qt.WA_Hover, True)
        self.setCursor(Qt.ArrowCursor)

        # 阴影效果 (macOS 风)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(24)
        self._shadow.setOffset(0, 8)
        self._shadow.setColor(QColor(self.highlight_color).lighter(150))
        self._shadow.setEnabled(False)
        self.setGraphicsEffect(self._shadow)

        # 几何动画，用来模拟 1.02 缩放
        self._anim = QPropertyAnimation(self, b"geometry", self)
        self._anim.setDuration(130)
        self._anim.setEasingCurve(QEasingCurve.OutQuad)

        self._apply_style()

    # -------- 外部 API --------
    def setHighlightColor(self, color_str: str):
        self.highlight_color = color_str
        self._shadow.setColor(QColor(color_str).lighter(150))
        self._apply_style()

    def setForcedHighlight(self, on: bool):
        """用于“当前选中”的效果，如当前 StatCard / 当前 Heatmap 类型"""
        self._forced_highlight = on
        # 选中时给一个轻微的常驻阴影
        self._shadow.setEnabled(on or self._hovered)
        self._apply_style()

    # -------- 内部样式 & 动画 --------
    def _apply_style(self):
        if self._hovered or self._forced_highlight:
            border = self.highlight_color
            bg = self.hover_bg
        else:
            border = self.border_color
            bg = self.base_bg

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg};
                border-radius: {self.radius}px;
                border: 1px solid {border};
            }}
            """
        )

    def _start_scale_anim(self, scale: float):
        """用几何动画模拟轻微缩放"""
        if not self.isVisible():
            return

        if self._base_geometry is None:
            self._base_geometry = self.geometry()

        base = self._base_geometry

        if scale == 1.0:
            target = base
        else:
            w, h = base.width(), base.height()
            dw = int(w * (scale - 1.0) / 2)
            dh = int(h * (scale - 1.0) / 2)
            target = QRect(base.x() - dw, base.y() - dh, w + 2 * dw, h + 2 * dh)

        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(target)
        self._anim.start()

    # -------- Qt 事件重载 --------
    def enterEvent(self, event):
        self._hovered = True
        self._shadow.setEnabled(True)
        self._apply_style()
        self._start_scale_anim(1.02)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        # 如果没有被“选中”，移除阴影
        self._shadow.setEnabled(self._forced_highlight)
        self._apply_style()
        self._start_scale_anim(1.0)
        super().leaveEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        # 初次显示时记录基准几何
        self._base_geometry = self.geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 非 hover 状态下更新基准几何，避免拖动窗口后缩放错位
        if not self._hovered and not self._anim.state() == QPropertyAnimation.Running:
            self._base_geometry = self.geometry()


# --------------------------------------------------------
# 顶部统计卡片（继承 HoverPanel）
# --------------------------------------------------------
class StatCard(HoverPanel):
    clicked = Signal()

    def __init__(self, title: str, value: str, color: str, parent=None):
        super().__init__(
            parent=parent,
            base_bg="rgba(13, 17, 23, 230)",
            hover_bg="rgba(18, 24, 35, 245)",
            border_color="rgba(60, 68, 77, 210)",
            highlight_color=color,
            radius=12,
        )

        self.setObjectName("StatCard")
        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.theme_color = color
        self.is_selected = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(
            "color: #8b949e; font-size: 13px; font-weight: 600; border: none; background: transparent;"
        )

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(
            "color: #f0f6fc; font-size: 24px; font-weight: 700; border: none; background: transparent;"
        )

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

        self._apply_style()

    def set_selected(self, selected: bool):
        self.is_selected = selected
        # 选中的卡片保持轻微高亮和阴影
        self.setForcedHighlight(selected)

    def update_value(self, new_value: str):
        self.lbl_value.setText(new_value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# --------------------------------------------------------
# Dashboard 主页面
# --------------------------------------------------------
class DashboardPage(QWidget):
    navigate_to_detail = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_metric = "Screen Time"

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(30)

        # ========== 1. 顶部统计卡片区 ==========
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(18)

        self.card_clicks = StatCard("Clicks", "0", "#1f6feb")
        self.card_screen_time = StatCard("Screen Time", "0h 0m", "#238636")
        self.card_keystrokes = StatCard("Keystrokes", "0", "#d29922")

        # 点击切换 Heatmap 模式
        self.card_clicks.clicked.connect(
            lambda: self.switch_heatmap_mode("Clicks", "#1f6feb")
        )
        self.card_screen_time.clicked.connect(
            lambda: self.switch_heatmap_mode("Screen Time", "#238636")
        )
        self.card_keystrokes.clicked.connect(
            lambda: self.switch_heatmap_mode("Keystrokes", "#d29922")
        )

        stats_layout.addWidget(self.card_clicks)
        stats_layout.addWidget(self.card_screen_time)
        stats_layout.addWidget(self.card_keystrokes)

        self.main_layout.addLayout(stats_layout)

        # ========== 2. Heatmap 区（Wallpaper Engine 风玻璃面板） ==========
        self.heatmap_container = HoverPanel(
            base_bg="rgba(9, 12, 20, 235)",
            hover_bg="rgba(15, 19, 28, 245)",
            border_color="rgba(48, 54, 61, 180)",
            highlight_color="#238636", # 默认 Screen Time 绿色
            radius=12,
        )
        self.heatmap_container.setObjectName("HeatmapContainer")

        heatmap_layout = QVBoxLayout(self.heatmap_container)
        heatmap_layout.setContentsMargins(20, 18, 20, 20)
        heatmap_layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.lbl_activity = QLabel("Activity: Screen Time")
        self.lbl_activity.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #f0f6fc; border: none; background: transparent;"
        )

        self.year_combo = QComboBox()
        self.year_combo.setFixedWidth(80)
        self.year_combo.setStyleSheet(
            """
            QComboBox {
                background: rgba(1, 4, 9, 220);
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 5px;
                padding: 2px 10px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #0d1117;
                selection-background-color: #1f6feb;
                border-radius: 4px;
            }
            """
        )

        header_layout.addWidget(self.lbl_activity)
        header_layout.addStretch()
        header_layout.addWidget(self.year_combo)

        heatmap_layout.addLayout(header_layout)

        self.heatmap = HeatmapWidget()
        self.heatmap.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.heatmap.date_clicked.connect(self.on_heatmap_date_clicked)

        heatmap_layout.addWidget(self.heatmap)
        self.main_layout.addWidget(self.heatmap_container)

        # ========== 3. 底部：Top Apps Today + Achievements ==========
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)

        # --- Top Apps Today 外层玻璃卡片 ---
        self.apps_container = HoverPanel(
            base_bg="rgba(9, 12, 20, 235)",
            hover_bg="rgba(15, 19, 28, 245)",
            border_color="rgba(48, 54, 61, 180)",
            # ❗ 修正：初始时，Apps 容器也使用 Screen Time 的颜色 (绿色)，以保持同步 ❗
            highlight_color="#238636",
            radius=12,
        )
        self.apps_container.setObjectName("AppsContainer")

        apps_container_layout = QVBoxLayout(self.apps_container)
        apps_container_layout.setContentsMargins(0, 0, 0, 0)
        apps_container_layout.setSpacing(0)

        self.apps_widget = AppsWidget()
        self.apps_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        apps_container_layout.addWidget(self.apps_widget)

        # AppsContainer 占据 3 份比例 (约 75%)
        bottom_layout.addWidget(self.apps_container, 3)

        # --- Achievements 外层玻璃卡片 ---
        self.achieve_frame = HoverPanel(
            base_bg="rgba(9, 12, 20, 235)",
            hover_bg="rgba(15, 19, 28, 245)",
            border_color="rgba(48, 54, 61, 180)",
            highlight_color="#f78166", # 保持 Achievements 的红色
            radius=12,
        )
        self.achieve_frame.setObjectName("AchievementPanel")

        achieve_layout = QVBoxLayout(self.achieve_frame)
        achieve_layout.setContentsMargins(20, 18, 20, 20)
        achieve_layout.setSpacing(10)

        achieve_lbl = QLabel("Achievements")
        achieve_lbl.setStyleSheet(
            "color: #f0f6fc; font-weight: 600; font-size: 15px; border: none; background: transparent;"
        )
        achieve_layout.addWidget(achieve_lbl)

        achieve_layout.addStretch()

        bottom_layout.addWidget(self.achieve_frame, 1)  # Achievements 区域占据 1 份

        self.main_layout.addLayout(bottom_layout)

        # 默认选中 Screen Time
        self.update_cards_selection("Screen Time")

    # ----------------------------------------------------
    # 模式切换 / 选中状态
    # ----------------------------------------------------
    def switch_heatmap_mode(self, metric_name: str, color: str):
        """切换 Heatmap 显示的指标 & 高亮颜色"""
        self.current_metric = metric_name
        self.lbl_activity.setText(f"Activity: {metric_name}")

        # Heatmap 内部模式
        if hasattr(self.heatmap, "set_metric"):
            self.heatmap.set_metric(metric_name, color)

        # 更新 Heatmap 外框高亮颜色
        self.heatmap_container.setHighlightColor(color)

        # ❗ 修正：同时更新 Apps 容器的高亮颜色，实现颜色同步 ❗
        self.apps_container.setHighlightColor(color)

        # 更新顶部卡片选中态
        self.update_cards_selection(metric_name)

    def update_cards_selection(self, active_metric: str):
        self.card_clicks.set_selected(active_metric == "Clicks")
        self.card_screen_time.set_selected(active_metric == "Screen Time")
        self.card_keystrokes.set_selected(active_metric == "Keystrokes")

    # ----------------------------------------------------
    # 供外部调用的数据更新接口
    # ----------------------------------------------------
    def update_stats(self, time_sec: float, clicks: int, keys: int):
        m, s = divmod(int(time_sec), 60)
        h, m = divmod(m, 60)
        time_str = f"{h}h {m}m"

        self.card_screen_time.update_value(time_str)
        self.card_clicks.update_value(str(clicks))
        self.card_keystrokes.update_value(str(keys))

    def update_heatmap_data(self, data_rows, year: int):
        self.heatmap.set_data(data_rows, year)

    def update_apps_data(self, apps_data):
        self.apps_widget.update_data(apps_data)

    # ----------------------------------------------------
    # 事件：从 Heatmap 点击某一天，跳转到详细页面
    # ----------------------------------------------------
    def on_heatmap_date_clicked(self, date_str: str):
        self.navigate_to_detail.emit(date_str, self.current_metric)