import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def fetch_daily_forecast(lat: float, lon: float, past_days: int = 7, forecast_days: int = 16) -> dict:
    url = f"{settings.OPEN_METEO_BASE}"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,showers_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max",
        "past_days": past_days,
        "forecast_days": forecast_days,
        "timezone": "Asia/Kolkata"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        logger.info(f"WEATHER SERVICE | OPENMETEO CLIENT | FETCHING | DAILY | lat={lat}, lon={lon}")
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            logger.info(f"WEATHER SERVICE | OPENMETEO CLIENT | FETCH | SUCCESS | DAILY | lat={lat}, lon={lon}")
            return resp.json()
        except httpx.TimeoutException as e:
            logger.error(f"WEATHER SERVICE | OPENMETEO CLIENT | FETCH | TIMEOUT | DAILY | lat={lat}, lon={lon} | error={e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"WEATHER SERVICE | OPENMETEO CLIENT | FETCH | FAILED | DAILY | lat={lat}, lon={lon} | status={e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"WEATHER SERVICE | OPENMETEO CLIENT | FETCH | ERROR | DAILY | lat={lat}, lon={lon} | error={e}")
            raise   

async def fetch_hourly_forecast(lat: float, lon: float, past_days: int = 7, forecast_days: int = 16) -> dict:
    url = f"{settings.OPEN_METEO_BASE}"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,rain,showers,precipitation_probability",
        "past_days": past_days,
        "forecast_days": forecast_days,
        "timezone": "Asia/Kolkata"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        logger.info(f"WEATHER SERVICE | OPENMETEO CLIENT | FETCHING | HOURLY | lat={lat}, lon={lon}")
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            logger.info(f"WEATHER SERVICE | OPENMETEO CLIENT | FETCH | SUCCESS | HOURLY | lat={lat}, lon={lon}")
            return resp.json()
        except httpx.TimeoutException as e:
            logger.error(f"WEATHER SERVICE | OPENMETEO CLIENT | FETCH | TIMEOUT | HOURLY | lat={lat}, lon={lon} | error={e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"WEATHER SERVICE | OPENMETEO CLIENT | FETCH | FAILED | HOURLY | lat={lat}, lon={lon} | status={e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"WEATHER SERVICE | OPENMETEO CLIENT | FETCH | ERROR | HOURLY | lat={lat}, lon={lon} | error={e}")
            raise
