import time
import threading
from .idle_check import get_idle_duration
from .tracker import InputListener
from .window_utils import get_active_process_name
from src.database import db

IGNORE_APPS = [
    "explorer.exe", "SearchHost.exe", "LockApp.exe",
    "TextInputHost.exe", "Taskmgr.exe", "ApplicationFrameHost.exe"
]


class MonitorService:
    def __init__(self, interval=2, idle_threshold=300):
        self.interval = interval
        self.idle_threshold = idle_threshold
        self.tracker = InputListener()
        self.running = False
        self.paused = False
        self._thread = None

    def start(self):
        if self.running: return
        self.tracker.start()
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("Monitor service started.")

    def stop(self):
        self.running = False
        self.tracker.stop()
        if self._thread:
            self._thread.join()

    def _loop(self):
        while self.running:
            time.sleep(self.interval)

            # 获取数据 (新增了 details)
            clicks, keys, key_details = self.tracker.get_and_reset_counts()

            if self.paused:
                continue

            idle_sec = get_idle_duration()
            screen_time_delta = 0
            current_app = None

            if idle_sec < self.idle_threshold:
                raw_app_name = get_active_process_name()
                if raw_app_name and raw_app_name not in IGNORE_APPS:
                    current_app = raw_app_name
                    screen_time_delta = self.interval

            if clicks > 0 or keys > 0 or screen_time_delta > 0:
                db.update_stats(add_time=screen_time_delta, add_clicks=clicks, add_keys=keys)
                if current_app:
                    db.update_app_usage(current_app, screen_time_delta)

                # --- 新增：保存按键详情 ---
                if key_details:
                    db.update_key_counts(key_details)