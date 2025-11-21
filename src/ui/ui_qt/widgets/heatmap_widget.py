import datetime
from PySide6.QtWidgets import QWidget, QToolTip, QSizePolicy
from PySide6.QtGui import QPainter, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QRect, QSize, Signal  # 引入 Signal


class HeatmapWidget(QWidget):
    # 【新增】定义一个信号，传出点击的日期字符串 (例如 "2025-11-21")
    date_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- 布局常量 ---
        self.gap = 3
        self.label_width_left = 40
        self.label_height_top = 25
        self.legend_height_bottom = 40

        # --- 颜色配置 ---
        self.empty_color = "#2d333b"
        self.color_schemes = {
            "Screen Time": ["#9be9a8", "#40c463", "#30a14e", "#216e39"],
            "Clicks": ["#79c0ff", "#388bfd", "#1f6feb", "#112542"],
            "Keystrokes": ["#f0b37e", "#d29922", "#b07b16", "#6e4a08"]
        }
        self.current_palette = self.color_schemes["Screen Time"]
        self.text_color = QColor("#8b949e")

        self.data_map = {}
        self.rects = []  # 存储每个格子的区域和日期
        self.year = datetime.date.today().year
        self.metric_name = "Screen Time"
        self.thresholds = [1, 5, 10, 20]
        self.total_weeks = 53

    def minimumSizeHint(self):
        h = self.label_height_top + 7 * (12 + self.gap) + self.legend_height_bottom
        return QSize(500, int(h))

    def set_data(self, data_list, year, metric_name="Screen Time"):
        self.year = year
        self.metric_name = metric_name
        self.data_map = {}

        last_day = datetime.date(year, 12, 31)
        self.total_weeks = int(last_day.strftime("%U")) + 1
        if self.total_weeks < 53: self.total_weeks = 53

        self.current_palette = self.color_schemes.get(metric_name, self.color_schemes["Screen Time"])

        idx = 1
        if metric_name == "Clicks":
            idx = 2
        elif metric_name == "Keystrokes":
            idx = 3

        max_val = 0
        for row in data_list:
            date_str = row[0]
            val = row[idx] if row[idx] else 0
            self.data_map[date_str] = val
            if val > max_val: max_val = val

        if max_val > 0:
            self.thresholds = [1, max_val / 4, max_val / 2, max_val * 0.75]
        else:
            self.thresholds = [1, 10, 50, 100]

        self.update()

    def get_color(self, value):
        if value == 0: return self.empty_color
        if value < self.thresholds[1]: return self.current_palette[0]
        if value < self.thresholds[2]: return self.current_palette[1]
        if value < self.thresholds[3]: return self.current_palette[2]
        return self.current_palette[3]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.rects = []  # 清空碰撞区域

        font = QFont("Segoe UI", 9)
        painter.setFont(font)

        # 1. 计算格子大小
        available_width = self.width() - self.label_width_left - 40
        if self.total_weeks > 0:
            width_based_size = (available_width - (self.total_weeks * self.gap)) / self.total_weeks
        else:
            width_based_size = 12

        available_height = self.height() - self.label_height_top - self.legend_height_bottom - 20
        height_based_size = (available_height - (7 * self.gap)) / 7

        cell_size = int(max(10, min(width_based_size, height_based_size, 28)))

        # 2. 计算居中
        grid_width = self.total_weeks * (cell_size + self.gap) - self.gap
        grid_height = 7 * (cell_size + self.gap) - self.gap
        content_total_width = self.label_width_left + grid_width
        content_total_height = self.label_height_top + grid_height + self.legend_height_bottom

        start_x = max(0, (self.width() - content_total_width) // 2)
        start_y = max(0, (self.height() - content_total_height) // 2)

        grid_start_x = start_x + self.label_width_left
        grid_start_y = start_y + self.label_height_top

        # 3. 绘制星期
        days = {1: "Mon", 3: "Wed", 5: "Fri"}
        painter.setPen(self.text_color)
        for row_idx, text in days.items():
            y = grid_start_y + row_idx * (cell_size + self.gap)
            painter.drawText(QRect(start_x, y, self.label_width_left - 8, cell_size),
                             Qt.AlignRight | Qt.AlignVCenter, text)

        # 4. 绘制网格
        start_date = datetime.date(self.year, 1, 1)
        end_date = datetime.date(self.year, 12, 31)
        current_date = start_date
        start_offset = (current_date.weekday() + 1) % 7

        col = 0
        row = start_offset
        last_month_drawn = -1

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            value = self.data_map.get(date_str, 0)

            x = grid_start_x + col * (cell_size + self.gap)
            y = grid_start_y + row * (cell_size + self.gap)

            if row == 0 or (col == 0 and row == start_offset):
                month = current_date.month
                if month != last_month_drawn:
                    month_name = current_date.strftime("%b")
                    painter.setPen(self.text_color)
                    painter.drawText(x, grid_start_y - 8, month_name)
                    last_month_drawn = month

            rect = QRect(x, y, cell_size, cell_size)
            color = self.get_color(value)

            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.NoPen)
            radius = 3 if cell_size > 16 else 2
            painter.drawRoundedRect(rect, radius, radius)

            # 【关键】存入 rects 供点击检测使用
            self.rects.append((rect, date_str, value))

            current_date += datetime.timedelta(days=1)
            row += 1
            if row > 6:
                row = 0
                col += 1

        # 5. 绘制图例
        legend_y = grid_start_y + grid_height + 15
        legend_icon_size = max(10, cell_size - 2)
        legend_gap = 4
        legend_total_width = 30 + (5 * legend_icon_size + 4 * legend_gap) + 30 + 10
        grid_right_edge = grid_start_x + grid_width
        legend_start_x = grid_right_edge - legend_total_width

        painter.setPen(self.text_color)
        painter.drawText(QRect(legend_start_x, legend_y, 30, legend_icon_size), Qt.AlignRight | Qt.AlignVCenter, "Less")

        current_x = legend_start_x + 35
        full_palette = [self.empty_color] + self.current_palette
        for color_code in full_palette:
            rect = QRect(current_x, legend_y, legend_icon_size, legend_icon_size)
            painter.setBrush(QBrush(QColor(color_code)))
            painter.drawRoundedRect(rect, 2, 2)
            current_x += legend_icon_size + legend_gap

        painter.setPen(self.text_color)
        painter.drawText(QRect(current_x + 5, legend_y, 30, legend_icon_size), Qt.AlignLeft | Qt.AlignVCenter, "More")

    def mouseMoveEvent(self, event):
        pos = event.pos()
        found = False
        for rect, date_str, value in self.rects:
            if rect.contains(pos):
                if self.metric_name == "Screen Time":
                    h = int(value // 3600)
                    m = int((value % 3600) // 60)
                    val_text = f"{h}h {m}m"
                else:
                    val_text = f"{value}"
                # 鼠标变成小手
                self.setCursor(Qt.PointingHandCursor)
                tip_text = f"{date_str}\n{val_text} {self.metric_name}"
                QToolTip.showText(event.globalPos(), tip_text, self)
                found = True
                break

        if not found:
            self.setCursor(Qt.ArrowCursor)
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    # 【新增】点击事件处理
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            for rect, date_str, value in self.rects:
                if rect.contains(pos):
                    # 触发信号，传递日期
                    self.date_clicked.emit(date_str)
                    return
        super().mousePressEvent(event)