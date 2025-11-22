import math
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont
from PySide6.QtCore import Qt, QRectF, Signal


# ========== 可留作以后详细页用的 PieChartWidget（首页不用） ==========
class PieChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self.data = []
        self.total = 0

    def set_data(self, data):
        """data: [(name, value, color_hex), ...]"""
        self.data = data
        self.total = sum(d[1] for d in data)
        self.update()

    def paintEvent(self, event):
        if self.total <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        side = min(w, h)
        x_offset = (w - side) / 2
        y_offset = (h - side) / 2

        rect = QRectF(x_offset + 10, y_offset + 10, side - 20, side - 20)
        center = rect.center()

        outer_r = rect.width() / 2
        hole_ratio = 0.6
        inner_r = outer_r * hole_ratio
        text_r = (outer_r + inner_r) / 2

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#21262d")))
        painter.drawEllipse(rect)

        current_angle_qt = 90 * 16
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))

        for name, value, color in self.data:
            pct = value / self.total
            span_angle_qt = -int(pct * 360 * 16)

            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.NoPen)
            painter.drawPie(rect, current_angle_qt, span_angle_qt)

            if pct > 0.04:
                mid_angle_qt = current_angle_qt + span_angle_qt / 2
                mid_deg = mid_angle_qt / 16
                rad = math.radians(mid_deg)

                tx = center.x() + text_r * math.cos(rad)
                ty = center.y() - text_r * math.sin(rad)

                pct_text = f"{int(pct * 100)}%"
                painter.setPen(QColor("white"))
                text_rect = QRectF(tx - 18, ty - 9, 36, 18)
                painter.drawText(text_rect, Qt.AlignCenter, pct_text)

            current_angle_qt += span_angle_qt

        # 中间挖空
        inner_rect = rect.adjusted(
            rect.width() * (1 - hole_ratio) / 2,
            rect.height() * (1 - hole_ratio) / 2,
            -rect.width() * (1 - hole_ratio) / 2,
            -rect.height() * (1 - hole_ratio) / 2
        )
        painter.setBrush(QBrush(QColor("#161b22")))
        painter.drawEllipse(inner_rect)


# ========== 首页用：只有列表 + 使用时间，没有饼图 ==========
class TopAppsWidget(QFrame):
    """
    首页「Top Apps Today」内容区：
    - 不再包含 PieChart，只绘制一列 App 行
    - 整个大卡片外观由外部 QFrame / QSS 控制，这里不再额外套 Card
    """
    clicked = Signal()   # 整块点击（给你跳到详细页用）

    def __init__(self, parent=None):
        super().__init__(parent)
        # 不再设置 objectName = "Card"，避免生成第二层小卡片
        self.setCursor(Qt.PointingHandCursor)

        self.app_colors = ['#1f6feb', '#238636', '#d29922', '#8957e5', '#da3633']

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0)
        main_layout.setSpacing(8)

        # 只要一个纵向 layout 放每一行
        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        main_layout.addLayout(self.list_layout)
        main_layout.addStretch()

    # ------- 对外接口：刷新数据 -------
    def update_data(self, top_apps_list):
        """
        top_apps_list: [(process_name, seconds), ...]
        """
        # 清空旧行
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not top_apps_list:
            lbl = QLabel("No data yet")
            lbl.setStyleSheet("color: #8b949e; font-style: italic;")
            self.list_layout.addWidget(lbl)
            return

        limit = min(5, len(top_apps_list))
        max_seconds = max(seconds for _, seconds in top_apps_list[:limit]) or 1

        for i in range(limit):
            app_name, seconds = top_apps_list[i]
            color = self.app_colors[i % len(self.app_colors)]
            self._add_app_row(app_name, seconds, max_seconds, color)

    # ------- 内部：创建单行 -------
    def _add_app_row(self, app_name, seconds, max_seconds, color_hex):
        row = QWidget()
        row.setFixedHeight(30)

        lo = QHBoxLayout(row)
        lo.setContentsMargins(5, 0, 5, 0)
        lo.setSpacing(10)

        # 左侧：名字 + 进度条
        left = QWidget()
        left_lo = QVBoxLayout(left)
        left_lo.setContentsMargins(0, 0, 0, 0)
        left_lo.setSpacing(3)

        display_name = app_name.replace(".exe", "")
        name_label = QLabel(display_name)
        name_label.setStyleSheet("color: #c9d1d9; font-size: 13px;")

        # 简易条形进度条（不画边框）
        bar_bg = QFrame()
        bar_bg.setFixedHeight(4)
        bar_bg.setStyleSheet("background-color: #161b22; border-radius: 2px;")

        bar_fill = QFrame(bar_bg)
        ratio = max(0.08, min(1.0, seconds / max_seconds))
        bar_fill.setStyleSheet(f"background-color: {color_hex}; border-radius: 2px;")
        bar_fill.resize(int(ratio * bar_bg.width()), bar_bg.height())

        # 让 bar_fill 在 resize 时跟着父控件宽度变化
        def resize_bar():
            bar_fill.resize(int(ratio * bar_bg.width()), bar_bg.height())

        bar_bg.resizeEvent = lambda e: (QFrame.resizeEvent(bar_bg, e), resize_bar())

        left_lo.addWidget(name_label)
        left_lo.addWidget(bar_bg)

        # 右侧：时间文本
        minutes = int(seconds // 60)
        time_text = f"{minutes}m"
        time_label = QLabel(time_text)
        time_label.setStyleSheet("color: #8b949e; font-size: 13px;")

        lo.addWidget(left)
        lo.addStretch()
        lo.addWidget(time_label)

        # 行 hover 轻微高亮（不再画小卡片边框）
        row.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: rgba(255, 255, 255, 0.04);
            }
        """)

        self.list_layout.addWidget(row)

    # ------- 整块点击 / hover 外观（给大卡片用） -------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        # 外观交给外层 Wallpaper 卡片控制，这里只给一点点反馈也行
        super().enterEvent(event)

    def leaveEvent(self, event):
        super().leaveEvent(event)
