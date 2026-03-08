import logging
from datetime import datetime
from sqlalchemy.orm import Session
from data_service.weather.services.weather_service import get_weather_for_pincode
from data_service.core.cache_service import get_cached_weather, set_cached_weather
from data_service.weather.utils.features_utils import compute_features
from data_service.crop.utils.time_utils import get_now_utc, get_time_window_utc, utc_to_local_str
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

async def get_weather_features_for_pincode(
    db: Session, 
    pincode: str, 
    days_past: int = 7, 
    days_future: int = 16, 
    include_hourly: bool = False,
    force_refresh: bool = False
):
    incl_hourly_str = str(include_hourly).lower()
    # Cache key format exactly as requested: weather:v2:{pincode}:{days_past}:{days_future}:{include_hourly}:v1
    cache_key = f"weather:v2:{pincode}:{days_past}:{days_future}:{incl_hourly_str}:v1"
    
    if not force_refresh:
        cached = await get_cached_weather(cache_key)
        if cached:
            logger.info(f"WEATHER SERVICE | V2 | Cache hit/miss - hit | key={cache_key}")
            return cached
        logger.info(f"WEATHER SERVICE | V2 | Cache hit/miss - miss | key={cache_key}")

    # Ensure data exists by calling existing v1 function
    v1_result = await get_weather_for_pincode(db, pincode, days_past, days_future, force_refresh)
    
    # "today_local" determination: Use timezone Asia/Kolkata
    tz = ZoneInfo("Asia/Kolkata")
    now_local = datetime.now(tz)
    today_local = now_local.date()
    
    features = compute_features(
        daily_rows=v1_result.get("daily", []),
        heavy_rain_days=v1_result.get("heavy_rain_days", []),
        hourly_by_date=v1_result.get("hourly", {}),
        today_local=today_local,
        include_hourly=include_hourly
    )
    
    # We populate the root fields
    response_obj = {
        "pincode": v1_result.get("pincode", pincode),
        "lat": v1_result.get("lat"),
        "lon": v1_result.get("lon"),
        "timezone": v1_result.get("timezone", "Asia/Kolkata"),
    }
    
    # Append window inputs
    features["window"]["past_days"] = days_past
    features["window"]["future_days"] = days_future
    
    # Merge response_obj with features block
    response_obj.update(features)
    
    # Logging
    logger.info(
        f"V2 | Features computed: dry_spell={features['advisory_flags']['dry_spell']}, "
        f"storm_risk={features['advisory_flags']['storm_risk']}, "
        f"irrigation_needed={features['advisory_flags']['irrigation_needed_for_sowing']}"
    )
    
    window_str = f"[{features['window']['start_date']} to {features['window']['end_date']}]"
    heavy_days_count = len(response_obj['rainfall_summary_mm']['heavy_rain_days'])
    
    logger.info(
        f"V2 | Returned pincode={pincode}, window={window_str}, heavy_days_count={heavy_days_count}"
    )

    await set_cached_weather(cache_key, response_obj)
    return response_obj
