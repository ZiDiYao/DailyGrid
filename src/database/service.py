import sqlite3
from datetime import date, timedelta, datetime

DB_NAME = "activity_data.db"


class DatabaseManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    # ======================================================
    # 初始化数据库
    # ======================================================
    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 每日汇总
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    screen_time_seconds REAL DEFAULT 0,
                    mouse_clicks INTEGER DEFAULT 0,
                    keystrokes INTEGER DEFAULT 0
                )
                """
            )

            # 每日每应用使用时长
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS app_stats (
                    date TEXT,
                    app_name TEXT,
                    duration_seconds REAL DEFAULT 0,
                    PRIMARY KEY (date, app_name)
                )
                """
            )

            # 设置表（例如 daily_goal）
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )

            # 键盘热力图
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS keyboard_stats (
                    date TEXT,
                    key_name TEXT,
                    count INTEGER DEFAULT 0,
                    PRIMARY KEY (date, key_name)
                )
                """
            )

            # 小时粒度统计（用于 Daily Activity 24h 图）
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS hourly_stats (
                    date TEXT,
                    hour INTEGER,
                    screen_time_seconds REAL DEFAULT 0,
                    mouse_clicks INTEGER DEFAULT 0,
                    keystrokes INTEGER DEFAULT 0,
                    PRIMARY KEY (date, hour)
                )
                """
            )

            # 默认每日目标 4 小时
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES ('daily_goal', '4.0')"
            )

            conn.commit()

    # ======================================================
    # 写入 / 更新
    # ======================================================
    def update_stats(self, add_time=0, add_clicks=0, add_keys=0):
        """
        更新今日的总统计 + 小时统计。
        add_time 单位：秒
        """
        now = datetime.now()
        today_str = now.date().isoformat()
        current_hour = now.hour

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # --- 更新 daily_stats ---
            try:
                cursor.execute(
                    """
                    INSERT INTO daily_stats (date, screen_time_seconds, mouse_clicks, keystrokes)
                    VALUES (?, ?, ?, ?)
                    """,
                    (today_str, add_time, add_clicks, add_keys),
                )
            except sqlite3.IntegrityError:
                cursor.execute(
                    """
                    UPDATE daily_stats
                    SET screen_time_seconds = screen_time_seconds + ?,
                        mouse_clicks        = mouse_clicks        + ?,
                        keystrokes          = keystrokes          + ?
                    WHERE date = ?
                    """,
                    (add_time, add_clicks, add_keys, today_str),
                )

            # --- 更新 hourly_stats（用于 24h 图） ---
            try:
                cursor.execute(
                    """
                    INSERT INTO hourly_stats (date, hour, screen_time_seconds, mouse_clicks, keystrokes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (today_str, current_hour, add_time, add_clicks, add_keys),
                )
            except sqlite3.IntegrityError:
                cursor.execute(
                    """
                    UPDATE hourly_stats
                    SET screen_time_seconds = screen_time_seconds + ?,
                        mouse_clicks        = mouse_clicks        + ?,
                        keystrokes          = keystrokes          + ?
                    WHERE date = ? AND hour = ?
                    """,
                    (add_time, add_clicks, add_keys, today_str, current_hour),
                )

            conn.commit()

    def update_app_usage(self, app_name, duration_delta):
        today_str = str(date.today())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO app_stats (date, app_name, duration_seconds)
                    VALUES (?, ?, ?)
                    """,
                    (today_str, app_name, duration_delta),
                )
            except sqlite3.IntegrityError:
                cursor.execute(
                    """
                    UPDATE app_stats
                    SET duration_seconds = duration_seconds + ?
                    WHERE date = ? AND app_name = ?
                    """,
                    (duration_delta, today_str, app_name),
                )
            conn.commit()

    def update_key_counts(self, key_counts_dict):
        if not key_counts_dict:
            return
        today_str = str(date.today())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for key, count in key_counts_dict.items():
                try:
                    cursor.execute(
                        """
                        INSERT INTO keyboard_stats (date, key_name, count)
                        VALUES (?, ?, ?)
                        """,
                        (today_str, key, count),
                    )
                except sqlite3.IntegrityError:
                    cursor.execute(
                        """
                        UPDATE keyboard_stats
                        SET count = count + ?
                        WHERE date = ? AND key_name = ?
                        """,
                        (count, today_str, key),
                    )
            conn.commit()

    # ======================================================
    # 基础查询
    # ======================================================
    def get_today_stats(self):
        today_str = str(date.today())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT screen_time_seconds, mouse_clicks, keystrokes
                FROM daily_stats
                WHERE date = ?
                """,
                (today_str,),
            )
            row = cursor.fetchone()
            return row if row else (0, 0, 0)

    def get_all_data(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_stats ORDER BY date")
            return cursor.fetchall()

    def get_available_years(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT substr(date, 1, 4) FROM daily_stats ORDER BY date DESC"
            )
            rows = cursor.fetchall()
            years = [int(row[0]) for row in rows]
            current_year = date.today().year
            if current_year not in years:
                years.insert(0, current_year)
            return years

    def get_data_by_year(self, year):
        year_str = str(year)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM daily_stats
                WHERE date LIKE ?
                ORDER BY date
                """,
                (f"{year_str}-%",),
            )
            return cursor.fetchall()

    def get_today_top_apps(self, limit=5):
        today_str = str(date.today())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT app_name, duration_seconds
                FROM app_stats
                WHERE date = ?
                ORDER BY duration_seconds DESC
                LIMIT ?
                """,
                (today_str, limit),
            )
            return cursor.fetchall()

    def get_total_keyboard_heatmap(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT key_name, SUM(count)
                FROM keyboard_stats
                GROUP BY key_name
                """
            )
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}

    # ======================================================
    # 详情页图表相关
    # ======================================================
    def get_top_apps_by_date(self, date_str, limit=5):
        """获取指定日期的 Top Apps"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT app_name, duration_seconds
                FROM app_stats
                WHERE date = ?
                ORDER BY duration_seconds DESC
                LIMIT ?
                """,
                (date_str, limit),
            )
            return cursor.fetchall()

    def get_weekly_trend(self, end_date_str):
        """
        获取指定日期往前 7 天 (含当天) 的趋势数据。
        返回列表: [(date_str, screen_time_seconds, mouse_clicks, keystrokes), ... 7 天]
        """
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        start_date = end_date - timedelta(days=6)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT date, screen_time_seconds, mouse_clicks, keystrokes
                FROM daily_stats
                WHERE date BETWEEN ? AND ?
                ORDER BY date ASC
                """,
                (str(start_date), end_date_str),
            )
            rows = cursor.fetchall()

        data_map = {row[0]: row for row in rows}
        result = []
        current = start_date
        while current <= end_date:
            d_str = current.strftime("%Y-%m-%d")
            if d_str in data_map:
                result.append(data_map[d_str])
            else:
                result.append((d_str, 0, 0, 0))
            current += timedelta(days=1)

        return result

    def get_yearly_trend(self, year):
        """
        获取某年 1-12 月的数据 (用于 Year Trend 图)
        返回长度为 12 的列表：
        - 对于过去/当前月份: (screen_time_seconds_sum, mouse_clicks_sum, keystrokes_sum)
        - 对于未来月份（今年还没到的月）: None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT strftime('%m', date) AS month,
                       SUM(screen_time_seconds),
                       SUM(mouse_clicks),
                       SUM(keystrokes)
                FROM daily_stats
                WHERE strftime('%Y', date) = ?
                GROUP BY month
                ORDER BY month ASC
                """,
                (str(year),),
            )
            rows = cursor.fetchall()

        today = date.today()
        current_year = today.year
        current_month = today.month

        temp_map = {}
        for r in rows:
            month_key = r[0]  # "01" ~ "12"
            temp_map[month_key] = (
                r[1] or 0,
                r[2] or 0,
                r[3] or 0,
            )

        result = []
        for i in range(1, 13):
            month_str = str(i).zfill(2)
            if year == current_year and i > current_month:
                # 未来月份：用 None 占位，前端可以画为“空”
                result.append(None)
            else:
                result.append(temp_map.get(month_str, (0, 0, 0)))

        return result

    def get_hourly_activity(self, date_str):
        """
        获取某天的 24 小时活动分布 (用于 Daily Activity 24h 图)

        返回长度为 24 的列表，每个元素是一个三元组：
            (screen_time_seconds, mouse_clicks, keystrokes)

        下标 0 对应 0 点, 1 对应 1 点, ..., 23 对应 23 点。
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT hour, screen_time_seconds, mouse_clicks, keystrokes
                FROM hourly_stats
                WHERE date = ?
                ORDER BY hour ASC
                """,
                (date_str,),
            )
            rows = cursor.fetchall()

        # 先放 24 个 0
        hourly = [(0, 0, 0) for _ in range(24)]

        for h, sec, clicks, keys in rows:
            if 0 <= h < 24:
                hourly[h] = (sec or 0, clicks or 0, keys or 0)

        return hourly


# 全局单例
db = DatabaseManager()
