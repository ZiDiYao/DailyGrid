from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont
from PySide6.QtCore import Qt, QRectF, QPointF

# 颜色配置 (Dracule 风格，与 AppsWidget 保持一致)
APP_COLORS = [
    QColor("#61dafb"), QColor("#50fa7b"), QColor("#ff79c6"), QColor("#f1fa8c"),
    QColor("#bd93f9"), QColor("#ffb86c"), QColor("#8be9fd"), QColor("#ff6e67"),
    QColor("#bfd7ea"), QColor("#c9e4de")
]
TITLE_COLOR = QColor("#c9d1d9")
LABEL_COLOR = QColor("#8b949e")
TOP_PAD = 20  # 图例顶部填充


class PieChartWidget(QWidget):
    """
    自定义饼图组件 (Pie Chart)
    - 左侧显示饼图
    - 右侧显示图例 (Legend)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 250)
        self.data = []  # 格式: [(label, value), ...]
        self.total = 0.0
        self.setStyleSheet("background: transparent;")
        self.font = QFont("Segoe UI", 9)

    def set_data(self, data: list):
        """
        设置数据并重绘
        :param data: list of tuples [(app_name, seconds), ...]
        """
        # 过滤掉时长为 0 的应用
        self.data = [item for item in data if item[1] > 0]
        self.total = sum(item[1] for item in self.data)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.font)

        W, H = self.width(), self.height()

        # 布局计算：饼图位于左侧，图例位于右侧
        CHART_SIDE = min(H, W * 0.5)  # 饼图占据高度，或宽度的一半 (取较小值)

        rect_size = CHART_SIDE * 0.8  # 饼图实际大小
        center = QPointF(CHART_SIDE / 2, H / 2)

        # 定义饼图绘制区域
        rect = QRectF(center.x() - rect_size / 2, center.y() - rect_size / 2, rect_size, rect_size)

        # --- 如果无数据 ---
        if not self.data or self.total == 0:
            painter.setPen(QPen(LABEL_COLOR))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Usage Data Today.")
            painter.end()
            return

        start_angle = 90 * 16  # 12点钟方向开始 (Qt 角度单位是 1/16 度)

        # --- 1. 绘制饼图扇区 ---
        for i, (label, value) in enumerate(self.data):
            percentage = value / self.total
            span_angle = round(percentage * 360 * 16)

            color = APP_COLORS[i % len(APP_COLORS)]
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(22, 27, 34), 2))  # 深色分割线

            painter.drawPie(rect, start_angle, span_angle)
            start_angle += span_angle

        # --- 2. 绘制图例 (Legend) ---
        legend_start_x = CHART_SIDE + 20
        max_legend_y = H - 10

        for i, (label, value) in enumerate(self.data):
            percentage = value / self.total
            color = APP_COLORS[i % len(APP_COLORS)]

            legend_y = TOP_PAD + i * 25

            # 检查是否超出底部边界
            if legend_y + 20 > max_legend_y:
                break

            # 绘制颜色方块
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRect(int(legend_start_x), int(legend_y), 10, 10)

            # 绘制文字标签
            painter.setPen(QPen(TITLE_COLOR))

            # 将秒数转换为小时/分钟
            minutes = int(value) // 60
            hours = minutes // 60
            minutes %= 60

            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            display_label = f"{label.replace('.exe', '')} ({percentage:.1%}) - {time_str}"

            painter.drawText(int(legend_start_x) + 15, int(legend_y) + 10, display_label)

        painter.end()