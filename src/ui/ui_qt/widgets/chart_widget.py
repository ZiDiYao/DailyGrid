from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont
from PySide6.QtCore import Qt, QRectF, QPointF
import math


class ChartWidget(QWidget):
    """
    一个基于 QPainter 的折线图组件，支持时间轴和未来数据断点。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_color = QColor(0, 0, 0)
        self.unit_guess = ""  # "Time" 或 "Count"
        self._data = []  # 实际数据点 (可能包含 None)
        self._labels = []  # X 轴标签

        # 保持 DetailPage 的卡片样式
        self.setStyleSheet("background-color: #161b22; border-radius: 12px; border: none;")

        self.font = QFont("Segoe UI", 8)
        self.label_color = QColor(139, 148, 158)  # 灰色
        self.grid_color = QColor(33, 38, 45)  # 深灰色网格线
        self.dot_radius = 4

    def set_data(self, values: list, labels: list):
        """更新数据并请求重绘"""
        self._data = values
        self._labels = labels
        self.update()  # 请求 Qt 调用 paintEvent

    def _get_max_val(self):
        """获取最大值，忽略 None"""
        valid_data = [v for v in self._data if v is not None and v > 0]
        if not valid_data:
            return 0

        max_val = max(valid_data)

        # 确保 Y 轴刻度至少是 5 的倍数
        if self.unit_guess == "Count":
            # Count 向上取整到 5 的倍数
            if max_val >= 5:
                return math.ceil(max_val / 5) * 5
            return 5  # 最小显示 5
        elif self.unit_guess == "Time":
            # Time 向上取整到 1 小时或 0.5 小时
            if max_val >= 2: return math.ceil(max_val)
            if max_val > 0.5: return math.ceil(max_val * 2) / 2  # 0.5的倍数
            return 1.0  # 最小显示 1 小时

        return max_val if max_val > 0 else 1.0

    def _get_y_label(self, val):
        """根据 unit_guess 格式化 Y 轴标签"""
        if self.unit_guess == "Time":
            return f"{val:.1f}h"
        elif self.unit_guess == "Count":
            if val >= 1000:
                return f"{val / 1000:.0f}K"
            return str(int(val))
        return str(val)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.font)

        # 检查数据
        if not self._data or all(v is None or v == 0 for v in self._data):
            painter.setPen(QPen(self.label_color))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data Available.")
            return

        W, H = self.width(), self.height()
        LEFT_PAD = 40  # 留给 Y 轴标签
        RIGHT_PAD = 10
        TOP_PAD = 10
        BOTTOM_PAD = 25  # 留给 X 轴标签

        CHART_W = W - LEFT_PAD - RIGHT_PAD
        CHART_H = H - TOP_PAD - BOTTOM_PAD

        max_val = self._get_max_val()
        if max_val == 0: max_val = 1

        data_count = len(self._data)

        # 确保至少有两个点才能画线，否则画一个点
        if data_count <= 1:
            # 只有一个点，可以不画线，只画点和标签
            # 保持退出，避免后续计算出错
            painter.setPen(QPen(self.label_color));
            painter.drawText(self.rect(), Qt.AlignCenter, "Not enough data points.")
            return

        # 1. 绘制 Y 轴和网格线
        num_y_steps = 3
        step_val = max_val / num_y_steps

        painter.setPen(QPen(self.grid_color, 1))

        for i in range(num_y_steps + 1):
            y_val = i * step_val
            y_pos = H - BOTTOM_PAD - (y_val / max_val) * CHART_H

            # 绘制网格线
            if i > 0:
                painter.drawLine(LEFT_PAD, int(y_pos), W - RIGHT_PAD, int(y_pos))

            # 绘制 Y 轴标签
            painter.setPen(QPen(self.label_color))
            label = self._get_y_label(y_val)
            painter.drawText(QRectF(0, y_pos - 10, LEFT_PAD - 5, 20), Qt.AlignRight | Qt.AlignVCenter, label)

            # 还原画笔颜色
            painter.setPen(QPen(self.grid_color, 1))

        # 2. 计算数据点位置 (Points)
        points = []
        x_step = CHART_W / (data_count - 1)

        for i, value in enumerate(self._data):
            if value is None:
                points.append(None)
                continue

            # 实际值
            val = float(value)

            # 缩放 Y 值
            y_scaled = (val / max_val) * CHART_H

            # 确保点不会跑到顶部或底部边缘，留出 self.dot_radius 的空间
            if y_scaled > CHART_H - self.dot_radius:
                y_scaled = CHART_H - self.dot_radius
            if y_scaled < self.dot_radius:
                y_scaled = self.dot_radius

            y_pos = H - BOTTOM_PAD - y_scaled

            # X 位置
            x_pos = LEFT_PAD + i * x_step

            points.append(QPointF(x_pos, y_pos))

        # 3. 绘制折线和数据点
        painter.setPen(QPen(self.theme_color, 2.5))
        painter.setBrush(QBrush(self.theme_color))

        last_point = None

        for i, point in enumerate(points):
            if point is None:
                last_point = None
                continue

            # 绘制折线 (仅连接有效点)
            if last_point is not None:
                painter.drawLine(last_point, point)

            # 绘制数据点 (圆点)
            painter.setPen(QPen(self.theme_color.darker(120), 1))
            painter.drawEllipse(point, self.dot_radius, self.dot_radius)

            last_point = point

        # 4. 绘制 X 轴标签
        painter.setPen(QPen(self.label_color))

        # 定义一个标签宽度，用于居中。我们使用 x_step 作为宽度。
        label_width = x_step if data_count > 1 else CHART_W

        for i, label in enumerate(self._labels):
            x_pos = LEFT_PAD + i * x_step

            # 调整位置，使其位于数据点正下方。使用 label_width/2 来居中。
            text_rect = QRectF(x_pos - label_width / 2,
                               H - BOTTOM_PAD + 5,
                               label_width,
                               BOTTOM_PAD - 5)

            alignment = Qt.AlignCenter

            # Day chart (24h) 标签太多，只画偶数小时
            if data_count == 24 and i % 2 != 0:  # 修正：改为每隔一小时显示标签
                continue

            painter.drawText(text_rect, alignment, label)

        painter.end()