from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import Optional

from app.core.db import get_db
from app.mandi.services import mandi_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Mandi"])

@router.get("/v1/mandi/raw", summary="Get Raw Mandi Prices")
async def get_raw_mandi_prices(
    state: str = Query(..., min_length=2, description="Target state (e.g. 'Maharashtra')"),
    district: Optional[str] = Query(None, description="Optional district"),
    market: Optional[str] = Query(None, description="Optional market name"),
    commodity: Optional[str] = Query(None, description="Optional commodity"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Fetch RAW mandi prices directly mimicking Data.gov.in format.
    Passes through exactly what the upstream gives, caching the response.
    
    Example:
    `curl -X 'GET' 'http://localhost:8081/v1/mandi/raw?state=Maharashtra&commodity=Onion&limit=50'`
    """
    try:
        return await mandi_service.get_mandi_raw(
            db=db,
            state=state,
            district=district,
            market=market,
            commodity=commodity,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error in GET /v1/mandi/raw: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/mandi/insights", summary="Get Cleaned Mandi Insights")
async def get_mandi_insights(
    state: str = Query(..., min_length=2, description="Target state"),
    district: Optional[str] = Query(None, description="Optional district"),
    market: Optional[str] = Query(None, description="Optional market"),
    commodity: Optional[str] = Query(None, description="Optional commodity"),
    days: int = Query(30, description="Window in days (7, 30, 90, 365)"),
    group_by: str = Query("market", description="Grouping key: 'market', 'district', or 'commodity'"),
    force_refresh: bool = Query(False, description="Bypass cache"),
    db: Session = Depends(get_db)
):
    """
    Returns derived insights (summary, trends, best markets) from Mandi Prices data.
    Ensures data freshness behind the scenes.
    
    Example:
    `curl -X 'GET' 'http://localhost:8081/v2/mandi/insights?state=Maharashtra&commodity=Onion&days=30&group_by=market'`
    """
    valid_groups = ["market", "district", "commodity"]
    if group_by not in valid_groups:
        raise HTTPException(status_code=400, detail=f"group_by must be one of {valid_groups}")

    if days not in [7, 30, 90, 365]:
        # we can still allow any numbers, but the requirement specifies "allow 7, 30, 90, 365", let's constrain or default:
        if days <= 0 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")

    try:
        return await mandi_service.get_mandi_insights(
            db=db,
            state=state,
            district=district,
            market=market,
            commodity=commodity,
            days=days,
            group_by=group_by,
            force_refresh=force_refresh
        )
    except Exception as e:
        import traceback
        logger.error(f"Error in GET /v2/mandi/insights:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal Error analyzing Mandi insights.")
