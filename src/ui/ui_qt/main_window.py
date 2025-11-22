import sys
import datetime
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSystemTrayIcon, QMenu, QStackedWidget
from PySide6.QtCore import QFile, QTextStream, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QColor

from src.database import db
# 假设 MonitorService 在 src/monitor/service.py
from src.monitor.service import MonitorService

# 导入页面组件
from src.ui.ui_qt.dashboard import DashboardPage
from src.ui.ui_qt.detail_page import DetailPage
from src.ui.ui_qt.app_detail_page import AppDetailPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DailyGrid (Qt)")
        self.resize(1150, 850)

        # 1. 后端服务初始化
        db.init_db()
        # MonitorService 接收 idle_threshold
        self.monitor = MonitorService(interval=2, idle_threshold=300)
        self.monitor.start()

        self.db_stats = (0, 0, 0)
        self.current_year = datetime.date.today().year

        # 2. UI 基础设置
        self.load_stylesheet()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # --- 多页面堆栈管理 (Stacked Widget) ---
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Index 0: Dashboard (仪表盘主页)
        self.dashboard = DashboardPage()
        self.stack.addWidget(self.dashboard)

        # Index 1: Trend Detail Page (详情页)
        self.detail_page = DetailPage()
        self.stack.addWidget(self.detail_page)

        # Index 2: App Detail Page (应用详情页)
        self.app_detail_page = AppDetailPage()
        self.stack.addWidget(self.app_detail_page)

        # --- 核心路由信号连接 ---
        self.dashboard.navigate_to_detail.connect(self.go_to_trend_detail)
        self.detail_page.back_clicked.connect(self.go_to_dashboard)
        self.dashboard.apps_widget.clicked.connect(self.go_to_app_detail)
        self.app_detail_page.back_clicked.connect(self.go_to_dashboard)

        # --- 系统托盘 ---
        self.setup_tray()

        # --- 定时器 ---
        # UI 刷新 (500ms): 更新实时计数值
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_ui_loop)
        self.ui_timer.start(500)

        # 数据库同步 (2000ms): 写入数据并重绘图表
        self.db_timer = QTimer(self)
        self.db_timer.timeout.connect(self.sync_db_loop)
        self.db_timer.start(2000)

        # 初始执行一次
        self.sync_db_loop()

    # --- 页面跳转逻辑 ---

    def go_to_trend_detail(self, date_str, tab_name="Overview"):
        """
        跳转到趋势详情页
        """
        self.detail_page.load_data(date_str)
        self.detail_page.set_initial_tab(tab_name)
        self.stack.setCurrentWidget(self.detail_page)

    def go_to_app_detail(self, app_name):
        # 未来可以根据 app_name 加载数据
        self.stack.setCurrentWidget(self.app_detail_page)

    def go_to_dashboard(self):
        self.stack.setCurrentWidget(self.dashboard)

    # --- 辅助功能 ---
    def load_stylesheet(self):
        # 加载 QSS 样式表
        file = QFile("src/ui/ui_qt/styles.qss")
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            self.setStyleSheet(stream.readAll())
            file.close()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#1f6feb"))
        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)

        menu = QMenu()
        menu.addAction("Open DailyGrid", self.show_window)
        menu.addSeparator()
        menu.addAction("Quit", self.quit_app)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_click)

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_window()

    def show_window(self):
        self.show()
        self.setWindowState(Qt.WindowActive)
        self.activateWindow()

    def closeEvent(self, event):
        # 拦截关闭事件，最小化到托盘
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_app()

    def quit_app(self):
        self.monitor.stop()
        self.tray_icon.hide()
        sys.exit(0)

    # --- 循环更新逻辑 ---
    def sync_db_loop(self):
        """定时从数据库读取最新数据并更新图表"""
        self.db_stats = db.get_today_stats()

        if self.dashboard and hasattr(self.dashboard, 'year_combo'):
            if self.dashboard.year_combo.count() > 0:
                selected_year = int(self.dashboard.year_combo.currentText())
                if selected_year != self.current_year:
                    self.current_year = selected_year
            else:
                years = db.get_available_years()
                if years:
                    self.dashboard.year_combo.addItems([str(y) for y in years])
                    idx = self.dashboard.year_combo.findText(str(self.current_year))
                    if idx >= 0: self.dashboard.year_combo.setCurrentIndex(idx)

        year_data = db.get_data_by_year(self.current_year)
        top_apps = db.get_today_top_apps(limit=7)  # 注意：这里 limit=5，如果需要 Top 7 请修改

        if self.dashboard:
            self.dashboard.update_heatmap_data(year_data, self.current_year)
            # AppsWidget 内部会处理 limit=7 的逻辑，这里传递原始数据
            self.dashboard.update_apps_data(top_apps)

    def update_ui_loop(self):
        """高频更新：将内存中的实时计数显示在 UI 上"""

        # ❗ 修正：将 .tracker 替换为 .input_listener ❗
        if not self.monitor.input_listener: return

        base_time, base_clicks, base_keys = self.db_stats

        # ❗ 修正：将 .tracker 替换为 .input_listener ❗
        pending_clicks, pending_keys = self.monitor.input_listener.get_current_counts()

        total_time = base_time
        total_clicks = base_clicks + pending_clicks
        total_keys = base_keys + pending_keys

        if self.dashboard:
            self.dashboard.update_stats(total_time, total_clicks, total_keys)