from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPainterPath, QLinearGradient
from PySide6.QtCore import Qt, QRectF, QPointF


class ModernChartWidget(QWidget):
    def __init__(self, chart_type="area", color="#1f6feb", parent=None):
        super().__init__(parent)
        self.chart_type = chart_type
        self.theme_color = QColor(color)
        self.data_points = []
        self.x_labels = []
        self.highlight_index = -1

        self.setMinimumHeight(200)

        # 【关键修改】强制透明，不填充背景，防止出现“黑框”
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; border: none;")

    def set_data(self, values: list, labels: list, highlight_idx=-1):
        self.data_points = [float(v) if v is not None else 0.0 for v in values]
        self.x_labels = labels
        self.highlight_index = highlight_idx
        self.update()

    def set_color(self, color_hex):
        self.theme_color = QColor(color_hex)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 确保不画背景，直接在透明画布上画线

        w, h = self.width(), self.height()
        padding_top = 30
        padding_bottom = 30
        padding_left = 10
        padding_right = 10

        chart_rect = QRectF(padding_left, padding_top, w - padding_left - padding_right,
                            h - padding_top - padding_bottom)

        # 1. 绘制网格线 (虚线，极淡)
        self.draw_grid(painter, chart_rect)

        if not self.data_points: return

        max_val = max(self.data_points) if max(self.data_points) > 0 else 1
        count = len(self.data_points)
        step_x = chart_rect.width() / max(1, count)

        # 2. 绘制图表
        if self.chart_type == "bar":
            self.draw_bars(painter, chart_rect, max_val, step_x)
        else:
            self.draw_area(painter, chart_rect, max_val, step_x)

        # 3. 绘制 X 轴标签
        self.draw_labels(painter, chart_rect, step_x)

    def draw_grid(self, painter, rect):
        # 颜色调得非常淡，融入背景
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1, Qt.DotLine))
        steps = 4
        for i in range(steps + 1):
            y = rect.bottom() - (rect.height() / steps) * i
            painter.drawLine(rect.left(), y, rect.right(), y)

    def draw_bars(self, painter, rect, max_val, step_x):
        bar_width_ratio = 0.5
        bar_w = step_x * bar_width_ratio
        offset = (step_x - bar_w) / 2

        for i, val in enumerate(self.data_points):
            if val == 0: continue
            bar_h = (val / max_val) * rect.height()
            x = rect.left() + i * step_x + offset
            y = rect.bottom() - bar_h

            bar_rect = QRectF(x, y, bar_w, bar_h)

            if i == self.highlight_index:
                painter.setBrush(QBrush(self.theme_color.lighter(130)))
            else:
                c = QColor(self.theme_color)
                c.setAlpha(180)
                painter.setBrush(QBrush(c))

            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bar_rect, 3, 3)

    def draw_area(self, painter, rect, max_val, step_x):
        path = QPainterPath()
        fill_path = QPainterPath()
        start_x = rect.left() + step_x * 0.5
        path.moveTo(start_x, rect.bottom())
        fill_path.moveTo(start_x, rect.bottom())

        points = []
        for i, val in enumerate(self.data_points):
            x = rect.left() + step_x * (i + 0.5)
            y = rect.bottom() - (val / max_val) * rect.height()
            points.append(QPointF(x, y))

        if points:
            path.moveTo(points[0])
            fill_path.moveTo(points[0])
            for p in points[1:]:
                path.lineTo(p)
                fill_path.lineTo(p)
            fill_path.lineTo(points[-1].x(), rect.bottom())
            fill_path.lineTo(points[0].x(), rect.bottom())

        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        c_start = QColor(self.theme_color)
        c_start.setAlpha(80)
        c_end = QColor(self.theme_color)
        c_end.setAlpha(0)
        gradient.setColorAt(0, c_start)
        gradient.setColorAt(1, c_end)

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawPath(fill_path)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(self.theme_color, 2))
        painter.drawPath(path)

        painter.setBrush(QBrush(self.theme_color))
        for i, p in enumerate(points):
            if self.highlight_index != -1:
                if i == self.highlight_index:
                    painter.setBrush(QBrush(QColor("#ffffff")))
                    painter.drawEllipse(p, 4, 4)
                    painter.setBrush(QBrush(self.theme_color))
                else:
                    painter.drawEllipse(p, 2, 2)
            else:
                painter.drawEllipse(p, 2, 2)

    def draw_labels(self, painter, rect, step_x):
        painter.setPen(QColor("#7d8590"))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)

        skip = 1
        if len(self.x_labels) > 12: skip = 2
        if len(self.x_labels) > 20: skip = 4

        for i, label in enumerate(self.x_labels):
            if i % skip != 0: continue
            x = rect.left() + step_x * (i + 0.5)
            text_rect = QRectF(x - 20, rect.bottom() + 5, 40, 20)
            painter.drawText(text_rect, Qt.AlignCenter, str(label))