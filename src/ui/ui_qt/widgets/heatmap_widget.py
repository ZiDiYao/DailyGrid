from PySide6.QtWidgets import QWidget, QToolTip
from PySide6.QtCore import Qt, Signal, QRectF, QEvent, QPoint
from PySide6.QtGui import QPainter, QColor, QCursor, QFont, QBrush
import datetime


class HeatmapWidget(QWidget):
    date_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 增加最小高度，以容纳更大的格子 (7行 * (14+3) + 上下边距)
        self.setMinimumHeight(200)
        self.setMouseTracking(True)

        self.raw_data = {}
        self.current_year = datetime.date.today().year
        self.rects = []
        self.hovered_date = None

        self.active_metric = "Screen Time"
        self.base_color = QColor("#238636")

        # --- 核心尺寸调整 ---
        self.BOX_SIZE = 14  # 增大格子 (原 11)
        self.SPACING = 3  # 保持紧凑间距
        self.LABEL_WIDTH = 28  # 稍微加宽左侧标签预留区
        self.LABEL_GAP = 8  # 文字和格子的距离

        self.thresholds = {
            "Screen Time": 8 * 3600,
            "Clicks": 5000,
            "Keystrokes": 10000
        }

    def set_data(self, data_rows, year):
        self.current_year = year
        self.raw_data = {}
        if data_rows:
            for row in data_rows:
                self.raw_data[row[0]] = (row[1] or 0, row[2] or 0, row[3] or 0)
        self.update()

    def set_metric(self, metric_name, color_hex):
        self.active_metric = metric_name
        self.base_color = QColor(color_hex)
        self.update()

    def get_value_for_date(self, date_str):
        if date_str not in self.raw_data: return 0
        t, c, k = self.raw_data[date_str]
        if self.active_metric == "Screen Time": return t
        if self.active_metric == "Clicks": return c
        if self.active_metric == "Keystrokes": return k
        return 0

    def get_color(self, value):
        if value <= 0:
            return QColor("#161b22")

        max_val = self.thresholds.get(self.active_metric, 100)
        ratio = min(value / max_val, 1.0)
        c = QColor(self.base_color)

        # GitHub 风格透明度分级
        if ratio < 0.25:
            alpha = 80
        elif ratio < 0.50:
            alpha = 120
        elif ratio < 0.75:
            alpha = 180
        else:
            alpha = 255

        c.setAlpha(alpha)
        return c

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        weeks = 53
        grid_width = weeks * (self.BOX_SIZE + self.SPACING)
        total_content_width = self.LABEL_WIDTH + self.LABEL_GAP + grid_width

        # 居中计算
        available_w = self.width()
        if available_w > total_content_width:
            start_x = (available_w - total_content_width) // 2
        else:
            start_x = 20

        start_y = 40  # 稍微增加顶部留白，给月份标签更多空间

        font = QFont("Segoe UI", 9)  # 保持字体清晰
        painter.setFont(font)

        # --- A. 绘制左侧星期标签 ---
        painter.setPen(QColor("#8b949e"))
        label_x = start_x + self.LABEL_WIDTH  # 右对齐基准线

        days = {1: "Mon", 3: "Wed", 5: "Fri"}
        for r, text in days.items():
            # 计算文字垂直居中：格子的顶部Y + 格子高度 - 基线调整
            y_pos = start_y + r * (self.BOX_SIZE + self.SPACING) + self.BOX_SIZE - 2

            # 使用 align right 绘制
            painter.drawText(label_x - painter.fontMetrics().horizontalAdvance(text), y_pos, text)

        # --- B. 绘制格子 ---
        self.rects = []
        grid_start_x = start_x + self.LABEL_WIDTH + self.LABEL_GAP

        year = self.current_year
        d1 = datetime.date(year, 1, 1)
        d2 = datetime.date(year, 12, 31)
        start_date = d1 - datetime.timedelta(days=d1.weekday())

        month_labels_drawn = set()

        curr = start_date
        end_date = d2 + datetime.timedelta(days=6)

        while curr <= end_date:
            if curr.year > year + 1: break

            days_diff = (curr - start_date).days
            col = days_diff // 7
            row = curr.weekday()

            if col >= weeks: break

            x = grid_start_x + col * (self.BOX_SIZE + self.SPACING)
            y = start_y + row * (self.BOX_SIZE + self.SPACING)

            rect = QRectF(x, y, self.BOX_SIZE, self.BOX_SIZE)

            if curr.year == year:
                date_str = str(curr)
                val = self.get_value_for_date(date_str)
                color = self.get_color(val)

                painter.setBrush(QBrush(color))

                if date_str == self.hovered_date:
                    painter.setPen(QColor(255, 255, 255, 200))
                    painter.drawRoundedRect(rect, 3, 3)  # 稍微加大圆角
                else:
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(rect, 2, 2)

                self.rects.append((rect, date_str, val))

                # 月份标签
                if curr.day <= 7 and curr.weekday() == 0:
                    m = curr.month
                    if m not in month_labels_drawn:
                        month_name = curr.strftime("%b")
                        painter.setPen(QColor("#8b949e"))
                        # 根据格子大小调整月份文字位置
                        painter.drawText(int(x), start_y - 10, month_name)
                        month_labels_drawn.add(m)
            pass
            curr += datetime.timedelta(days=1)

        # --- D. 绘制右下角 Legend ---
        # 调整 Y 轴位置，因为格子变高了，Legend 也要往下移
        legend_y = start_y + 7 * (self.BOX_SIZE + self.SPACING) + 15
        self.draw_legend(painter, grid_start_x + grid_width, legend_y)

    def draw_legend(self, painter, align_right_x, y_pos):
        box_s = 12  # 图例的格子也稍微大一点 (原 10)
        gap = 4

        text_less = "Less"
        text_more = "More"

        fm = painter.fontMetrics()
        w_less = fm.horizontalAdvance(text_less)
        w_more = fm.horizontalAdvance(text_more)

        # 5个格子 + 间距
        boxes_width = 5 * box_s + 4 * gap
        total_legend_width = w_less + 8 + boxes_width + 8 + w_more

        start_x = align_right_x - total_legend_width

        painter.setPen(QColor("#8b949e"))

        # Draw "Less" (垂直居中对齐)
        text_y = y_pos + box_s - 2
        painter.drawText(int(start_x), int(text_y), text_less)

        curr_x = start_x + w_less + 8
        threshold = self.thresholds.get(self.active_metric, 100)
        levels = [0, threshold * 0.2, threshold * 0.4, threshold * 0.7, threshold]

        for val in levels:
            color = self.get_color(val)
            rect = QRectF(curr_x, y_pos, box_s, box_s)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 2, 2)
            curr_x += box_s + gap

        # Draw "More"
        painter.drawText(int(curr_x + 4), int(text_y), text_more)

    def mouseMoveEvent(self, event):
        pos = event.position()
        found = False
        for r, d, v in self.rects:
            if r.contains(pos):
                if self.hovered_date != d:
                    self.hovered_date = d
                    self.setCursor(Qt.PointingHandCursor)
                    self.update()
                found = True
                break
        if not found and self.hovered_date:
            self.hovered_date = None
            self.setCursor(Qt.ArrowCursor)
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hovered_date = None
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.hovered_date and event.button() == Qt.LeftButton:
            self.date_clicked.emit(self.hovered_date)

    def event(self, event):
        if event.type() == QEvent.Type.ToolTip and self.rects:
            pos = self.mapFromGlobal(QCursor.pos())
            for r, d, v in self.rects:
                if r.contains(pos):
                    if self.active_metric == "Screen Time":
                        # 格式化: 1h 30m 或 45m 或 0m
                        h, rem = divmod(int(v), 3600)
                        m = rem // 60
                        if h > 0:
                            txt = f"{d}\n{h}h {m}m"
                        else:
                            txt = f"{d}\n{m}m"
                    else:
                        txt = f"{d}\n{int(v):,} {self.active_metric}"
                    QToolTip.showText(QCursor.pos(), txt)
                    return True
        return super().event(event)