from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import logging

from data_service.core.db import get_db
from data_service.search.services import search_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Global Search"])

@router.get("/v1/search")
async def search_route(q: str = Query(...), state: str = Query(None), limit: int = Query(25), db: Session = Depends(get_db)):
    try:
        logger.info("CROP SERVICE | GET /v1/search")
        return await search_service.execute_search(db, q, state, limit)
    except Exception as e:
        logger.error(f"CROP SERVICE | Error in /v1/search: {e}")
        raise HTTPException(500, "Internal Service Error")
