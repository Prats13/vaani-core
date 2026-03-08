from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import logging

from data_service.core.db import get_db
from data_service.weather.services.weather_service import get_weather_for_pincode
from data_service.weather.services.weather_features_service import get_weather_features_for_pincode

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Weather"])

@router.get("/v1/weather/{pincode}")
async def get_weather(
    pincode: str,
    days_past: int = Query(7),
    days_future: int = Query(16),
    force_refresh: bool = Query(False),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"WEATHER SERVICE | Fetching weather for pincode: {pincode}")
        result = await get_weather_for_pincode(db, pincode, days_past, days_future, force_refresh)
        logger.info(f"WEATHER SERVICE | Weather fetched successfully for pincode: {pincode}")
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"WEATHER SERVICE | Error fetching weather: {e}")
        raise HTTPException(status_code=500, detail="Internal Service Error")

@router.get("/v2/weather/{pincode}")
async def get_weather_v2(
    pincode: str,
    days_past: int = Query(7),
    days_future: int = Query(16),
    include_hourly: bool = Query(False),
    force_refresh: bool = Query(False),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"WEATHER SERVICE | Fetching v2 weather for pincode: {pincode}")
        result = await get_weather_features_for_pincode(db, pincode, days_past, days_future, include_hourly, force_refresh)
        logger.info(f"WEATHER SERVICE | V2 Weather fetched successfully for pincode: {pincode}")
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"WEATHER SERVICE | Error fetching v2 weather: {e}")
        raise HTTPException(status_code=500, detail="Internal Service Error")
