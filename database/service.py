import sqlite3
from datetime import date, timedelta, datetime
import calendar
import os

DB_NAME = "activity_data.db"


class DatabaseManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    screen_time_seconds REAL DEFAULT 0,
                    mouse_clicks INTEGER DEFAULT 0,
                    keystrokes INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_stats (
                    date TEXT,
                    app_name TEXT,
                    duration_seconds REAL DEFAULT 0,
                    PRIMARY KEY (date, app_name)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            # --- 新增：键盘按键统计表 ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keyboard_stats (
                    date TEXT,
                    key_name TEXT,
                    count INTEGER DEFAULT 0,
                    PRIMARY KEY (date, key_name)
                )
            ''')

            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('daily_goal', '4.0')")
            conn.commit()

    # --- 新增：更新具体按键数据 ---
    def update_key_counts(self, key_counts_dict):
        """
        key_counts_dict: {'A': 10, 'Space': 5, ...}
        """
        if not key_counts_dict: return

        today_str = str(date.today())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for key, count in key_counts_dict.items():
                try:
                    cursor.execute('INSERT INTO keyboard_stats (date, key_name, count) VALUES (?, ?, ?)',
                                   (today_str, key, count))
                except sqlite3.IntegrityError:
                    cursor.execute('UPDATE keyboard_stats SET count = count + ? WHERE date = ? AND key_name = ?',
                                   (count, today_str, key))
            conn.commit()

    # --- 新增：获取生涯按键总和 (用于画热力图) ---
    def get_total_keyboard_heatmap(self):
        """返回 { 'A': 100, 'B': 20 ... }"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key_name, SUM(count) FROM keyboard_stats GROUP BY key_name')
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}

    # ... (以下是旧代码，保持不变) ...
    def set_config(self, key, value):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    def get_config(self, key, default=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def get_current_streak(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT date FROM daily_stats WHERE screen_time_seconds > 0 ORDER BY date DESC")
            rows = cursor.fetchall()
        if not rows: return 0
        dates = [datetime.strptime(r[0], "%Y-%m-%d").date() for r in rows]
        today = date.today()
        streak = 0
        latest_date = dates[0]
        if latest_date < today - timedelta(days=1): return 0
        check_date = latest_date
        for d in dates:
            if d == check_date:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        return streak

    def get_lifetime_stats(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(screen_time_seconds), SUM(mouse_clicks), SUM(keystrokes) FROM daily_stats')
            row = cursor.fetchone()
            return (row[0] or 0, row[1] or 0, row[2] or 0)

    def update_stats(self, add_time=0, add_clicks=0, add_keys=0):
        today_str = str(date.today())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO daily_stats (date, screen_time_seconds, mouse_clicks, keystrokes) VALUES (?, ?, ?, ?)',
                    (today_str, add_time, add_clicks, add_keys))
            except sqlite3.IntegrityError:
                cursor.execute(
                    'UPDATE daily_stats SET screen_time_seconds = screen_time_seconds + ?, mouse_clicks = mouse_clicks + ?, keystrokes = keystrokes + ? WHERE date = ?',
                    (add_time, add_clicks, add_keys, today_str))
            conn.commit()

    def update_app_usage(self, app_name, duration_delta):
        today_str = str(date.today())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO app_stats (date, app_name, duration_seconds) VALUES (?, ?, ?)',
                               (today_str, app_name, duration_delta))
            except sqlite3.IntegrityError:
                cursor.execute(
                    'UPDATE app_stats SET duration_seconds = duration_seconds + ? WHERE date = ? AND app_name = ?',
                    (duration_delta, today_str, app_name))
            conn.commit()

    def get_all_data(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_stats ORDER BY date")
            return cursor.fetchall()

    def get_today_stats(self):
        today_str = str(date.today())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT screen_time_seconds, mouse_clicks, keystrokes FROM daily_stats WHERE date = ?",
                           (today_str,))
            row = cursor.fetchone()
            return row if row else (0, 0, 0)

    def get_available_years(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT substr(date, 1, 4) FROM daily_stats ORDER BY date DESC")
            rows = cursor.fetchall()
            years = [int(row[0]) for row in rows]
            current_year = date.today().year
            if current_year not in years: years.insert(0, current_year)
            return years

    def get_data_by_year(self, year):
        year_str = str(year)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_stats WHERE date LIKE ? ORDER BY date", (f"{year_str}-%",))
            return cursor.fetchall()

    def get_today_top_apps(self, limit=5):
        today_str = str(date.today())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT app_name, duration_seconds FROM app_stats WHERE date = ? ORDER BY duration_seconds DESC LIMIT ?',
                (today_str, limit))
            return cursor.fetchall()

    def get_calendar_data(self, period="Week"):
        today = date.today()
        if period == "Week":
            idx = (today.weekday() + 1) % 7
            start_date = today - timedelta(days=idx)
            end_date = start_date + timedelta(days=6)
        elif period == "Month":
            start_date = today.replace(day=1)
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            end_date = start_date.replace(day=days_in_month)
        elif period == "Year":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT date, screen_time_seconds, mouse_clicks, keystrokes FROM daily_stats WHERE date >= ? AND date <= ? ORDER BY date ASC',
                (str(start_date), str(end_date)))
            rows = cursor.fetchall()
        data_dict = {row[0]: row for row in rows}
        result = []
        delta = (end_date - start_date).days + 1
        for i in range(delta):
            current = start_date + timedelta(days=i)
            curr_str = str(current)
            if curr_str in data_dict:
                result.append(data_dict[curr_str])
            else:
                result.append((curr_str, 0, 0, 0))
        return result

    def get_stats_by_range(self, days=7):
        today = date.today()
        start_date = today - timedelta(days=days - 1)
        start_str = str(start_date)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT date, screen_time_seconds, mouse_clicks, keystrokes FROM daily_stats WHERE date >= ? ORDER BY date ASC',
                (start_str,))
            rows = cursor.fetchall()
        result = []
        data_dict = {row[0]: row for row in rows}
        for i in range(days):
            target_date = start_date + timedelta(days=i)
            date_str = str(target_date)
            if date_str in data_dict:
                result.append(data_dict[date_str])
            else:
                result.append((date_str, 0, 0, 0))
        return result