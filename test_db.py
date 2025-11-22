# test_db.py
import datetime
from src.database import db

today = datetime.date.today().strftime("%Y-%m-%d")

print("today:", today)
print("get_today_stats:", db.get_today_stats())
print("get_hourly_activity:", db.get_hourly_activity(today))
print("get_weekly_trend:", db.get_weekly_trend(today))
print("get_yearly_trend:", db.get_yearly_trend(datetime.date.today().year))
