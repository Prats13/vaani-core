import logging
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db, Base, engine
import app.models  # ensure models are imported before create_all
from app.services.cache_service import redis_client
from app.services.weather_service import get_weather_for_pincode
from app.services.weather_features_service import get_weather_features_for_pincode

logging.basicConfig(level=logging.INFO)

# Provide synchronous table creation
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Weather Intelligence Service")

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logging.error(f"WEATHER SERVICE | DB Health check failed: {e}")
        db_status = "error"
        
    try:
        await redis_client.ping()
        redis_status = "ok"
    except Exception as e:
        logging.error(f"WEATHER SERVICE | Redis Health check failed: {e}")
        redis_status = "error"
    
    logging.info(f"WEATHER SERVICE | Health check completed: db={db_status}, redis={redis_status}")    
    return {"status": "ok", "db": db_status, "redis": redis_status}

@app.get("/v1/weather/{pincode}")
async def get_weather(
    pincode: str,
    days_past: int = Query(7),
    days_future: int = Query(16),
    force_refresh: bool = Query(False),
    db: Session = Depends(get_db)
):
    try:
        logging.info(f"WEATHER SERVICE | Fetching weather for pincode: {pincode}")
        result = await get_weather_for_pincode(db, pincode, days_past, days_future, force_refresh)
        logging.info(f"WEATHER SERVICE | Weather fetched successfully for pincode: {pincode}")
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.error(f"WEATHER SERVICE | Error fetching weather: {e}")
        raise HTTPException(status_code=500, detail="Internal Service Error")

@app.get("/v2/weather/{pincode}")
async def get_weather_v2(
    pincode: str,
    days_past: int = Query(7),
    days_future: int = Query(16),
    include_hourly: bool = Query(False),
    force_refresh: bool = Query(False),
    db: Session = Depends(get_db)
):
    try:
        logging.info(f"WEATHER SERVICE | Fetching v2 weather for pincode: {pincode}")
        result = await get_weather_features_for_pincode(db, pincode, days_past, days_future, include_hourly, force_refresh)
        logging.info(f"WEATHER SERVICE | V2 Weather fetched successfully for pincode: {pincode}")
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.error(f"WEATHER SERVICE | Error fetching v2 weather: {e}")
        raise HTTPException(status_code=500, detail="Internal Service Error")
