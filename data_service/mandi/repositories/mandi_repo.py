import logging
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, asc
from sqlalchemy.dialects.postgresql import insert
from data_service.mandi.models import MandiPrice, ApiRawSnapshot
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

async def insert_raw_snapshot(db: Session, request_params: dict, response_payload: dict) -> None:
    try:
        snapshot = ApiRawSnapshot(
            resource_id="35985678-0d79-46b4-9ed6-6f13308a1d24",
            request_params=request_params,
            response_payload=response_payload
        )
        db.add(snapshot)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting API raw snapshot: {e}")

async def upsert_mandi_prices(db: Session, records: List[dict]):
    """
    Inserts or updates mandi price records using INSERT ... ON CONFLICT DO UPDATE.
    Expects records to be dictionary representing MandiPrice objects.
    """
    if not records:
        return

    stmt = insert(MandiPrice).values(records)

    # Columns to update on conflict
    update_dict = {
        "min_price": stmt.excluded.min_price,
        "max_price": stmt.excluded.max_price,
        "modal_price": stmt.excluded.modal_price,
        "commodity_code": stmt.excluded.commodity_code,
        "ingested_at": func.now()
    }

    on_conflict_stmt = stmt.on_conflict_do_update(
        constraint='uq_mandi_prices_all_keys',
        set_=update_dict
    )

    try:
        db.execute(on_conflict_stmt)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error upserting mandi prices: {e}")
        raise

async def get_raw_prices_from_db(
    db: Session,
    state: str,
    district: Optional[str] = None,
    market: Optional[str] = None,
    commodity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Fetches latest mandi prices from DB with optional filters.
    """
    conditions = [MandiPrice.state == state]
    if district:
        conditions.append(MandiPrice.district == district)
    if market:
        conditions.append(MandiPrice.market == market)
    if commodity:
        conditions.append(MandiPrice.commodity == commodity)

    stmt = select(MandiPrice).where(and_(*conditions)).order_by(
        desc(MandiPrice.arrival_date)
    ).limit(limit).offset(offset)

    result = db.execute(stmt)
    return result.scalars().all()

from sqlalchemy.sql import func
async def get_latest_arrival_date(db: Session, state: str, district: str = None, market: str = None, commodity: str = None):
    """
    Returns the maximum (latest) arrival date for the given filters.
    """
    conditions = [MandiPrice.state == state]
    if district:
        conditions.append(MandiPrice.district == district)
    if market:
        conditions.append(MandiPrice.market == market)
    if commodity:
        conditions.append(MandiPrice.commodity == commodity)

    stmt = select(func.max(MandiPrice.arrival_date)).where(and_(*conditions))
    return db.execute(stmt).scalar()

async def get_prices_for_insights(
    db: Session,
    state: str,
    district: Optional[str] = None,
    market: Optional[str] = None,
    commodity: Optional[str] = None,
    from_date: datetime.date = None
):
    """
    Fetches mandi prices used for insights (from a certain date).
    """
    conditions = [MandiPrice.state == state]
    if district:
        conditions.append(MandiPrice.district == district)
    if market:
        conditions.append(MandiPrice.market == market)
    if commodity:
        conditions.append(MandiPrice.commodity == commodity)
    if from_date:
        conditions.append(MandiPrice.arrival_date >= from_date)

    stmt = select(MandiPrice).where(and_(*conditions)).order_by(asc(MandiPrice.arrival_date))
    result = db.execute(stmt)
    return result.scalars().all()
