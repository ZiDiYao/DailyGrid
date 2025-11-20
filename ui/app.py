import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import platform
import csv
import os
import sys
import winreg
from tkinter import filedialog, messagebox
from database import db
from monitor import MonitorService
from .graph import GithubHeatmap, GITHUB_PALETTE
# 引用 painter
from .keyboard_painter import draw_keyboard_heatmap
import datetime
from matplotlib.ticker import FuncFormatter

# --- 1. 字体设置 ---
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Segoe UI']
elif system_name == "Darwin":
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC']
plt.rcParams['axes.unicode_minus'] = False

# --- UI 常量 ---
GH_BG = "#0d1117"
GH_FRAME = "#161b22"
GH_TEXT_MAIN = "#c9d1d9"
GH_TEXT_SUB = "#8b949e"
GH_BLUE = "#1f6feb"
GH_HOVER = "#30363d"
GH_CARD_HOVER = "#21262d"

COLOR_SCREEN_TIME = "#238636"
COLOR_CLICKS = "#1f6feb"
COLOR_KEYS = "#d29922"

IOS_TRACK_COLOR = "#010409"
PILL_RADIUS = 20

APP_COLORS = ['#1f6feb', '#238636', '#d29922', '#8957e5', '#da3633']
TT_BG_NORMAL = "#1f2328"
TT_BG_HIGHLIGHT = "#40464d"

TOOLTIP_FONT = ("Segoe UI", 11)
MAIN_FONT = ("Segoe UI", 12)
NUM_FONT = ("Segoe UI", 24, "bold")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# --- 设置窗口 ---
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Settings")
        self.geometry("400x500")
        self.configure(fg_color=GH_BG)
        self.attributes("-topmost", True)

        self.lbl_title = ctk.CTkLabel(self, text="Settings", font=("Segoe UI", 18, "bold"), text_color=GH_TEXT_MAIN)
        self.lbl_title.pack(pady=20)

        self.frame_main = ctk.CTkFrame(self, fg_color=GH_FRAME)
        self.frame_main.pack(fill="x", padx=20, pady=10)
        self.switch_tracking = ctk.CTkSwitch(
            self.frame_main, text="Enable Tracking", command=self.on_tracking_change,
            text_color=GH_TEXT_MAIN, progress_color=COLOR_SCREEN_TIME
        )
        if not parent.monitor.paused: self.switch_tracking.select()
        self.switch_tracking.pack(padx=10, pady=15, anchor="w")

        self.frame_idle = ctk.CTkFrame(self, fg_color=GH_FRAME)
        self.frame_idle.pack(fill="x", padx=20, pady=10)
        self.lbl_idle = ctk.CTkLabel(self.frame_idle, text="Idle Threshold", text_color=GH_TEXT_MAIN, font=MAIN_FONT)
        self.lbl_idle.pack(anchor="w", padx=10, pady=(10, 0))
        current_idle = parent.monitor.idle_threshold / 60
        self.lbl_idle_val = ctk.CTkLabel(self.frame_idle, text=f"{int(current_idle)} min", text_color=GH_BLUE,
                                         font=("Segoe UI", 12, "bold"))
        self.lbl_idle_val.pack(anchor="e", padx=10, pady=(0, 0))
        self.slider_idle = ctk.CTkSlider(
            self.frame_idle, from_=1, to=20, number_of_steps=19,
            command=self.on_slider_change, progress_color=GH_BLUE, button_color=GH_TEXT_MAIN
        )
        self.slider_idle.set(current_idle)
        self.slider_idle.pack(fill="x", padx=10, pady=(5, 15))

        self.frame_sys = ctk.CTkFrame(self, fg_color=GH_FRAME)
        self.frame_sys.pack(fill="x", padx=20, pady=10)
        self.switch_top = ctk.CTkSwitch(self.frame_sys, text="Always on Top", command=self.on_top_change,
                                        text_color=GH_TEXT_MAIN, progress_color=GH_BLUE)
        if bool(parent.attributes("-topmost")): self.switch_top.select()
        self.switch_top.pack(padx=10, pady=(15, 10), anchor="w")
        self.switch_autostart = ctk.CTkSwitch(self.frame_sys, text="Run on Startup", command=self.on_autostart_change,
                                              text_color=GH_TEXT_MAIN, progress_color=GH_BLUE)
        if self.check_autostart_status(): self.switch_autostart.select()
        self.switch_autostart.pack(padx=10, pady=(0, 15), anchor="w")

        self.btn_export = ctk.CTkButton(
            self, text="Export Data to CSV", command=self.export_data,
            fg_color=GH_FRAME, text_color=GH_TEXT_MAIN, hover_color=GH_HOVER, border_width=1, border_color=GH_HOVER
        )
        self.btn_export.pack(fill="x", padx=20, pady=20)

    def on_tracking_change(self):
        is_enabled = self.switch_tracking.get()
        self.parent_app.monitor.paused = not is_enabled
        self.parent_app.update_status_label()

    def on_slider_change(self, value):
        self.lbl_idle_val.configure(text=f"{int(value)} min")
        self.parent_app.monitor.idle_threshold = int(value) * 60

    def on_top_change(self):
        self.parent_app.attributes("-topmost", self.switch_top.get())

    def check_autostart_status(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                                 winreg.KEY_READ)
            winreg.QueryValueEx(key, "DailyGrid")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False

    def on_autostart_change(self):
        enable = self.switch_autostart.get()
        app_name = "DailyGrid"
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            if enable:
                exe_path = f'"{sys.executable}"' if getattr(sys, 'frozen',
                                                            False) else f'"{sys.executable.replace("python.exe", "pythonw.exe")}" "{os.path.abspath(sys.argv[0])}"'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            else:
                winreg.DeleteValue(key, app_name)
            winreg.CloseKey(key)
        except Exception:
            if enable:
                self.switch_autostart.deselect()
            else:
                self.switch_autostart.select()

    def export_data(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")],
                                                initialfile=f"dailygrid_export_{datetime.date.today()}.csv")
        if filename:
            try:
                data = db.get_all_data()
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Date", "Screen Time", "Clicks", "Keystrokes"])
                    writer.writerows(data)
                messagebox.showinfo("Success", "Data exported!")
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))


# --- 详情页 ---
class DetailPage(ctk.CTkFrame):
    def __init__(self, parent, controller, metric_key="screen_time_seconds"):
        super().__init__(parent, fg_color=GH_BG)
        self.controller = controller
        self.metric_key = metric_key

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=40, pady=30)

        self.btn_back = ctk.CTkButton(
            self.top_bar, text="← Back", width=80, command=lambda: controller.show_frame("DashboardPage"),
            fg_color=GH_FRAME, hover_color=GH_HOVER, text_color=GH_TEXT_MAIN, corner_radius=PILL_RADIUS
        )
        self.btn_back.pack(side="left")

        title_map = {"screen_time_seconds": "Screen Time Trends", "mouse_clicks": "Clicks Trends",
                     "keystrokes": "Keyboard Heatmap"}
        self.lbl_title = ctk.CTkLabel(self.top_bar, text=title_map.get(metric_key, ""), font=("Segoe UI", 20, "bold"),
                                      text_color=GH_TEXT_MAIN)
        self.lbl_title.pack(side="left", padx=20)

        if self.metric_key != "keystrokes":
            self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.control_frame.pack(fill="x", padx=40, pady=10)

            self.seg_period = ctk.CTkSegmentedButton(
                self.control_frame,
                values=["Week", "Month", "Year"],
                command=self.update_chart,
                font=MAIN_FONT,
                corner_radius=PILL_RADIUS,
                selected_color=GH_BLUE,
                text_color="white",
                text_color_disabled=GH_TEXT_SUB,
                unselected_color=IOS_TRACK_COLOR,
                unselected_hover_color=GH_FRAME
            )
            self.seg_period.pack(side="left")
            self.seg_period.set("Week")
        else:
            self.control_frame = None

        self.chart_frame = ctk.CTkFrame(self, fg_color=GH_FRAME, corner_radius=10, border_width=1,
                                        border_color=GH_HOVER)
        self.chart_frame.pack(fill="both", expand=True, padx=40, pady=20)

        fig_size = (12, 5) if self.metric_key == "keystrokes" else (10, 5)

        self.fig = Figure(figsize=fig_size, facecolor=GH_BG)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(GH_BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        if self.metric_key == "keystrokes":
            self.update_keyboard_map()
        else:
            self.update_chart("Week")

    def update_keyboard_map(self):
        key_data = db.get_total_keyboard_heatmap()
        draw_keyboard_heatmap(self.ax, key_data)
        self.canvas.draw()

    def update_chart(self, period):
        if self.metric_key == "keystrokes": return

        data = db.get_calendar_data(period)
        dates_str = [row[0] for row in data]

        metric_idx = 1
        theme_color = GH_BLUE
        if self.metric_key == "mouse_clicks":
            metric_idx = 2
            theme_color = COLOR_CLICKS
        elif self.metric_key == "screen_time_seconds":
            theme_color = COLOR_SCREEN_TIME

        if self.control_frame:
            self.seg_period.configure(selected_color=theme_color, selected_hover_color=theme_color)

        today = datetime.date.today()
        raw_values = []
        for i, row in enumerate(data):
            d = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
            val = row[metric_idx]
            if d > today:
                raw_values.append(None)
            else:
                raw_values.append(val)

        current_unit = ""
        processed_values = []
        valid_values = [v for v in raw_values if v is not None]

        if self.metric_key == "screen_time_seconds":
            max_val = max(valid_values) if valid_values else 0
            if max_val < 3600:
                processed_values = [v / 60.0 if v is not None else None for v in raw_values]
                current_unit = "m"
            else:
                processed_values = [v / 3600.0 if v is not None else None for v in raw_values]
                current_unit = "h"
        else:
            processed_values = raw_values

        self.ax.clear()
        x_indices = range(len(processed_values))

        self.ax.plot(x_indices, processed_values, marker='o', color=theme_color, linewidth=2, markersize=5)

        fill_x = []
        fill_y = []
        for x, y in zip(x_indices, processed_values):
            if y is not None:
                fill_x.append(x)
                fill_y.append(y)
        if fill_x: self.ax.fill_between(fill_x, fill_y, color=theme_color, alpha=0.1)

        self.ax.set_facecolor(GH_BG)
        self.ax.grid(True, color="#30363d", linestyle='--', alpha=0.3)
        for spine in self.ax.spines.values(): spine.set_visible(False)
        self.ax.set_ylim(bottom=0)

        def format_y(x, pos):
            if current_unit == "m":
                return f"{int(x)}m"
            elif current_unit == "h":
                return f"{int(x)}h" if x % 1 == 0 else f"{x:.1f}h"
            else:
                return f"{x / 1000:.1f}k" if x >= 1000 else f"{int(x)}"

        self.ax.yaxis.set_major_formatter(FuncFormatter(format_y))
        self.ax.tick_params(axis='y', colors=GH_TEXT_SUB, labelsize=10, length=0)

        dates_dt = [datetime.datetime.strptime(d, "%Y-%m-%d") for d in dates_str]
        tick_indices = []
        tick_labels = []

        if period == "Week":
            tick_indices = [0, 1, 2, 3, 4, 5, 6]
            tick_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        elif period == "Month":
            tick_indices = list(range(0, len(processed_values), 5))
            tick_labels = [f"{i + 1}" for i in tick_indices]
        elif period == "Year":
            last_month = -1
            for i, dt in enumerate(dates_dt):
                if dt.month != last_month:
                    tick_indices.append(i)
                    tick_labels.append(dt.strftime("%b"))
                    last_month = dt.month

        self.ax.set_xticks(tick_indices)
        self.ax.set_xticklabels(tick_labels)
        self.ax.tick_params(axis='x', colors=GH_TEXT_SUB, rotation=0, labelsize=10, length=0)

        if len(x_indices) > 0:
            self.ax.set_xlim(min(x_indices) - 0.5, max(x_indices) + 0.5)

        self.canvas.draw()


# --- 主仪表盘页 ---
class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=GH_BG)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=2)
        self.grid_rowconfigure(4, weight=1)

        # 1. Header (Stats)
        self.stats_container = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_container.grid(row=0, column=0, padx=40, pady=(30, 10), sticky="ew")
        for i in range(3): self.stats_container.grid_columnconfigure(i, weight=1)

        self.lbl_time = self._create_stat_card(self.stats_container, 0, "Screen Time", "0h 0m", "screen_time_seconds")
        self.lbl_clicks = self._create_stat_card(self.stats_container, 1, "Clicks", "0", "mouse_clicks")
        self.lbl_keys = self._create_stat_card(self.stats_container, 2, "Keystrokes", "0", "keystrokes")

        # 2. Controls
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=1, column=0, padx=40, pady=5, sticky="ew")

        self.seg_button = ctk.CTkSegmentedButton(
            self.control_frame, values=["Screen Time", "Clicks", "Keystrokes"], command=self.on_metric_change,
            font=MAIN_FONT,
            corner_radius=PILL_RADIUS, unselected_color=IOS_TRACK_COLOR, unselected_hover_color=GH_FRAME,
            selected_color=GH_BLUE, selected_hover_color=GH_BLUE, text_color=GH_TEXT_MAIN,
            text_color_disabled=GH_TEXT_SUB
        )
        self.seg_button.pack(side="left")
        self.seg_button.set("Screen Time")

        self.btn_settings = ctk.CTkButton(self.control_frame, text="⚙️", width=40, command=controller.open_settings,
                                          fg_color=GH_FRAME, hover_color=GH_HOVER, text_color=GH_TEXT_MAIN,
                                          corner_radius=10)
        self.btn_settings.pack(side="right", padx=(10, 0))

        self.available_years = db.get_available_years()
        self.selected_year = self.available_years[0]
        self.year_option = ctk.CTkOptionMenu(self.control_frame, values=[str(y) for y in self.available_years],
                                             command=self.on_year_change, width=90, font=MAIN_FONT, fg_color=GH_FRAME,
                                             button_color=GH_FRAME, button_hover_color=GH_HOVER,
                                             text_color=GH_TEXT_MAIN, corner_radius=10)
        self.year_option.pack(side="right", padx=10)

        self.current_metric = "screen_time_seconds"

        # Title
        self.lbl_heatmap_title = ctk.CTkLabel(self, text="Overall Activity", font=("Segoe UI", 14, "bold"),
                                              text_color=GH_TEXT_MAIN)
        self.lbl_heatmap_title.grid(row=2, column=0, padx=40, pady=(15, 5), sticky="w")

        # 3. Heatmap
        self.chart_border = ctk.CTkFrame(self, fg_color=GH_FRAME, corner_radius=10, border_width=1,
                                         border_color=GH_HOVER)
        self.chart_border.grid(row=3, column=0, padx=40, pady=5, sticky="nsew")

        self.fig = Figure(figsize=(12, 3), facecolor=GH_BG)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(GH_BG)
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self.chart_border)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=2, pady=2)
        self.chart_canvas.get_tk_widget().configure(bg=GH_BG)
        self.chart_canvas.mpl_connect("motion_notify_event", self.on_mouse_hover)
        self.chart_canvas.mpl_connect("axes_leave_event", self.hide_tooltip)
        self.heatmap_obj = None

        # 4. Top Apps
        self.apps_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.apps_frame.grid(row=4, column=0, padx=40, pady=10, sticky="nsew")
        self.lbl_apps_title = ctk.CTkLabel(self.apps_frame, text="Top Apps Today", font=("Segoe UI", 14, "bold"),
                                           text_color=GH_TEXT_MAIN)
        self.lbl_apps_title.pack(anchor="w", pady=(0, 5))

        self.charts_container = ctk.CTkFrame(self.apps_frame, fg_color="transparent")
        self.charts_container.pack(fill="both", expand=True)
        self.charts_container.grid_columnconfigure(0, weight=3)
        self.charts_container.grid_columnconfigure(1, weight=2)

        self.bar_fig = Figure(figsize=(6, 2.5), facecolor=GH_BG)
        self.bar_fig.subplots_adjust(left=0.3, right=0.95, top=0.9, bottom=0.1)
        self.bar_ax = self.bar_fig.add_subplot(111)
        self.bar_ax.set_facecolor(GH_BG)
        self.bar_canvas = FigureCanvasTkAgg(self.bar_fig, master=self.charts_container)
        self.bar_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.bar_canvas.get_tk_widget().configure(bg=GH_BG)

        self.pie_fig = Figure(figsize=(4, 2.5), facecolor=GH_BG)
        self.pie_fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        self.pie_ax = self.pie_fig.add_subplot(111)
        self.pie_ax.set_facecolor(GH_BG)
        self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, master=self.charts_container)
        self.pie_canvas.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.pie_canvas.get_tk_widget().configure(bg=GH_BG)

        # 5. Footer
        self.lbl_status = ctk.CTkLabel(self, text=" ● Tracking active", text_color="#3fb950", font=("Arial", 10))
        self.lbl_status.grid(row=5, column=0, pady=5)

        self.tooltip_window = None
        self.tooltip_label = None
        self.last_hovered_cell = None
        self._init_tooltip()

        self.on_metric_change(self.current_metric)
        self.update_graph()
        self.update_apps_charts()

    def _create_stat_card(self, parent, col_idx, title, value, metric_key):
        card = ctk.CTkFrame(parent, fg_color=GH_FRAME, corner_radius=10, border_width=1, border_color=GH_HOVER)
        card.grid(row=0, column=col_idx, padx=10, sticky="ew")

        def on_enter(e):
            card.configure(fg_color=GH_CARD_HOVER)

        def on_leave(e):
            card.configure(fg_color=GH_FRAME)

        def on_click(event):
            self.controller.show_detail(metric_key)

        for widget in [card]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
            widget.configure(cursor="hand2")

        lbl_title = ctk.CTkLabel(card, text=title, font=("Segoe UI", 13), text_color=GH_TEXT_SUB)
        lbl_title.pack(pady=(15, 0))
        lbl_val = ctk.CTkLabel(card, text=value, font=NUM_FONT, text_color=GH_TEXT_MAIN)
        lbl_val.pack(pady=(0, 15))

        for lbl in [lbl_title, lbl_val]:
            lbl.bind("<Button-1>", on_click)
            lbl.bind("<Enter>", on_enter)
            lbl.bind("<Leave>", on_leave)
            lbl.configure(cursor="hand2")
        return lbl_val

    def _init_tooltip(self):
        self.tooltip_window = ctk.CTkToplevel(self)
        self.tooltip_window.withdraw()
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_attributes("-topmost", True)
        self.tooltip_window.configure(fg_color=TT_BG_NORMAL)
        self.tooltip_label = ctk.CTkLabel(self.tooltip_window, text="", font=TOOLTIP_FONT, text_color="white", padx=12,
                                          pady=6, bg_color=TT_BG_NORMAL, corner_radius=4)
        self.tooltip_label.pack()

    def on_metric_change(self, value):
        metric_map = {"Screen Time": "screen_time_seconds", "Clicks": "mouse_clicks", "Keystrokes": "keystrokes"}
        if value in metric_map:
            self.current_metric = metric_map[value]
            ui_name = value
        else:
            self.current_metric = value
            inv_map = {v: k for k, v in metric_map.items()}
            ui_name = inv_map.get(value, "Screen Time")

        color_map = {"Screen Time": COLOR_SCREEN_TIME, "Clicks": COLOR_CLICKS, "Keystrokes": COLOR_KEYS}
        hover_map = {"Screen Time": "#2ea043", "Clicks": "#2680eb", "Keystrokes": "#d9a12c"}

        self.seg_button.set(ui_name)
        self.seg_button.configure(
            selected_color=color_map.get(ui_name),
            selected_hover_color=hover_map.get(ui_name),
            text_color_disabled=GH_TEXT_SUB,
            text_color="white"
        )
        self.update_graph()

    def on_year_change(self, value):
        self.selected_year = int(value)
        self.update_graph()

    def update_graph(self):
        rows = db.get_data_by_year(self.selected_year)
        self.heatmap_obj = GithubHeatmap(rows, metric=self.current_metric, year=self.selected_year)
        self.heatmap_obj.plot(self.ax)
        self.chart_canvas.draw()

    def update_apps_charts(self):
        top_apps = db.get_today_top_apps(limit=5)
        self.bar_ax.clear()
        self.pie_ax.clear()

        if not top_apps:
            self.bar_canvas.draw()
            self.pie_canvas.draw()
            return

        apps_rev = [row[0] for row in reversed(top_apps)]
        durations_rev = [row[1] / 60.0 for row in reversed(top_apps)]
        durations = [row[1] / 60.0 for row in top_apps]

        bar_colors = list(reversed(APP_COLORS[:len(top_apps)]))
        bars = self.bar_ax.barh(apps_rev, durations_rev, color=bar_colors, height=0.5)

        self.bar_ax.set_facecolor(GH_BG)
        for spine in self.bar_ax.spines.values(): spine.set_visible(False)
        self.bar_ax.get_xaxis().set_visible(False)
        self.bar_ax.tick_params(axis='y', colors=GH_TEXT_MAIN, labelsize=10, length=0)

        if durations_rev:
            max_duration = max(durations_rev)
            top_limit = max_duration * 1.2 if max_duration > 0 else 1
            self.bar_ax.set_xlim(0, top_limit)

        for bar in bars:
            width = bar.get_width()
            minutes = int(width)
            time_str = f"{minutes // 60}h {minutes % 60}m" if minutes >= 60 else (
                f"{minutes}m" if minutes >= 1 else "<1m")
            self.bar_ax.text(width + (top_limit * 0.02), bar.get_y() + bar.get_height() / 2,
                             time_str, ha='left', va='center', color=GH_TEXT_SUB, fontsize=9, fontname="Segoe UI")

        def my_autopct(pct):
            return ('%1.0f%%' % pct) if pct > 5 else ''

        wedges, texts, autotexts = self.pie_ax.pie(
            durations, colors=APP_COLORS[:len(top_apps)], labels=None, autopct=my_autopct,
            startangle=90, counterclock=False, wedgeprops={'width': 0.4, 'edgecolor': GH_BG}, pctdistance=0.75
        )
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(8)
            autotext.set_weight('bold')

        self.bar_canvas.draw()
        self.pie_canvas.draw()

    def on_mouse_hover(self, event):
        if self.heatmap_obj is None: return
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            self.hide_tooltip()
            return

        col = int(event.xdata)
        row = int(event.ydata)
        current_cell = (row, col)
        data = self.heatmap_obj.get_info_by_coord(event.xdata, event.ydata)
        if not data:
            self.hide_tooltip()
            return

        if current_cell != self.last_hovered_cell:
            date_str, raw_val, display_val = data
            metric_name = self.current_metric.replace("_", " ").title()
            if "screen_time_seconds" in self.current_metric:
                val_str = f"{int(raw_val // 3600)}h {int((raw_val % 3600) // 60)}m"
                metric_display = "Screen Time"
            else:
                val_str = f"{int(raw_val)}"
                metric_display = metric_name
            self.tooltip_label.configure(text=f"{val_str} {metric_display} on {date_str}")
            self._move_tooltip(event.x, event.y)
            self.tooltip_window.deiconify()
            self.last_hovered_cell = current_cell

    def _move_tooltip(self, x_canvas, y_canvas):
        x_root = self.chart_canvas.get_tk_widget().winfo_rootx() + x_canvas + 25
        y_root = self.chart_canvas.get_tk_widget().winfo_rooty() + y_canvas - 40
        self.tooltip_window.geometry(f"+{int(x_root)}+{int(y_root)}")

    def hide_tooltip(self, event=None):
        if self.tooltip_window: self.tooltip_window.withdraw()
        self.last_hovered_cell = None


# --- 主程序控制器 ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DailyGrid")
        self.geometry("1100x850")
        self.configure(fg_color=GH_BG)

        db.init_db()
        self.monitor = MonitorService(interval=2, idle_threshold=300)
        self.monitor.start()

        # 缓存今日数据 (ScreenTime, Clicks, Keys)
        self.cached_today_stats = (0, 0, 0)

        self.container = ctk.CTkFrame(self, fg_color=GH_BG)
        self.container.pack(fill="both", expand=True)
        self.frames = {}

        self.dashboard = DashboardPage(self.container, self)
        self.frames["DashboardPage"] = self.dashboard
        self.dashboard.grid(row=0, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.show_frame("DashboardPage")

        # 启动双循环
        self.after(2000, self.sync_db_loop)  # 慢循环：同步数据库
        self.after(50, self.update_live_loop)  # 快循环：刷新界面

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def show_detail(self, metric_key):
        if "DetailPage" in self.frames:
            self.frames["DetailPage"].destroy()
        detail_page = DetailPage(self.container, self, metric_key=metric_key)
        self.frames["DetailPage"] = detail_page
        detail_page.grid(row=0, column=0, sticky="nsew")
        detail_page.tkraise()

    def open_settings(self):
        if hasattr(self,
                   'settings_window') and self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
        else:
            self.settings_window = SettingsWindow(self)

    # --- 慢循环：2秒一次，从数据库同步基准数据 ---
    def sync_db_loop(self):
        # 获取今日已归档的数据
        self.cached_today_stats = db.get_today_stats()

        # 顺便更新 Top Apps (这个不需要太快)
        self.dashboard.update_apps_charts()

        self.after(2000, self.sync_db_loop)

    # --- 快循环：50ms一次，读取内存增量并刷新UI ---
    def update_live_loop(self):
        # 1. 获取基准
        base_time, base_clicks, base_keys = self.cached_today_stats

        # 2. 获取增量 (内存中还未写入DB的数据)
        pending_clicks, pending_keys = self.monitor.tracker.get_current_counts()

        # 3. 计算总数
        total_clicks = base_clicks + pending_clicks
        total_keys = base_keys + pending_keys

        # Screen Time 的实时计算比较复杂(涉及到 idle 检测)，为了稳妥，
        # 这里只做 Clicks/Keys 的实时，Screen Time 依然依赖 2秒一次的 DB 同步
        # 或者你可以简单加上 (当前时间 - 上次同步时间) 如果 active 的话
        # 但为了不闪烁，暂时保持 Screen Time 2秒一更，Click/Keys 50ms 一更
        total_time = base_time

        # 4. 更新 UI
        if self.monitor.paused:
            self.dashboard.lbl_status.configure(text=" ● Tracking paused", text_color="#da3633")
        else:
            self.dashboard.lbl_status.configure(text=" ● Tracking active", text_color="#238636")

        h = int(total_time // 3600)
        m = int((total_time % 3600) // 60)

        self.dashboard.lbl_time.configure(text=f"{h}h {m}m")
        self.dashboard.lbl_clicks.configure(text=f"{total_clicks}")
        self.dashboard.lbl_keys.configure(text=f"{total_keys}")

        self.after(50, self.update_live_loop)

    def on_closing(self):
        self.monitor.stop()
        self.destroy()

    def update_status_label(self):
        pass  # 已在 live loop 中处理