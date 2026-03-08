import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, delete
from data_service.weather.models import WeatherDaily, WeatherHourly, WeatherCoverage, WeatherResponse
from data_service.weather.services.geocode_service import resolve_pincode
from data_service.weather.clients.openmeteo_client import fetch_daily_forecast, fetch_hourly_forecast
from data_service.core.cache_service import get_cached_weather, set_cached_weather, generate_cache_key
from data_service.crop.utils.time_utils import get_time_window_utc, get_now_utc, utc_to_local_str, local_to_utc
from data_service.weather.utils.rainfall_utils import is_heavy_rain_day
from core.config import settings

logger = logging.getLogger(__name__)

async def get_weather_for_pincode(db: Session, pincode: str, days_past: int = 7, days_future: int = 16, force_refresh: bool = False):
    logger.info(f"WEATHER SERVICE | GET WEATHER | PINCODE | {pincode}")
    from_ts, to_ts = get_time_window_utc(days_past, days_future)
    from_str = utc_to_local_str(from_ts)[:10]
    to_str = utc_to_local_str(to_ts)[:10]
    
    cache_key = generate_cache_key(pincode, from_str, to_str)
    logger.info(f"WEATHER SERVICE | GET WEATHER | CACHE KEY GENERATED | {cache_key}")
    if not force_refresh:
        cached = await get_cached_weather(cache_key)
        logger.info(f"WEATHER SERVICE | GET WEATHER | CACHE HIT | {cached}")
        if cached:
            return cached
        logger.info(f"WEATHER SERVICE | GET WEATHER | CACHE MISS | {cached}")
            
    # resolve pincode
    loc = await resolve_pincode(db, pincode)
    
    now = get_now_utc()
    coverage = db.query(WeatherCoverage).filter(
        WeatherCoverage.pincode == pincode,
        WeatherCoverage.provider == "open-meteo"
    ).first()
    
    needs_refresh = True
    if coverage and not force_refresh:
        logger.info(f"WEATHER SERVICE | GET WEATHER | COVERAGE | {coverage}")
        stale_threshold = now - timedelta(hours=settings.forecast_refresh_ttl_hours)
        if coverage.last_refresh_at >= stale_threshold:
            needs_refresh = False

    if needs_refresh:
        logger.info(f"WEATHER SERVICE | GET WEATHER | REFRESHING DB FROM OPENMETEO | {pincode}")
        await fetch_and_upsert_weather(db, loc, "open-meteo", past_days=days_past, forecast_days=days_future)
    
    # Query Data
    daily_rows = db.query(WeatherDaily).filter(
        WeatherDaily.pincode == pincode,
        WeatherDaily.provider == "open-meteo"
    ).order_by(WeatherDaily.date_local).all()
    
    heavy_rain_dates = []
    daily_data = []
    
    for row in daily_rows:
        d_dict = {
            "date": row.date_local,
            "temperature_max": row.temperature_max,
            "temperature_min": row.temperature_min,
            "precipitation_sum": row.precipitation_sum,
            "rain_sum": row.rain_sum,
            "showers_sum": row.showers_sum,
            "precip_probability_max": row.precip_probability_max,
            "wind_max": row.wind_max,
            "gust_max": row.gust_max,
            "is_heavy_rain": row.is_heavy_rain
        }
        daily_data.append(d_dict)
        if row.is_heavy_rain:
            heavy_rain_dates.append(row.date_local)
            
    hourly_data = {}
    if heavy_rain_dates:
        # Fetch hourly data only for heavy rain days
        hourly_rows = db.query(WeatherHourly).filter(
            WeatherHourly.pincode == pincode,
            WeatherHourly.provider == "open-meteo"
        ).order_by(WeatherHourly.ts_utc).all()
        
        for hr in hourly_rows:
            local_date = utc_to_local_str(hr.ts_utc)[:10]
            if local_date in heavy_rain_dates:
                if local_date not in hourly_data:
                    hourly_data[local_date] = []
                hourly_data[local_date].append({
                    "time": utc_to_local_str(hr.ts_utc),
                    "temperature_c": hr.temperature_c,
                    "precip_mm": hr.precip_mm,
                    "rh_pct": hr.rh_pct,
                    "wind_kmh": hr.wind_kmh
                })
                
    response_obj = {
        "pincode": loc.pincode,
        "lat": loc.lat,
        "lon": loc.lon,
        "timezone": loc.timezone,
        "daily": daily_data,
        "heavy_rain_days": heavy_rain_dates,
        "hourly": hourly_data
    }
    
    await set_cached_weather(cache_key, response_obj)
    return response_obj

async def fetch_and_upsert_weather(db: Session, loc, provider: str, past_days: int = 7, forecast_days: int = 16):
    now = get_now_utc()
    logger.info(f"WEATHER SERVICE | FETCH AND UPSERT WEATHER | NOW | {now}")
    # 1. Fetch DAILY
    daily_res = await fetch_daily_forecast(loc.lat, loc.lon, past_days, forecast_days)
    
    daily_times = daily_res["daily"]["time"]
    heavy_rain_dates = []
    
    for i, d_time in enumerate(daily_times):
        day_dict = {
            "precipitation_sum": daily_res["daily"].get("precipitation_sum", [])[i],
            "precipitation_probability_max": daily_res["daily"].get("precipitation_probability_max", [])[i],
            "rain_sum": daily_res["daily"].get("rain_sum", [])[i],
        }
        is_heavy = is_heavy_rain_day(day_dict)
        if is_heavy:
            heavy_rain_dates.append(d_time)
            
        # upsert db record
        existing = db.query(WeatherDaily).filter_by(
            pincode=loc.pincode, 
            provider=provider, 
            date_local=d_time
        ).first()
        
        if existing:
            existing.temperature_max = daily_res["daily"].get("temperature_2m_max", [])[i]
            existing.temperature_min = daily_res["daily"].get("temperature_2m_min", [])[i]
            existing.precipitation_sum = day_dict["precipitation_sum"]
            existing.rain_sum = day_dict["rain_sum"]
            existing.showers_sum = daily_res["daily"].get("showers_sum", [])[i]
            existing.precip_probability_max = day_dict["precipitation_probability_max"]
            existing.wind_max = daily_res["daily"].get("wind_speed_10m_max", [])[i]
            existing.gust_max = daily_res["daily"].get("wind_gusts_10m_max", [])[i]
            existing.is_heavy_rain = is_heavy
            existing.ingested_at = now
        else:
            new_daily = WeatherDaily(
                pincode=loc.pincode,
                provider=provider,
                date_local=d_time,
                temperature_max=daily_res["daily"].get("temperature_2m_max", [])[i],
                temperature_min=daily_res["daily"].get("temperature_2m_min", [])[i],
                precipitation_sum=day_dict["precipitation_sum"],
                rain_sum=day_dict["rain_sum"],
                showers_sum=daily_res["daily"].get("showers_sum", [])[i],
                precip_probability_max=day_dict["precipitation_probability_max"],
                wind_max=daily_res["daily"].get("wind_speed_10m_max", [])[i],
                gust_max=daily_res["daily"].get("wind_gusts_10m_max", [])[i],
                is_heavy_rain=is_heavy,
                ingested_at=now
            )
            db.add(new_daily)
    
    # 2. If Heavy Rain, fetch HOURLY
    if heavy_rain_dates:
        logger.info(f"WEATHER SERVICE | FETCH AND UPSERT WEATHER | HEAVY RAIN DETECTED | {heavy_rain_dates}")
        hourly_res = await fetch_hourly_forecast(loc.lat, loc.lon, past_days, forecast_days)
        h_times = hourly_res["hourly"]["time"]
        for i, h_time in enumerate(h_times):
            h_date = h_time[:10]
            if h_date in heavy_rain_dates:
                utc_ts = local_to_utc(h_time, "Asia/Kolkata")
                
                existing_hr = db.query(WeatherHourly).filter_by(
                    pincode=loc.pincode,
                    provider=provider,
                    ts_utc=utc_ts
                ).first()
                
                h_temp = hourly_res["hourly"].get("temperature_2m", [])[i]
                h_precip = hourly_res["hourly"].get("precipitation", [])[i]
                h_rh = hourly_res["hourly"].get("relative_humidity_2m", [])[i]
                h_wind = hourly_res["hourly"].get("wind_speed_10m", [])[i]
                
                if existing_hr:
                    existing_hr.temperature_c = h_temp
                    existing_hr.precip_mm = h_precip
                    existing_hr.rh_pct = h_rh
                    existing_hr.wind_kmh = h_wind
                    existing_hr.ingested_at = now
                else:
                    new_hr = WeatherHourly(
                        pincode=loc.pincode,
                        provider=provider,
                        ts_utc=utc_ts,
                        temperature_c=h_temp,
                        precip_mm=h_precip,
                        rh_pct=h_rh,
                        wind_kmh=h_wind,
                        ingested_at=now
                    )
                    db.add(new_hr)
                    
    # Update Coverage
    cov = db.query(WeatherCoverage).filter_by(pincode=loc.pincode, provider=provider).first()
    
    min_date = min(daily_times)
    max_date = max(daily_times)
    min_ts_utc = local_to_utc(min_date + "T00:00", "Asia/Kolkata")
    max_ts_utc = local_to_utc(max_date + "T23:59", "Asia/Kolkata")
    
    if cov:
        cov.min_ts_utc = min_ts_utc
        cov.max_ts_utc = max_ts_utc
        cov.last_refresh_at = now
        cov.last_success_at = now
    else:
        new_cov = WeatherCoverage(
            pincode=loc.pincode,
            provider=provider,
            min_ts_utc=min_ts_utc,
            max_ts_utc=max_ts_utc,
            last_refresh_at=now,
            last_success_at=now
        )
        db.add(new_cov)
        
    db.commit()
