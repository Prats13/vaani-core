from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

def get_now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def get_time_window_utc(days_past: int = 7, days_future: int = 16):
    now = get_now_utc()
    from_ts = now - timedelta(days=days_past)
    to_ts = now + timedelta(days=days_future)
    return from_ts, to_ts

def local_to_utc(local_str: str, tz_name: str = "Asia/Kolkata") -> datetime:
    tz = ZoneInfo(tz_name)
    # Open-Meteo usually returns 'YYYY-MM-DDTHH:MM' or 'YYYY-MM-DD'
    if len(local_str) == 10:  # YYYY-MM-DD
        dt = datetime.strptime(local_str, "%Y-%m-%d")
    else:
        dt = datetime.fromisoformat(local_str)
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

def utc_to_local_str(utc_dt: datetime, tz_name: str = "Asia/Kolkata") -> str:
    tz = ZoneInfo(tz_name)
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(tz).isoformat()
