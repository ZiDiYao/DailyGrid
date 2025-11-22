from PySide6.QtWidgets import QWidget, QToolTip
from PySide6.QtCore import Qt, Signal, QRectF, QEvent
from PySide6.QtGui import QPainter, QColor, QCursor
import datetime


class HeatmapWidget(QWidget):
    date_clicked = Signal(str)  # 发送 "YYYY-MM-DD"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)

        # { "YYYY-MM-DD": (time, clicks, keys) }
        self.raw_data = {}
        self.current_year = datetime.date.today().year
        self.rects = []  # (QRectF, date_str, value)

        # 当前显示的模式
        self.active_metric = "Screen Time"
        self.base_color = QColor("#238636")

        # 阈值配置
        self.thresholds = {
            "Screen Time": 8 * 3600,
            "Clicks": 5000,
            "Keystrokes": 10000,
            "Combined": 100
        }

        # 交互状态
        self.hovered_date = None

        # 鼠标追踪
        self.setMouseTracking(True)

    # ------------ 数据与模式 ------------

    def set_data(self, data_rows, year):
        self.current_year = year
        self.raw_data = {}
        if data_rows:
            for row in data_rows:
                # row: (date, time, clicks, keys)
                self.raw_data[row[0]] = (row[1] or 0, row[2] or 0, row[3] or 0)
        self.update()

    def set_metric(self, metric_name, color_hex):
        self.active_metric = metric_name
        self.base_color = QColor(color_hex)
        self.update()

    def get_value_for_date(self, date_str):
        if date_str not in self.raw_data:
            return 0
        time, clicks, keys = self.raw_data[date_str]

        if self.active_metric == "Screen Time":
            return time
        elif self.active_metric == "Clicks":
            return clicks
        elif self.active_metric == "Keystrokes":
            return keys
        else:
            return 0

    def get_color(self, value):
        if value == 0:
            return QColor("#161b22")
        max_val = self.thresholds.get(self.active_metric, 100)
        intensity = min(value / max_val, 1.0)
        alpha = int(50 + (205 * intensity))
        c = QColor(self.base_color)
        c.setAlpha(alpha)
        return c

    # ------------ 绘制 ------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # 固定格子大小和间距
        box_size = 12
        spacing = 3

        # 计算网格总宽度并居中
        columns = 53  # 够一年用了
        grid_width = columns * box_size + (columns - 1) * spacing
        start_x = max(50, (self.width() - grid_width) // 2)
        start_y = 30

        # 背景
        painter.fillRect(self.rect(), QColor(20, 27, 36, 240))  # 更接近 WE


        # --- 左侧星期标签 (Mon / Wed / Fri) ---
        painter.setPen(QColor("#8b949e"))
        weekday_labels = [("Mon", 0), ("Wed", 2), ("Fri", 4)]
        for text, row in weekday_labels:
            y = start_y + row * (box_size + spacing) + box_size - 2
            painter.drawText(5, y, text)

        # --- 生成格子 ---
        self.rects = []

        year = self.current_year
        d1 = datetime.date(year, 1, 1)
        d2 = datetime.date(year, 12, 31)

        # 以当年第一周的「周一」作为第 0 列基准
        first_monday = d1 - datetime.timedelta(days=d1.weekday())

        # 记录每个月第一次出现的列号，用来画月份标签
        month_first_col = {}

        curr = d1
        while curr <= d2:
            date_str = str(curr)

            # row: 周几 (Mon=0..Sun=6)
            weekday = curr.weekday()
            row = weekday

            # col: 从 first_monday 起算已经过了多少周
            week_index = (curr - first_monday).days // 7
            col = week_index

            if col >= columns:
                curr += datetime.timedelta(days=1)
                continue

            x = start_x + col * (box_size + spacing)
            y = start_y + row * (box_size + spacing)
            rect = QRectF(x, y, box_size, box_size)

            value = self.get_value_for_date(date_str)
            color = self.get_color(value)

            # 悬停高亮 or 普通绘制
            if date_str == self.hovered_date:
                painter.setBrush(color)
                painter.setPen(QColor("#ffffff"))
                painter.drawRoundedRect(rect, 2, 2)
            else:
                painter.setBrush(color)
                if value == 0:
                    painter.setPen(QColor("#252b33"))
                else:
                    painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(rect, 2, 2)

            self.rects.append((rect, date_str, value))

            # 月份标签：记录该月第一次出现的列
            m = curr.month
            if m not in month_first_col:
                month_first_col[m] = col

            curr += datetime.timedelta(days=1)

        # --- 绘制月份标签 ---
        painter.setPen(QColor("#8b949e"))
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for m in range(1, 13):
            if m in month_first_col:
                col = month_first_col[m]
                x = start_x + col * (box_size + spacing)
                painter.drawText(x, start_y - 10, month_names[m - 1])

    # ------------ 鼠标交互 ------------

    def mouseMoveEvent(self, event):
        pos = event.position()
        found_hover = False

        for rect, date_str, value in self.rects:
            if rect.contains(pos):
                found_hover = True
                if self.hovered_date != date_str:
                    self.hovered_date = date_str
                    self.setCursor(QCursor(Qt.PointingHandCursor))
                    self.update()
                break

        if not found_hover and self.hovered_date is not None:
            self.hovered_date = None
            self.setCursor(QCursor(Qt.ArrowCursor))
            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self.hovered_date is not None:
            self.hovered_date = None
            self.setCursor(QCursor(Qt.ArrowCursor))
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.hovered_date:
            self.date_clicked.emit(self.hovered_date)
        super().mousePressEvent(event)

    def event(self, event):
        # ToolTip 处理
        if event.type() == QEvent.Type.ToolTip:
            help_event = event
            pos = help_event.pos()
            for rect, date_str, value in self.rects:
                if rect.contains(pos):
                    val_str = str(int(value))
                    if self.active_metric == "Screen Time":
                        h = int(value // 3600)
                        m = int((value % 3600) // 60)
                        val_str = f"{h}h {m}m"
                    QToolTip.showText(
                        help_event.globalPos(),
                        f"{date_str}\n{self.active_metric}: {val_str}"
                    )
                    return True
        return super().event(event)
