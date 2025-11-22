from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QFrame, QStackedWidget, QListWidget, QListWidgetItem, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import datetime

from src.database import db
from .widgets.chart_widget import ChartWidget


class DetailPage(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 当前查看的日期（字符串形式 "YYYY-MM-DD"）
        self.current_date_str = datetime.date.today().strftime("%Y-%m-%d")

        # ========== 1. 主布局：左侧导航 + 右侧内容 ==========
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ---------- 左侧侧边栏 ----------
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet(
            "background-color: #0d1117; border-right: 1px solid #30363d;"
        )

        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 20, 10, 20)
        self.sidebar_layout.setSpacing(10)

        # 返回按钮
        self.btn_back = QPushButton("← Back")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                border: 1px solid #30363d;
                color: #c9d1d9;
                border-radius: 6px;
                padding: 8px;
                text-align: left;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #30363d; }
        """)
        self.btn_back.clicked.connect(self.back_clicked.emit)
        self.sidebar_layout.addWidget(self.btn_back)

        self.sidebar_layout.addSpacing(20)

        lbl_menu = QLabel("VIEWS")
        lbl_menu.setStyleSheet(
            "color: #8b949e; font-size: 11px; font-weight: bold; padding-left: 5px;"
        )
        self.sidebar_layout.addWidget(lbl_menu)

        # 导航列表
        self.nav_list = QListWidget()
        self.nav_list.setFrameShape(QFrame.NoFrame)
        self.nav_list.setFocusPolicy(Qt.NoFocus)
        self.nav_list.setStyleSheet("""
            QListWidget { background: transparent; outline: none; border: none; }
            QListWidget::item {
                color: #8b949e;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
                margin-bottom: 4px;
            }
            QListWidget::item:selected {
                background-color: #1f6feb;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background-color: #21262d;
                color: #c9d1d9;
            }
        """)

        self.sidebar_layout.addWidget(self.nav_list)
        self.main_layout.addWidget(self.sidebar)

        # 切换视图信号
        self.nav_list.currentRowChanged.connect(self.switch_page)

        # ---------- 右侧内容区域 ----------
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.content_layout.addWidget(self.stack)

        self.main_layout.addWidget(self.content_area)

        # 图表引用字典：charts[page_idx][metric]["Day"/"Week"/"Year"] = ChartWidget
        self.charts = {}

        # 初始化页面结构
        self.init_pages()

        # 默认加载“今天”的数据
        self.load_data(self.current_date_str)

    # ======================================================
    # 页面结构初始化
    # ======================================================
    def init_pages(self):
        # 每个 page 只对应一个 metric
        self.pages_config = [
            {"name": "Screen Time", "metrics": ["Screen Time"]},
            {"name": "Clicks", "metrics": ["Clicks"]},
            {"name": "Keystrokes", "metrics": ["Keystrokes"]},
        ]

        # 每个 metric 的样式配置
        self.metrics_info = {
            "Screen Time": {"color": "#238636", "unit": "Time", "icon": "🕒"},
            "Clicks": {"color": "#1f6feb", "unit": "Count", "icon": "🖱️"},
            "Keystrokes": {"color": "#d29922", "unit": "Count", "icon": "⌨️"},
        }

        self.time_frames = ["Day", "Week", "Year"]

        for page_idx, config in enumerate(self.pages_config):

            # ---------- 左侧菜单项 ----------
            item_text = f"  {config['name']}"
            if config["name"] == "Screen Time":
                item_text = "  🕒  Screen Time"
            elif config["name"] == "Clicks":
                item_text = "  🖱️  Clicks"
            elif config["name"] == "Keystrokes":
                item_text = "  ⌨️  Keystrokes"

            item = QListWidgetItem(item_text)
            self.nav_list.addItem(item)

            # ---------- 右侧页面（带滚动） ----------
            page_container = QWidget()
            page_layout = QVBoxLayout(page_container)
            page_layout.setContentsMargins(0, 0, 0, 0)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet("background: transparent;")

            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(40, 40, 40, 40)
            content_layout.setSpacing(30)

            # 页面标题（大字）
            lbl_page_title = QLabel(config["name"])
            lbl_page_title.setStyleSheet(
                "font-size: 28px; font-weight: bold; color: #c9d1d9; margin-bottom: 10px;"
            )
            content_layout.addWidget(lbl_page_title)

            # 初始化字典
            if page_idx not in self.charts:
                self.charts[page_idx] = {}

            # 一个 page 只对应一个 metric，不过代码写成可扩展
            for metric in config["metrics"]:
                info = self.metrics_info[metric]

                # 卡片外框
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: #161b22;
                        border: 1px solid #30363d;
                        border-radius: 12px;
                    }
                """)
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(25, 25, 25, 25)
                card_layout.setSpacing(20)

                # 卡片标题（🕒 Screen Time / 🖱️ Clicks / ⌨️ Keystrokes）
                header_layout = QHBoxLayout()
                lbl_metric = QLabel(f"{info['icon']} {metric}")
                lbl_metric.setStyleSheet(
                    f"font-size: 18px; font-weight: bold; color: {info['color']}; border: none;"
                )
                header_layout.addWidget(lbl_metric)
                header_layout.addStretch()
                card_layout.addLayout(header_layout)

                if metric not in self.charts[page_idx]:
                    self.charts[page_idx][metric] = {}

                # 三个时间尺度：Day / Week / Year
                for tf in self.time_frames:
                    tf_title = "Daily Activity (24h)" if tf == "Day" else f"{tf} Trend"
                    lbl_tf = QLabel(tf_title)
                    lbl_tf.setStyleSheet(
                        "color: #8b949e; font-size: 13px; font-weight: 600; "
                        "border: none; margin-top: 10px;"
                    )
                    card_layout.addWidget(lbl_tf)

                    chart = ChartWidget()
                    chart.theme_color = QColor(info["color"])
                    chart.unit_guess = info["unit"]
                    chart.setFixedHeight(180)

                    card_layout.addWidget(chart)

                    # 存引用
                    self.charts[page_idx][metric][tf] = chart

                content_layout.addWidget(card)

            content_layout.addStretch()
            scroll.setWidget(content_widget)
            page_layout.addWidget(scroll)

            self.stack.addWidget(page_container)

        # 默认选中 Screen Time
        self.nav_list.setCurrentRow(0)

    # ======================================================
    # 导航切换 & 外部控制
    # ======================================================
    def switch_page(self, index: int):
        """左侧导航切换页面时调用"""
        if index < 0 or index >= self.stack.count():
            return
        self.stack.setCurrentIndex(index)

        # 切页面时，用当前日期刷新图表（保证 Clicks / Keystrokes 也看到同一天）
        if self.current_date_str:
            self.load_data(self.current_date_str)

    def set_initial_tab(self, tab_name: str):
        """
        Dashboard 调用：根据名字选中左侧导航。
        tab_name 可能是 "Screen Time" / "Clicks" / "Keystrokes"
        """
        for i, config in enumerate(self.pages_config):
            if config["name"] == tab_name:
                self.nav_list.setCurrentRow(i)
                return

        # 如果传的是老版本的 "Overview" 之类，就默认 Screen Time
        self.nav_list.setCurrentRow(0)

    # ======================================================
    # 数据加载逻辑（核心）
    # ======================================================
    def load_data(self, date_str: str):
        """
        根据日期加载 Day / Week / Year 数据，并刷新全部图表。
        date_str: "YYYY-MM-DD"
        """
        self.current_date_str = date_str  # 记住当前日期

        # 解析年份
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        current_year = dt.year

        # ---------- 1. 从数据库取数据 ----------
        day_data = db.get_hourly_activity(date_str)     # 24h
        week_data = db.get_weekly_trend(date_str)       # 最近 7 天
        year_data = db.get_yearly_trend(current_year)   # 1-12 月

        # ---------- 2. 准备 X 轴标签 ----------
        day_labels = [str(i) for i in range(24)]
        week_labels = []
        year_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        # y 值按 metric 分组
        d_vals = {"Screen Time": [], "Clicks": [], "Keystrokes": []}
        w_vals = {"Screen Time": [], "Clicks": [], "Keystrokes": []}
        y_vals = {"Screen Time": [], "Clicks": [], "Keystrokes": []}

        # ---------- Day: 24 小时 ----------
        for val in day_data:
            # val: (sec, clicks, keys)
            seconds, clicks, keys = val
            d_vals["Screen Time"].append((seconds or 0) / 3600.0)
            d_vals["Clicks"].append(clicks or 0)
            d_vals["Keystrokes"].append(keys or 0)

        # ---------- Week: 7 天 ----------
        for row in week_data:
            # row: (date, sec, clicks, keys)
            d_obj = datetime.datetime.strptime(row[0], "%Y-%m-%d")
            week_labels.append(d_obj.strftime("%a"))
            seconds, clicks, keys = row[1], row[2], row[3]
            w_vals["Screen Time"].append((seconds or 0) / 3600.0)
            w_vals["Clicks"].append(clicks or 0)
            w_vals["Keystrokes"].append(keys or 0)

        # ---------- Year: 12 个月 ----------
        for val in year_data:
            # val: (sec, clicks, keys) 或 None（未来月份）
            if val is None:
                y_vals["Screen Time"].append(None)
                y_vals["Clicks"].append(None)
                y_vals["Keystrokes"].append(None)
            else:
                seconds, clicks, keys = val
                y_vals["Screen Time"].append((seconds or 0) / 3600.0)
                y_vals["Clicks"].append(clicks or 0)
                y_vals["Keystrokes"].append(keys or 0)

        # ---------- 3. 把数据灌进所有页面的 Chart ----------
        for page_idx, page_charts in self.charts.items():
            config = self.pages_config[page_idx]

            for metric in config["metrics"]:
                if metric not in page_charts:
                    continue

                target_charts = page_charts[metric]

                # Day
                if "Day" in target_charts:
                    target_charts["Day"].set_data(d_vals[metric], day_labels)

                # Week
                if "Week" in target_charts:
                    target_charts["Week"].set_data(w_vals[metric], week_labels)

                # Year
                if "Year" in target_charts:
                    target_charts["Year"].set_data(y_vals[metric], year_labels)

        print("METRIC:", metric)
        print("  Day  :", d_vals[metric])
        print("  Week :", w_vals[metric])
        print("  Year :", y_vals[metric])

        target_charts["Day"].set_data(d_vals[metric], day_labels)
        target_charts["Week"].set_data(w_vals[metric], week_labels)
        target_charts["Year"].set_data(y_vals[metric], year_labels)
