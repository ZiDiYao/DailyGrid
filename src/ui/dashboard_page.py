import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from src.database import db
from .graph import GithubHeatmap
from .constants import *

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