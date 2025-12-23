from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import datetime

from src.database import db
from .widgets.chart_widget import ModernChartWidget


class DetailPage(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date_str = datetime.date.today().strftime("%Y-%m-%d")
        self.current_metric = "Screen Time"

        self.metric_colors = {
            "Screen Time": "#238636",
            "Clicks": "#1f6feb",
            "Keystrokes": "#d29922"
        }

        self.main_layout = QVBoxLayout(self)
        # 底部边距设为 10，尽量少留白
        self.main_layout.setContentsMargins(40, 30, 40, 10)
        self.main_layout.setSpacing(10)  # 整体间距收紧

        # 1. Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)

        self.btn_back = QPushButton("← Back")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setFixedWidth(60)
        self.btn_back.setStyleSheet("""
            QPushButton { color: #8b949e; border: none; background: transparent; font-size: 14px; font-weight: 600; text-align: left; }
            QPushButton:hover { color: #58a6ff; }
        """)
        self.btn_back.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(self.btn_back)

        self.lbl_date_title = QLabel("Dec 22, 2025")
        self.lbl_date_title.setStyleSheet(
            "color: #f0f6fc; font-size: 24px; font-weight: bold; background: transparent;")
        header_layout.addWidget(self.lbl_date_title)

        header_layout.addStretch()

        self.tabs = {}
        for name in ["Screen Time", "Clicks", "Keystrokes"]:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.setStyleSheet("""
                QPushButton {
                    color: #8b949e; 
                    background: transparent; 
                    border: 1px solid #30363d; 
                    border-radius: 6px; 
                    padding: 0 16px; 
                    font-weight: 600;
                    font-size: 13px;
                }
                QPushButton:hover { border-color: #c9d1d9; color: #c9d1d9; }
            """)
            btn.clicked.connect(lambda checked, n=name: self.switch_metric(n))
            header_layout.addWidget(btn)
            self.tabs[name] = btn

        self.main_layout.addLayout(header_layout)

        # 2. Hero Data
        hero_layout = QVBoxLayout()
        hero_layout.setSpacing(5)

        self.lbl_hero_val = QLabel("1h 38m")
        self.lbl_hero_val.setStyleSheet(
            "color: #f0f6fc; font-size: 64px; font-weight: bold; font-family: 'Segoe UI'; background: transparent;")
        hero_layout.addWidget(self.lbl_hero_val)

        self.lbl_hero_desc = QLabel("Total Screen Time")
        self.lbl_hero_desc.setStyleSheet("color: #8b949e; font-size: 14px; background: transparent;")
        hero_layout.addWidget(self.lbl_hero_desc)

        self.main_layout.addLayout(hero_layout)

        # 3. Charts Area (上下布局)
        # ScrollArea 保留，以防万一，但内容高度调小
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        content_widget = QWidget()
        content_widget.setAttribute(Qt.WA_TranslucentBackground)

        charts_layout = QVBoxLayout(content_widget)
        charts_layout.setContentsMargins(0, 10, 0, 10)  # 上下边距极小
        charts_layout.setSpacing(20)  # 两个图表间距缩小到 20px

        # --- Chart 1 ---
        v1 = QVBoxLayout()
        v1.setSpacing(5)
        lbl_h = QLabel("Hourly Breakdown")
        lbl_h.setStyleSheet("color: #7d8590; font-weight: 600; font-size: 14px; background: transparent;")
        v1.addWidget(lbl_h)

        self.chart_hourly = ModernChartWidget(chart_type="bar")
        self.chart_hourly.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.chart_hourly.setFixedHeight(220)  # 缩小到 220px
        v1.addWidget(self.chart_hourly)

        charts_layout.addLayout(v1)

        # --- Chart 2 ---
        v2 = QVBoxLayout()
        v2.setSpacing(5)
        lbl_w = QLabel("Weekly Context")
        lbl_w.setStyleSheet("color: #7d8590; font-weight: 600; font-size: 14px; background: transparent;")
        v2.addWidget(lbl_w)

        self.chart_week = ModernChartWidget(chart_type="area")
        self.chart_week.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.chart_week.setFixedHeight(220)  # 缩小到 220px
        v2.addWidget(self.chart_week)

        charts_layout.addLayout(v2)

        scroll.setWidget(content_widget)
        self.main_layout.addWidget(scroll)

    def set_initial_tab(self, metric_name):
        self.switch_metric(metric_name)

    def switch_metric(self, metric_name):
        self.current_metric = metric_name

        active_color = self.metric_colors.get(metric_name, "#f0f6fc")

        for name, btn in self.tabs.items():
            is_active = (name == metric_name)
            btn.setChecked(is_active)

            if is_active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(255, 255, 255, 0.1); 
                        border: 1px solid #f0f6fc; 
                        color: #f0f6fc;
                        border-radius: 6px; padding: 0 16px; font-weight: 600; font-size: 13px;
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        color: #8b949e; background: transparent; border: 1px solid #30363d; 
                        border-radius: 6px; padding: 0 16px; font-weight: 600; font-size: 13px;
                    }
                    QPushButton:hover { border-color: #c9d1d9; color: #c9d1d9; }
                """)

        self.chart_hourly.set_color(active_color)
        self.chart_week.set_color(active_color)

        self.load_data(self.current_date_str)

    def load_data(self, date_str):
        self.current_date_str = date_str
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")

        self.lbl_date_title.setText(dt.strftime("%A, %b %d, %Y"))

        day_data = db.get_hourly_activity(date_str)
        week_data = db.get_weekly_trend(date_str)
        metric = self.current_metric

        h_vals = []
        h_labels = [f"{i}" for i in range(24)]
        total_val = 0

        for row in day_data:
            try:
                if metric == "Screen Time":
                    v = row[1] if len(row) > 1 else 0
                elif metric == "Clicks":
                    v = row[2] if len(row) > 2 else 0
                elif metric == "Keystrokes":
                    v = row[3] if len(row) > 3 else 0
                else:
                    v = 0
            except IndexError:
                v = 0
            h_vals.append(v)
            total_val += v

        if metric == "Screen Time":
            h = int(total_val // 3600)
            m = int((total_val % 3600) // 60)
            self.lbl_hero_val.setText(f"{h}h {m}m")
            self.lbl_hero_desc.setText("Total Screen Time")
        else:
            self.lbl_hero_val.setText(f"{int(total_val):,}")
            self.lbl_hero_desc.setText(f"Total {metric}")

        self.chart_hourly.set_data(h_vals, h_labels)

        w_vals = []
        w_labels = []
        highlight_idx = -1
        for i, row in enumerate(week_data):
            try:
                if metric == "Screen Time":
                    v = row[1] if len(row) > 1 else 0
                elif metric == "Clicks":
                    v = row[2] if len(row) > 2 else 0
                elif metric == "Keystrokes":
                    v = row[3] if len(row) > 3 else 0
                else:
                    v = 0
            except IndexError:
                v = 0
            w_vals.append(v)
            w_dt = datetime.datetime.strptime(row[0], "%Y-%m-%d")
            w_labels.append(w_dt.strftime("%a"))
            if row[0] == date_str: highlight_idx = i

        self.chart_week.set_data(w_vals, w_labels, highlight_idx=highlight_idx)