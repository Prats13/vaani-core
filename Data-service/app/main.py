import logging
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

# IMPORTANT: Ensure models are imported before create_all so tables correspond to the DB schema
import app.weather.models
import app.crop.models
import app.mandi.models
from app.core.db import get_db, Base, engine
from app.core.cache_service import redis_client

from app.weather import routers as weather_routers
from app.crop import routers as crop_routers
from app.mandi import routers as mandi_routers
from app.search import routers as search_routers

logging.basicConfig(level=logging.INFO)

# Provide synchronous table creation
with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS weather"))
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS crop"))

Base.metadata.create_all(bind=engine)
app.crop.models.CropBase.metadata.create_all(bind=engine)

app = FastAPI(title="Vaani - Weather & Crop Intelligence Service")

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logging.error(f"SERVICE | DB Health check failed: {e}")
        db_status = "error"
        
    try:
        await redis_client.ping()
        redis_status = "ok"
    except Exception as e:
        logging.error(f"SERVICE | Redis Health check failed: {e}")
        redis_status = "error"
    
    logging.info(f"SERVICE | Health check completed: db={db_status}, redis={redis_status}")    
    return {"status": "ok", "db": db_status, "redis": redis_status}

# Mount Routers
app.include_router(weather_routers.router)
app.include_router(crop_routers.router)
app.include_router(mandi_routers.router)
app.include_router(search_routers.router)
