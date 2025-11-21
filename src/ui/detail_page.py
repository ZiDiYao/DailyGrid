import customtkinter as ctk
import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from src.database import db
from .keyboard_painter import draw_keyboard_heatmap
from .constants import *

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