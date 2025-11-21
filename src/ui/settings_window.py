import customtkinter as ctk
import winreg
import sys
import os
import csv
import datetime
from tkinter import filedialog, messagebox

from src.database import db
from .constants import *


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
        # 状态更新会在主循环中自动处理

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