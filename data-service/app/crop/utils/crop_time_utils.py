import datetime
from typing import List, Tuple, Optional

# Month name mapping
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March",
    4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September",
    10: "October", 11: "November", 12: "December"
}

def month_int_to_name(month: int) -> str:
    """Returns the month name for a given month integer 1-12."""
    return MONTH_NAMES.get(month, "")

def normalize_season(season_str: str) -> str:
    """Standardizes season string to a canonical format like 'Kharif', 'Rabi', 'Zaid', 'Annual'."""
    if not season_str:
        return ""
    s = season_str.lower().strip()
    if "kharif" in s:
        return "Kharif"
    if "rabi" in s:
        return "Rabi"
    if "zaid" in s or "summer" in s:
        return "Zaid"
    if "annual" in s or "all" in s:
        return "Annual"
    return season_str.title()

def month_to_season(month: int) -> Tuple[str, List[str]]:
    """
    Given a month integer (1-12), returns a tuple:
    (Primary Season, [List of candidate tags for fallback])
    
    Rough definitions (India context):
    Kharif: June - October
    Rabi: October - March
    Zaid: March - June
    """
    candidates = []
    
    month_name = month_int_to_name(month)
    if month_name:
        candidates.append(month_name)

    if month in [6, 7, 8, 9, 10]:
        season = "Kharif"
        candidates.extend(["Kharif", "Monsoon"])
    elif month in [10, 11, 12, 1, 2, 3]:
        season = "Rabi"
        candidates.extend(["Rabi", "Winter"])
    else:  # 3,4,5,6
        season = "Zaid"
        candidates.extend(["Zaid", "Summer"])
        
    candidates.append("Annual")
    return season, candidates

def get_current_month_ist() -> int:
    """Returns the current month (1-12) in Asia/Kolkata timezone."""
    # datetime.utcnow() + 5 hours 30 mins
    tz_offset = datetime.timedelta(hours=5, minutes=30)
    ist_time = datetime.datetime.utcnow() + tz_offset
    return ist_time.month

def determine_stage(month: int, sowing: List[int], growth: List[int], harvest: List[int]) -> Optional[str]:
    """Helper to determine the growing stage given month lists."""
    if sowing and month in sowing:
        return "Sowing"
    if harvest and month in harvest:
        return "Harvest"
    if growth and month in growth:
        return "Growth"
    return None
