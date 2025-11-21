import customtkinter as ctk
from src.database import db
from src.monitor import MonitorService

from .constants import GH_BG, setup_theme
from .dashboard_page import DashboardPage
from .detail_page import DetailPage
from .settings_window import SettingsWindow


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        setup_theme()  # 应用主题

        self.title("DailyGrid")
        self.geometry("1100x850")
        self.configure(fg_color=GH_BG)

        # 1. 初始化核心服务
        db.init_db()
        self.monitor = MonitorService(interval=2, idle_threshold=300)
        self.monitor.start()

        # 2. 状态缓存
        self.cached_today_stats = (0, 0, 0)
        self.settings_window = None

        # 3. 页面容器
        self.container = ctk.CTkFrame(self, fg_color=GH_BG)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        # 4. 加载主页
        self.show_dashboard()

        # 5. 启动循环任务
        self.after(2000, self.sync_db_loop)
        self.after(50, self.update_live_loop)

    def show_dashboard(self):
        # 懒加载：只有需要时才创建
        if "DashboardPage" not in self.frames:
            page = DashboardPage(self.container, self)
            self.frames["DashboardPage"] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_frame("DashboardPage")

    def show_detail(self, metric_key):
        # 详情页每次可能 key 不一样，建议重建
        if "DetailPage" in self.frames:
            self.frames["DetailPage"].destroy()

        detail_page = DetailPage(self.container, self, metric_key=metric_key)
        self.frames["DetailPage"] = detail_page
        detail_page.grid(row=0, column=0, sticky="nsew")
        detail_page.tkraise()

    def show_frame(self, page_name):
        if page_name in self.frames:
            self.frames[page_name].tkraise()

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.lift()

    # --- 后台逻辑 ---

    def sync_db_loop(self):
        self.cached_today_stats = db.get_today_stats()
        # 只有当 Dashboard 存在时才更新它的图表
        if "DashboardPage" in self.frames:
            self.frames["DashboardPage"].update_apps_charts()
        self.after(2000, self.sync_db_loop)

    def update_live_loop(self):
        # 安全检查：如果 Dashboard 还没加载，就跳过 UI 更新
        if "DashboardPage" not in self.frames:
            self.after(50, self.update_live_loop)
            return

        dashboard = self.frames["DashboardPage"]

        base_time, base_clicks, base_keys = self.cached_today_stats
        pending_clicks, pending_keys = self.monitor.tracker.get_current_counts()

        total_clicks = base_clicks + pending_clicks
        total_keys = base_keys + pending_keys
        total_time = base_time

        # 更新 Dashboard 上的文字
        if self.monitor.paused:
            dashboard.lbl_status.configure(text=" ● Tracking paused", text_color="#da3633")
        else:
            dashboard.lbl_status.configure(text=" ● Tracking active", text_color="#238636")

        h = int(total_time // 3600)
        m = int((total_time % 3600) // 60)
        dashboard.lbl_time.configure(text=f"{h}h {m}m")
        dashboard.lbl_clicks.configure(text=f"{total_clicks}")
        dashboard.lbl_keys.configure(text=f"{total_keys}")

        self.after(50, self.update_live_loop)

    def on_closing(self):
        """点击 X 隐藏窗口，不退出程序"""
        self.withdraw()

    def real_quit(self):
        """托盘点击 Quit，彻底退出"""
        self.monitor.stop()
        self.destroy()
        self.quit()