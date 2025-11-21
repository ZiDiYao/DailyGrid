from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSpacerItem, QSizePolicy
from .widgets.stat_card import StatCard
from .widgets.heatmap_widget import HeatmapWidget
from .widgets.pie_chart import TopAppsWidget
from .widgets.achievements import AchievementsWidget  # 【新增】引入成就組件


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.cached_year_data = []
        self.current_year = 2025
        self.current_metric = "Screen Time"

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        # =========================================
        # 1. 頂部統計卡片區
        # =========================================
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(15)

        self.card_time = StatCard("Screen Time", 0, theme_color="#238636")
        self.card_clicks = StatCard("Clicks", 0, theme_color="#1f6feb")
        self.card_keys = StatCard("Keystrokes", 0, theme_color="#d29922")

        self.stats_layout.addWidget(self.card_time)
        self.stats_layout.addWidget(self.card_clicks)
        self.stats_layout.addWidget(self.card_keys)

        self.card_time.clicked.connect(lambda: self.switch_metric("Screen Time"))
        self.card_clicks.clicked.connect(lambda: self.switch_metric("Clicks"))
        self.card_keys.clicked.connect(lambda: self.switch_metric("Keystrokes"))

        self.main_layout.addLayout(self.stats_layout)

        # =========================================
        # 2. 中間熱力圖區域
        # =========================================
        self.lbl_graph_title = QLabel("Overall Activity")
        self.lbl_graph_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #c9d1d9; margin-top: 10px;")
        self.main_layout.addWidget(self.lbl_graph_title)

        self.graph_container = QFrame()
        self.graph_container.setObjectName("Card")
        graph_layout = QVBoxLayout(self.graph_container)

        self.heatmap = HeatmapWidget()
        graph_layout.addWidget(self.heatmap)

        self.main_layout.addWidget(self.graph_container)

        # =========================================
        # 3. 底部 Top Apps 區域
        # =========================================
        self.lbl_apps_title = QLabel("Top Apps Today")
        self.lbl_apps_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #c9d1d9; margin-top: 10px;")
        self.main_layout.addWidget(self.lbl_apps_title)

        self.apps_widget = TopAppsWidget()
        self.main_layout.addWidget(self.apps_widget)

        # =========================================
        # 4. 【新增】Achievements 區域
        # =========================================
        self.lbl_achieve_title = QLabel("Achievements")
        self.lbl_achieve_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #c9d1d9; margin-top: 10px;")
        self.main_layout.addWidget(self.lbl_achieve_title)

        self.achievements_widget = AchievementsWidget()
        self.main_layout.addWidget(self.achievements_widget)

        # =========================================
        # 5. 底部填充
        # =========================================
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.main_layout.addItem(spacer)

        self.switch_metric("Screen Time")

    # --- 以下邏輯保持不變 ---

    def update_stats(self, total_seconds, total_clicks, total_keys):
        self.card_time.update_value(total_seconds, is_time=True)
        self.card_clicks.update_value(total_clicks, is_time=False)
        self.card_keys.update_value(total_keys, is_time=False)

    def update_heatmap_data(self, data_list, year):
        self.cached_year_data = data_list
        self.current_year = year
        self.heatmap.set_data(data_list, year, self.current_metric)

    def update_apps_data(self, top_apps_list):
        self.apps_widget.update_data(top_apps_list)

    def switch_metric(self, metric_name):
        self.current_metric = metric_name
        self.card_time.set_selected(metric_name == "Screen Time")
        self.card_clicks.set_selected(metric_name == "Clicks")
        self.card_keys.set_selected(metric_name == "Keystrokes")
        self.reorder_cards(metric_name)

        if self.cached_year_data:
            self.heatmap.set_data(self.cached_year_data, self.current_year, metric_name)

    def reorder_cards(self, active_metric):
        self.stats_layout.removeWidget(self.card_time)
        self.stats_layout.removeWidget(self.card_clicks)
        self.stats_layout.removeWidget(self.card_keys)

        cards = []
        if active_metric == "Screen Time":
            cards = [self.card_clicks, self.card_time, self.card_keys]
        elif active_metric == "Clicks":
            cards = [self.card_time, self.card_clicks, self.card_keys]
        elif active_metric == "Keystrokes":
            cards = [self.card_time, self.card_keys, self.card_clicks]

        for card in cards:
            self.stats_layout.addWidget(card)