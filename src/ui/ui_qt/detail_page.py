from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollArea, QFrame
from PySide6.QtCore import Qt, Signal
import datetime
from src.database import db
from .widgets.chart_widget import ChartWidget


class DetailPage(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # --- 滚动区域 ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: transparent; border: 0px;")

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(30)

        self.scroll.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll)

        # --- 1. 导航栏 ---
        nav_layout = QHBoxLayout()
        self.btn_back = QPushButton("← Back")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setFixedWidth(80)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #161b22; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; padding: 5px;
            }
            QPushButton:hover { background-color: #30363d; }
        """)
        self.btn_back.clicked.connect(self.back_clicked.emit)

        self.lbl_title = QLabel("Activity Trends")
        self.lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #c9d1d9;")

        nav_layout.addWidget(self.btn_back)
        nav_layout.addSpacing(20)
        nav_layout.addWidget(self.lbl_title)
        nav_layout.addStretch()

        self.content_layout.addLayout(nav_layout)

        # --- 2. 图表区域 ---

        # 日视图
        self.chart_day = self.create_section("Daily Activity (24h)", "#1f6feb")

        # 周视图
        self.chart_week = self.create_section("Weekly Trend", "#238636")

        # 年视图
        self.chart_year = self.create_section("Yearly Overview", "#d29922")

        self.content_layout.addStretch()

    def create_section(self, title, color_hex):
        container = QFrame()
        container.setObjectName("Card")
        container.setStyleSheet(f"""
            QFrame#Card {{
                background-color: #161b22; border: 1px solid #30363d; border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #c9d1d9;")
        layout.addWidget(lbl)

        chart = ChartWidget()
        layout.addWidget(chart)

        self.content_layout.addWidget(container)
        return chart

    def load_data(self, date_str):
        self.lbl_title.setText(f"Trends for {date_str}")

        # 1. 日数据 (暂时为空)
        day_values = db.get_hourly_activity(date_str)
        day_labels = [f"{i}" for i in range(0, 24)]  # 0-23
        self.chart_day.set_data(day_values, day_labels, "#1f6feb")

        # 2. 周数据
        week_data = db.get_weekly_trend(date_str)
        w_values = []
        w_labels = []
        for row in week_data:
            minutes = row[1] / 60.0 if row[1] else 0
            w_values.append(minutes)
            d = datetime.datetime.strptime(row[0], "%Y-%m-%d")
            w_labels.append(d.strftime("%m/%d"))  # X轴: 11/21

        self.chart_week.set_data(w_values, w_labels, "#238636")

        # 3. 年数据
        current_year = int(date_str.split("-")[0])
        year_data = db.get_yearly_trend(current_year)

        y_values = []
        for val in year_data:
            # 如果 db 返回 None (未来月份)，这里保持 None
            if val is None:
                y_values.append(None)
            else:
                # row: (time, clicks, keys)
                hours = val[0] / 3600.0 if val[0] else 0
                y_values.append(hours)

        y_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        self.chart_year.set_data(y_values, y_labels, "#d29922")