import threading
import time
from datetime import datetime

# 导入 database.py (使用相对导入)
from ..database import db

# 导入 monitor.window_utils (使用相对导入)
from .window_utils import get_active_process_name

# 导入 monitor.tracker.py 中的 InputListener
from .tracker import InputListener

# 监控间隔（秒）。例如，每 5 秒记录一次活动。
MONITOR_INTERVAL = 5


class MonitorService:
    # 接收 interval 和 idle_threshold
    def __init__(self, interval=MONITOR_INTERVAL, idle_threshold=300):
        super().__init__()
        self.interval = interval

        # 存储闲置阈值
        self.idle_threshold = idle_threshold

        self.running = False
        self._timer: threading.Timer | None = None

        # 记录上一次活动的应用名 (用于计算时长)
        self.last_app_name = None

        # 线程安全地存储上一次的活动数据，供外部UI查询
        self._live_stats = {"screen_time_seconds": 0, "mouse_clicks": 0, "keystrokes": 0}
        self._live_stats_lock = threading.Lock()

        # 初始化数据库和输入监听器
        db.init_db()
        # 属性名称保持 input_listener，对应 MainWindow 中的调用
        self.input_listener = InputListener()

        # 记录应用的累计时长 (内存中，达到 interval 后写入DB)
        self._app_durations = {}

    # ======================================================
    # 核心监控逻辑
    # ======================================================
    def _run_monitoring_task(self):
        """
        定时任务：每隔 self.interval 秒执行一次数据采集和写入。
        """
        if not self.running:
            return

        # 1. 重新安排下一次任务
        self._timer = threading.Timer(self.interval, self._run_monitoring_task)
        self._timer.start()

        # 2. 获取当前活动的应用名
        current_app_name = get_active_process_name()

        # 3. 获取输入增量 (点击/按键)
        clicks, keys, key_details = self.input_listener.get_and_reset_counts()

        # 4. 获取闲置时间
        idle_time = self.input_listener.get_idle_time()

        # 5. 判断是否处于活动状态 (未闲置 且 有点击/按键)
        is_active = (
                (clicks > 0) or
                (keys > 0) or
                (idle_time < self.idle_threshold)
        )

        # 6. 计算屏幕/应用使用时长
        screen_time_delta = 0
        app_duration_delta = 0

        if current_app_name and is_active:
            # 只要处于活动状态，就计入屏幕时间
            screen_time_delta = self.interval

            # 如果应用名没变，计入应用时长
            if current_app_name == self.last_app_name:
                app_duration_delta = self.interval

            self.last_app_name = current_app_name
        else:
            # 如果处于闲置状态，不计入时间，但保留 last_app_name
            pass

        # 7. 写入数据库
        if screen_time_delta > 0 or clicks > 0 or keys > 0:

            # --- 写入总统计 (daily_stats, hourly_stats) ---
            db.update_stats(screen_time_delta, clicks, keys)

            # --- 写入应用使用时长 ---
            if app_duration_delta > 0 and current_app_name:
                db.update_app_usage(current_app_name, app_duration_delta)

            # --- 写入键盘按键详情 ---
            if key_details:
                db.update_key_counts(key_details)

        # 8. 更新内存中的实时统计 (用于 UI 仪表盘)
        self._update_live_stats(screen_time_delta, clicks, keys)

    # ======================================================
    # 控制与状态
    # ======================================================
    def start(self):
        if self.running:
            return

        print(f"Monitoring service started with interval {self.interval}s, idle threshold {self.idle_threshold}s.")
        self.running = True
        self.input_listener.start()

        # 初始时获取上一个活动应用名
        self.last_app_name = get_active_process_name()

        # 启动定时任务
        self._run_monitoring_task()

    def stop(self):
        if not self.running:
            return

        print("Monitoring service stopped.")
        self.running = False
        if self._timer:
            self._timer.cancel()
        self.input_listener.stop()

    def _update_live_stats(self, time_delta, clicks_delta, keys_delta):
        """
        实时更新内存中的统计数据，供 UI 轮询。
        """
        with self._live_stats_lock:
            self._live_stats["screen_time_seconds"] += time_delta
            self._live_stats["mouse_clicks"] += clicks_delta
            self._live_stats["keystrokes"] += keys_delta

    def get_current_session_stats(self):
        """
        获取当前会话累计的总统计 (自服务启动以来)
        """
        with self._live_stats_lock:
            return self._live_stats.copy()