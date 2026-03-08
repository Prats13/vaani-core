from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import logging

from app.core.db import get_db
from app.crop.services import crop_catalog_service, crop_intelligence_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Crop Intelligence"])

# TIER 1
@router.get("/v1/crops")
async def get_all_crops(q: str = Query(None), limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    try:
        logger.info("CROP SERVICE | GET /v1/crops")
        return await crop_catalog_service.get_crops(db, q, limit, offset)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/crops: {e}")
        raise HTTPException(500, "Internal Service Error")

@router.get("/v1/states")
async def get_states(db: Session = Depends(get_db)):
    try:
        logger.info("CROP SERVICE | GET /v1/states")
        return await crop_catalog_service.get_states(db)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/states: {e}")
        raise HTTPException(500, "Internal Service Error")

@router.get("/v1/crops/state/{state}")
async def get_crops_by_state(state: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"CROP SERVICE | GET /v1/crops/state/{state}")
        return await crop_catalog_service.get_crops_for_state(db, state)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/crops/state: {e}")
        raise HTTPException(500, "Internal Service Error")

@router.get("/v1/crops/season/{season}")
async def get_crops_by_season(season: str, state: str = Query(...), limit_crops: int = 25, limit_varieties: int = 5, db: Session = Depends(get_db)):
    try:
        logger.info(f"CROP SERVICE | GET /v1/crops/season/{season}")
        return await crop_catalog_service.get_crops_for_season(db, season, state, limit_crops, limit_varieties)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/crops/season: {e}")
        raise HTTPException(500, "Internal Service Error")

@router.get("/v1/crops/month/{month}")
async def get_crops_by_month(month: int, state: str = Query(...), db: Session = Depends(get_db)):
    try:
        logger.info(f"CROP SERVICE | GET /v1/crops/month/{month}")
        return await crop_catalog_service.get_crops_for_month(db, month, state)
    except ValueError as ve:
         raise HTTPException(400, str(ve))
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/crops/month: {e}")
        raise HTTPException(500, "Internal Service Error")

# TIER 2
@router.get("/v1/varieties/top")
async def get_top_varieties(state: str = Query(...), limit: int = 10, db: Session = Depends(get_db)):
    try:
        logger.info("CROP SERVICE | GET /v1/varieties/top")
        return await crop_catalog_service.get_top_varieties_overall(db, state, limit)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/varieties/top: {e}")
        raise HTTPException(500, "Internal Service Error")

@router.get("/v1/varieties/resistant")
async def get_resistant_varieties(crop: str = Query(...), state: str = Query(...), disease: str = Query(...), limit: int = 50, db: Session = Depends(get_db)):
    try:
        logger.info("CROP SERVICE | GET /v1/varieties/resistant")
        return await crop_catalog_service.search_resistant_varieties(db, crop, state, disease, limit)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/varieties/resistant: {e}")
        raise HTTPException(500, "Internal Service Error")

@router.get("/v1/varieties/{crop_name}")
async def get_varieties_for_crop(crop_name: str, state: str = Query(...), limit: int = 50, include_raw_text: bool = Query(False), db: Session = Depends(get_db)):
    try:
        logger.info(f"CROP SERVICE | GET /v1/varieties/{crop_name}")
        return await crop_catalog_service.get_varieties_by_crop(db, crop_name, state, limit, include_raw_text)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/varieties: {e}")
        raise HTTPException(500, "Internal Service Error")

# TIER 3
@router.get("/v1/crop/{crop_name}/calendar")
async def get_crop_calendar_windows_route(crop_name: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"CROP SERVICE | GET /v1/crop/{crop_name}/calendar")
        return await crop_catalog_service.get_calendar_windows(db, crop_name)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/crop/calendar: {e}")
        raise HTTPException(500, "Internal Service Error")

@router.get("/v1/crop/{crop_name}/stage")
async def get_crop_stage_route(crop_name: str, month: int = Query(None), db: Session = Depends(get_db)):
    try:
        logger.info(f"CROP SERVICE | GET /v1/crop/{crop_name}/stage")
        return await crop_catalog_service.get_crop_stage(db, crop_name, month)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/crop/stage: {e}")
        raise HTTPException(500, "Internal Service Error")

# TIER 4 (v2 features integrated with weather)
@router.get("/v2/crop/suitability/{pincode}")
async def get_crop_suitability_route(pincode: str, month: int = Query(None), days_future: int = Query(16), limit_crops: int = Query(25), limit_varieties: int = Query(5), force_refresh: bool = Query(False), db: Session = Depends(get_db)):
    try:
        logger.info(f"CROP SERVICE | GET /v2/crop/suitability/{pincode}")
        return await crop_intelligence_service.get_crop_suitability(db, pincode, month, days_future, limit_crops, limit_varieties, force_refresh)
    except ValueError as ve:
        raise HTTPException(400, str(ve))
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v2/crop/suitability: {e}")
        raise HTTPException(500, "Internal Service Error")

@router.get("/v2/crop/risk/{pincode}")
async def get_crop_risk_route(pincode: str, crop: str = Query(...), month: int = Query(None), days_future: int = Query(16), db: Session = Depends(get_db)):
    try:
        logger.info(f"CROP SERVICE | GET /v2/crop/risk/{pincode}")
        return await crop_intelligence_service.get_crop_risk(db, pincode, crop, month, days_future)
    except ValueError as ve:
        raise HTTPException(400, str(ve))
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v2/crop/risk: {e}")
        raise HTTPException(500, "Internal Service Error")

@router.get("/v2/crop/sowing-window/{pincode}")
async def get_sowing_window_route(pincode: str, month: int = Query(None), days_future: int = Query(16), limit_crops: int = Query(25), db: Session = Depends(get_db)):
    try:
        logger.info(f"CROP SERVICE | GET /v2/crop/sowing-window/{pincode}")
        return await crop_intelligence_service.get_sowing_window(db, pincode, month, days_future, limit_crops)
    except ValueError as ve:
        raise HTTPException(400, str(ve))
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v2/crop/sowing-window: {e}")
        raise HTTPException(500, "Internal Service Error")

# TIER 5
@router.get("/v1/crops/compare")
async def compare_crops_route(crops: str = Query(..., description="Comma separated crop names"), state: str = Query(...), month: int = Query(None), db: Session = Depends(get_db)):
    try:
        logger.info("CROP SERVICE | GET /v1/crops/compare")
        crop_list = [c.strip() for c in crops.split(",") if c.strip()]
        return await crop_catalog_service.compare_crops(db, crop_list, state, month)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/crops/compare: {e}")
        raise HTTPException(500, "Internal Service Error")

@router.get("/v1/crops/{crop_name}/types")
async def get_crop_types_route(crop_name: str, state: str = Query(...), db: Session = Depends(get_db)):
    try:
        logger.info(f"CROP SERVICE | GET /v1/crops/{crop_name}/types")
        return await crop_catalog_service.get_crop_types_stats(db, crop_name, state)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/crops/types: {e}")
        raise HTTPException(500, "Internal Service Error")
