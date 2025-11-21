import sys
import datetime
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSystemTrayIcon, QMenu, QStackedWidget
from PySide6.QtCore import QFile, QTextStream, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QColor

from src.database import db
from src.monitor import MonitorService

from .dashboard import DashboardPage
from .detail_page import DetailPage
from .app_detail_page import AppDetailPage  # 【新增】


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DailyGrid (Qt)")
        self.resize(1100, 850)

        # 1. 服务初始化
        db.init_db()
        self.monitor = MonitorService(interval=2, idle_threshold=300)
        self.monitor.start()

        self.db_stats = (0, 0, 0)
        self.current_year = datetime.date.today().year

        # 2. UI 初始化
        self.load_stylesheet()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # --- 多页面堆栈 ---
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Page 1: Dashboard
        self.dashboard = DashboardPage()
        self.stack.addWidget(self.dashboard)

        # Page 2: Trend Detail Page
        self.detail_page = DetailPage()
        self.stack.addWidget(self.detail_page)

        # Page 3: App Detail Page 【新增】
        self.app_detail_page = AppDetailPage()
        self.stack.addWidget(self.app_detail_page)

        # --- 信号连接 ---

        # 1. 热力图点击 -> 趋势详情页
        self.dashboard.heatmap.date_clicked.connect(self.go_to_trend_detail)
        self.detail_page.back_clicked.connect(self.go_to_dashboard)

        # 2. Top Apps 点击 -> App 详情页 【新增】
        self.dashboard.apps_widget.clicked.connect(self.go_to_app_detail)
        self.app_detail_page.back_clicked.connect(self.go_to_dashboard)

        self.setup_tray()

        # 3. 定时器
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_ui_loop)
        self.ui_timer.start(500)

        self.db_timer = QTimer(self)
        self.db_timer.timeout.connect(self.sync_db_loop)
        self.db_timer.start(2000)

        self.sync_db_loop()

    # --- 跳转逻辑 ---
    def go_to_trend_detail(self, date_str):
        self.detail_page.load_data(date_str)
        self.stack.setCurrentWidget(self.detail_page)

    def go_to_app_detail(self):
        # 以后这里可以传参数，比如加载具体的 App 数据
        self.stack.setCurrentWidget(self.app_detail_page)

    def go_to_dashboard(self):
        self.stack.setCurrentWidget(self.dashboard)

    # --- 辅助方法 ---
    def load_stylesheet(self):
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
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_app()

    def quit_app(self):
        self.monitor.stop()
        self.tray_icon.hide()
        sys.exit(0)

    # --- 循环逻辑 ---
    def sync_db_loop(self):
        self.db_stats = db.get_today_stats()

        if self.dashboard and hasattr(self.dashboard, 'year_combo'):
            selected_year = int(self.dashboard.year_combo.currentText())
            if selected_year != self.current_year:
                self.current_year = selected_year

        year_data = db.get_data_by_year(self.current_year)
        top_apps = db.get_today_top_apps(limit=5)

        if self.dashboard:
            self.dashboard.update_heatmap_data(year_data, self.current_year)
            self.dashboard.update_apps_data(top_apps)

    def update_ui_loop(self):
        if not self.monitor.tracker: return

        base_time, base_clicks, base_keys = self.db_stats
        pending_clicks, pending_keys = self.monitor.tracker.get_current_counts()

        total_time = base_time
        total_clicks = base_clicks + pending_clicks
        total_keys = base_keys + pending_keys

        if self.dashboard:
            self.dashboard.update_stats(total_time, total_clicks, total_keys)