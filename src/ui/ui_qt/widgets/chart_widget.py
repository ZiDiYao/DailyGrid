from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath, QLinearGradient, QFont
from PySide6.QtCore import Qt, QPointF, QRectF


class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.data = []
        self.labels = []
        self.theme_color = QColor("#1f6feb")

    def set_data(self, values, labels, color_hex="#1f6feb"):
        self.data = values
        self.labels = labels
        self.theme_color = QColor(color_hex)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        padding_left = 40
        padding_bottom = 30
        padding_top = 30
        padding_right = 30

        plot_w = w - padding_left - padding_right
        plot_h = h - padding_bottom - padding_top

        # --- 1. 数据预处理 ---
        # 过滤掉 None，只用有效数字计算最大值
        valid_data = [v for v in self.data if v is not None]
        if not valid_data:
            real_max = 0
        else:
            real_max = max(valid_data)

        # 【优化】如果最大值是0，强制设为10，防止线条顶天立地
        # 稍微增加一点上限，让波峰不要顶到最上面
        max_val = real_max * 1.2 if real_max > 0 else 10

        # 计算步长
        count = len(self.data)
        x_step = plot_w / (count - 1) if count > 1 else plot_w
        y_ratio = plot_h / max_val

        # --- 2. 生成有效点的坐标 ---
        # points 列表可能包含 None (代表断点)
        points = []
        for i, val in enumerate(self.data):
            x = padding_left + i * x_step
            if val is not None:
                y = (h - padding_bottom) - (val * y_ratio)
                points.append(QPointF(x, y))
            else:
                points.append(None)

        # --- 3. 绘制路径 (处理断线) ---
        # 我们需要一段一段地画，遇到 None 就截断
        path = QPainterPath()
        fill_path = QPainterPath()  # 用于渐变填充

        has_started = False
        last_valid_point = None
        first_valid_point_in_segment = None

        for p in points:
            if p is None:
                # 遇到断点：如果有正在画的路径，需要闭合它以进行填充
                if has_started and last_valid_point:
                    # 闭合填充路径：垂直向下到底部，再回到段落起点底部
                    fill_path.lineTo(last_valid_point.x(), h - padding_bottom)
                    fill_path.lineTo(first_valid_point_in_segment.x(), h - padding_bottom)
                    fill_path.closeSubpath()
                    has_started = False
                continue

            # 如果是有效点
            if not has_started:
                path.moveTo(p)
                fill_path.moveTo(p)
                first_valid_point_in_segment = p
                has_started = True
            else:
                # 使用简单的直线连接，或者贝塞尔曲线
                # 这里为了断点处理简单，先用直线，贝塞尔需要更多控制点判断
                # 如果想用贝塞尔，可以在这里计算控制点
                c1 = QPointF((last_valid_point.x() + p.x()) / 2, last_valid_point.y())
                c2 = QPointF((last_valid_point.x() + p.x()) / 2, p.y())
                path.cubicTo(c1, c2, p)
                fill_path.cubicTo(c1, c2, p)

            last_valid_point = p

        # 处理最后一段的闭合
        if has_started and last_valid_point:
            fill_path.lineTo(last_valid_point.x(), h - padding_bottom)
            fill_path.lineTo(first_valid_point_in_segment.x(), h - padding_bottom)
            fill_path.closeSubpath()

        # --- 4. 上色 ---
        # 渐变
        gradient = QLinearGradient(0, padding_top, 0, h - padding_bottom)
        c_top = QColor(self.theme_color)
        c_top.setAlpha(100)
        c_bottom = QColor(self.theme_color)
        c_bottom.setAlpha(0)
        gradient.setColorAt(0, c_top)
        gradient.setColorAt(1, c_bottom)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawPath(fill_path)

        # 线条
        pen = QPen(self.theme_color, 3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # --- 5. 绘制坐标轴和标签 ---
        painter.setPen(QPen(QColor("#30363d"), 1))
        # X轴
        painter.drawLine(padding_left, h - padding_bottom, w - padding_right, h - padding_bottom)

        # 绘制文字
        painter.setPen(QColor("#8b949e"))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)

        # Y轴最大值
        painter.drawText(QRectF(0, padding_top - 10, padding_left - 8, 20),
                         Qt.AlignRight | Qt.AlignVCenter, str(int(max_val)))
        # Y轴 0
        painter.drawText(QRectF(0, h - padding_bottom - 10, padding_left - 8, 20),
                         Qt.AlignRight | Qt.AlignVCenter, "0")

        # X轴标签 (居中对齐)
        # 策略：无论多少数据，我们均匀取点显示，防止重叠
        if not self.labels: return

        label_count = len(self.labels)
        # 我们希望标签之间至少隔 40px
        max_labels = int(plot_w / 40)
        step = max(1, label_count // max_labels)

        for i in range(0, label_count, step):
            # 计算这个标签对应的 X 坐标
            cx = padding_left + i * x_step

            text = str(self.labels[i])
            # 定义一个以 cx 为中心的矩形
            rect = QRectF(cx - 25, h - padding_bottom + 5, 50, 20)
            painter.drawText(rect, Qt.AlignCenter, text)