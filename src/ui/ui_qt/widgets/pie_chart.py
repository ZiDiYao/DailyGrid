import math
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSpacerItem, QSizePolicy
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont
from PySide6.QtCore import Qt, QRectF, QPointF, Signal  # 引入 Signal


class PieChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 让鼠标事件穿透饼图传给父容器
        self.data = []
        self.total = 0

    def set_data(self, data):
        self.data = data
        self.total = sum(d[1] for d in data)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        side = min(w, h)
        x_offset = (w - side) / 2
        y_offset = (h - side) / 2

        rect = QRectF(x_offset + 10, y_offset + 10, side - 20, side - 20)
        center_point = rect.center()

        outer_radius = rect.width() / 2
        hole_ratio = 0.6
        inner_radius = outer_radius * hole_ratio
        text_radius = (outer_radius + inner_radius) / 2

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#21262d")))
        painter.drawEllipse(rect)

        if self.total > 0:
            current_angle_qt = 90 * 16
            font = QFont("Segoe UI", 9, QFont.Bold)
            painter.setFont(font)

            for name, value, color in self.data:
                pct = value / self.total
                span_angle_qt = -int(pct * 360 * 16)

                painter.setBrush(QBrush(QColor(color)))
                painter.setPen(Qt.NoPen)
                painter.drawPie(rect, current_angle_qt, span_angle_qt)

                if pct > 0.04:
                    mid_angle_qt = current_angle_qt + (span_angle_qt / 2)
                    mid_angle_deg = mid_angle_qt / 16
                    rad = math.radians(mid_angle_deg)

                    tx = center_point.x() + text_radius * math.cos(rad)
                    ty = center_point.y() - text_radius * math.sin(rad)

                    pct_text = f"{int(pct * 100)}%"
                    painter.setPen(QColor("white"))
                    text_rect = QRectF(tx - 20, ty - 10, 40, 20)
                    painter.drawText(text_rect, Qt.AlignCenter, pct_text)

                current_angle_qt += span_angle_qt

        center_rect = rect.adjusted(
            rect.width() * (1 - hole_ratio) / 2,
            rect.height() * (1 - hole_ratio) / 2,
            -rect.width() * (1 - hole_ratio) / 2,
            -rect.height() * (1 - hole_ratio) / 2
        )
        painter.setBrush(QBrush(QColor("#161b22")))
        painter.drawEllipse(center_rect)


class TopAppsWidget(QFrame):
    # 【新增】点击信号
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        # 【新增】鼠标变成小手
        self.setCursor(Qt.PointingHandCursor)

        self.app_colors = ['#1f6feb', '#238636', '#d29922', '#8957e5', '#da3633']

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        self.list_container = QWidget()
        self.list_container.setAttribute(Qt.WA_TransparentForMouseEvents)  # 让点击穿透
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()

        self.layout.addWidget(self.list_container, stretch=3)

        self.pie_chart = PieChartWidget()
        self.layout.addWidget(self.pie_chart, stretch=2)

    def update_data(self, top_apps_list):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        chart_data = []
        limit = min(len(top_apps_list), 5)

        self.list_layout.addStretch()

        if not top_apps_list:
            lbl = QLabel("No data yet")
            lbl.setStyleSheet("color: #8b949e; font-style: italic;")
            self.list_layout.addWidget(lbl)

        for i in range(limit):
            app_name, duration_seconds = top_apps_list[i]
            minutes = int(duration_seconds // 60)
            color = self.app_colors[i % len(self.app_colors)]

            chart_data.append((app_name, minutes, color))

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(5, 5, 10, 5)
            row_layout.setSpacing(10)

            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")

            display_name = app_name.replace(".exe", "").capitalize()
            lbl_name = QLabel(display_name)
            lbl_name.setStyleSheet("color: #c9d1d9; font-size: 14px; font-weight: 500;")

            h = int(minutes // 60)
            m = int(minutes % 60)
            time_str = f"{h}h {m}m" if h > 0 else f"{m}m"
            lbl_time = QLabel(time_str)
            lbl_time.setStyleSheet("color: #8b949e; font-size: 13px;")

            row_layout.addWidget(dot)
            row_layout.addWidget(lbl_name)
            row_layout.addStretch()
            row_layout.addWidget(lbl_time)

            row_widget.setStyleSheet("QWidget { background-color: #0d1117; border-radius: 6px; }")
            self.list_layout.addWidget(row_widget)

        self.list_layout.addStretch()
        self.pie_chart.set_data(chart_data)

    # 【新增】鼠标点击事件
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    # 【新增】鼠标悬停效果
    def enterEvent(self, event):
        self.setStyleSheet("""
            QFrame#Card {
                background-color: #1c2128; 
                border: 1px solid #8b949e;
                border-radius: 10px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("")  # 恢复默认样式(由外部QSS控制)
        super().leaveEvent(event)