import logging
import statistics
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.config import settings
from app.mandi.clients.data_gov_client import fetch_mandi_prices_from_data_gov
from app.mandi.repositories import mandi_repo
from app.core.cache_service import get_cached_data, set_cached_data

logger = logging.getLogger(__name__)

def build_raw_cache_key(state: str, district: str, market: str, commodity: str, limit: int, offset: int) -> str:
    parts = [f"state={state}"]
    if district: parts.append(f"district={district}")
    if market: parts.append(f"market={market}")
    if commodity: parts.append(f"commodity={commodity}")
    parts.append(f"limit={limit}")
    parts.append(f"offset={offset}")
    return "mandi:v1:raw:" + ":".join(parts)

def build_insights_cache_key(state: str, district: str, market: str, commodity: str, days: int, group_by: str) -> str:
    parts = [f"state={state}"]
    if district: parts.append(f"district={district}")
    if market: parts.append(f"market={market}")
    if commodity: parts.append(f"commodity={commodity}")
    parts.append(f"days={days}")
    parts.append(f"group_by={group_by}")
    return "mandi:v2:insights:" + ":".join(parts)

def parse_price(val: str) -> Optional[int]:
    if not val or val.strip().lower() in ['nr', 'na', '', 'null']:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def parse_arrival_date(val: str) -> Optional[datetime.date]:
    if not val:
        return None
    try:
        # e.g. "04/03/2026"
        return datetime.strptime(val.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None

async def fetch_and_upsert_raw(db: Session, state: str, district: str = None, market: str = None, commodity: str = None, limit: int = 50, offset: int = 0) -> dict:
    """
    1. Calls upstream data.gov.in API
    2. Upserts to DB
    3. Returns the raw payload dict
    """
    raw_payload = await fetch_mandi_prices_from_data_gov(state, district, market, commodity, limit, offset)

    # Optional: save snapshot
    # Extract records
    records_to_insert = []
    records = raw_payload.get("records", [])
    
    # Optional logic: save snapshot
    # Wait, we want to save snapshot to DB for debug purposes
    await mandi_repo.insert_raw_snapshot(db, {
        "state": state, "district": district, "market": market, "commodity": commodity, "limit": limit, "offset": offset
    }, raw_payload)
    
    for r in records:
        arr_date = parse_arrival_date(r.get("Arrival_Date"))
        if not arr_date:
            logger.warning(f"MANDI SERVICE | Skipping record with missing/invalid Arrival_Date: {r}")
            continue
        
        records_to_insert.append({
            "arrival_date": arr_date,
            "state": (r.get("State") or "").strip(),
            "district": (r.get("District") or "").strip(),
            "market": (r.get("Market") or "").strip(),
            "commodity": (r.get("Commodity") or "").strip(),
            "variety": (r.get("Variety") or "").strip(),
            "grade": (r.get("Grade") or "").strip(),
            "commodity_code": (r.get("Commodity_Code") or "").strip(),
            "min_price": parse_price(r.get("Min_Price")),
            "max_price": parse_price(r.get("Max_Price")),
            "modal_price": parse_price(r.get("Modal_Price")),
            "source": "data.gov.in"
        })

    if records_to_insert:
        await mandi_repo.upsert_mandi_prices(db, records_to_insert)
    
    logger.info(f"MANDI SERVICE | Fetched {len(records)} records from data.gov.in for State: {state}")
    return raw_payload

async def get_mandi_raw(db: Session, state: str, district: str = None, market: str = None, commodity: str = None, limit: int = 50, offset: int = 0) -> dict:
    cache_key = build_raw_cache_key(state, district, market, commodity, limit, offset)
    cached = await get_cached_data(cache_key)
    if cached:
        logger.info(f"MANDI SERVICE | Cache hit for raw v1: {cache_key}")
        return cached

    logger.info(f"MANDI SERVICE | Cache miss for raw v1: {cache_key}")
    raw_payload = await fetch_and_upsert_raw(db, state, district, market, commodity, limit, offset)

    # Cache response
    ttl = getattr(settings, "MANDI_CACHE_TTL_V1", 10800)
    await set_cached_data(cache_key, raw_payload, ttl)

    logger.info(f"MANDI SERVICE | Cache set for raw v1: {cache_key}")
    return raw_payload

async def get_mandi_insights(db: Session, state: str, district: str = None, market: str = None, commodity: str = None, days: int = 30, group_by: str = "market", force_refresh: bool = False) -> dict:
    cache_key = build_insights_cache_key(state, district, market, commodity, days, group_by)
    
    if not force_refresh:
        cached = await get_cached_data(cache_key)
        if cached:
            logger.info(f"MANDI SERVICE | Cache hit for insights v2: {cache_key}")
            return cached

    # Stale/Empty Check
    # "If DB has no data OR max(arrival_date) < (today - 2 days), refresh from upstream"
    # Wait, the dataset size from data.gov.in is huge, we should fetch multiple pages or just a large limit?
    # Instruction says: "trigger upstream fetch (same as v1) to refresh before computing insights"
    # We will fetch limit=500 for a refresh
    latest_date = await mandi_repo.get_latest_arrival_date(db, state, district, market, commodity)
    
    needs_refresh = False
    today = datetime.now().date()
    if not latest_date:
        needs_refresh = True
    elif (today - latest_date).days >= 2:
        needs_refresh = True

    if needs_refresh or force_refresh:
        logger.info("MANDI SERVICE | Data is stale or missing, triggering fetch_and_upsert_raw before insights")
        try:
            # We fetch a larger chunk to refresh recent data. Max limit is 500.
            await fetch_and_upsert_raw(db, state, district, market, commodity, limit=500, offset=0)
        except Exception as e:
            logger.error(f"MANDI SERVICE | Refresh failed, proceeding with whatever is in DB: {e}")

    # Compute insights
    # Fetch data from DB for the last `days` days
    from_date = today - timedelta(days=days)
    records = await mandi_repo.get_prices_for_insights(db, state, district, market, commodity, from_date)

    if not records:
        return {
            "filters": {"state": state, "district": district, "market": market, "commodity": commodity},
            "window": {"from_date": str(from_date), "to_date": str(today)},
            "latest_date_available": None,
            "summary": {"records_count": 0},
            "message": "No data available in the requested window."
        }

    # Prepare insights object
    valid_prices = [r.modal_price for r in records if r.modal_price is not None]
    
    latest_avail = max([r.arrival_date for r in records])
    summary = {
        "records_count": len(records),
        "min_modal_price": min(valid_prices) if valid_prices else None,
        "max_modal_price": max(valid_prices) if valid_prices else None,
        "avg_modal_price": round(statistics.mean(valid_prices), 2) if valid_prices else None,
        "median_modal_price": statistics.median(valid_prices) if valid_prices else None,
    }
    
    if len(valid_prices) > 1:
        summary["volatility_stddev"] = round(statistics.stdev(valid_prices), 2)
    else:
        summary["volatility_stddev"] = 0

    # Groupings & Time Series
    from collections import defaultdict
    group_stats = defaultdict(list)
    time_series_map = defaultdict(lambda: {"min_p": [], "max_p": [], "modal_p": []})

    for r in records:
        # For time_series overall
        d_str = str(r.arrival_date)
        if r.min_price is not None: time_series_map[d_str]["min_p"].append(r.min_price)
        if r.max_price is not None: time_series_map[d_str]["max_p"].append(r.max_price)
        if r.modal_price is not None: time_series_map[d_str]["modal_p"].append(r.modal_price)

        if group_by == "market":
            k = r.market
        elif group_by == "district":
            k = r.district
        elif group_by == "commodity":
            k = r.commodity
        else:
            k = r.market
        
        # We want to identify the latest price per group
        if r.arrival_date == latest_avail and r.modal_price is not None:
             group_stats[k].append(r.modal_price)

    # Time series aggregated by day (avg of whatever was recorded)
    time_series = []
    for d_str, price_lists in sorted(time_series_map.items()):
        
        ts_node = {
            "date": d_str,
            "min_price": round(statistics.mean(price_lists["min_p"])) if price_lists["min_p"] else None,
            "max_price": round(statistics.mean(price_lists["max_p"])) if price_lists["max_p"] else None,
            "modal_price": round(statistics.mean(price_lists["modal_p"])) if price_lists["modal_p"] else None,
        }
        time_series.append(ts_node)

    # Best items (using latest_avail date)
    best_options = {}
    if group_stats:
        # avg latest modal price per group
        avg_latest = {k: statistics.mean(v) for k, v in group_stats.items()}
        sorted_groups = sorted(avg_latest.items(), key=lambda x: x[1], reverse=True)
        
        best_options["top_5_by_modal_price_latest"] = [{"name": x[0], "modal_price": round(x[1], 2)} for x in sorted_groups[:5]]
        if group_by == "market":
            best_options["best_market_to_sell"] = best_options["top_5_by_modal_price_latest"][0]["name"] if sorted_groups else None

    # Trends
    trends = {}
    if len(time_series) >= 2:
        # e.g. day 0 vs day N
        day0_modal = time_series[0]["modal_price"]
        dayN_modal = time_series[-1]["modal_price"]
        if day0_modal and dayN_modal and day0_modal > 0:
            pct_change = ((dayN_modal - day0_modal) / day0_modal) * 100
            trends = {
                "day0_date": time_series[0]["date"],
                "dayN_date": time_series[-1]["date"],
                "day0_modal": day0_modal,
                "dayN_modal": dayN_modal,
                "pct_change_over_window": round(pct_change, 2)
            }

    insights_payload = {
        "filters": {"state": state, "district": district, "market": market, "commodity": commodity, "days": days, "group_by": group_by},
        "window": {"from_date": str(from_date), "to_date": str(today)},
        "latest_date_available": str(latest_avail) if latest_avail else None,
        "summary": summary,
        "trends": trends,
        "best_options": best_options,
        "time_series": time_series
    }

    # Cache insights
    ttl = getattr(settings, "MANDI_CACHE_TTL_V2", 21600)
    await set_cached_data(cache_key, insights_payload, ttl)
    
    logger.info(f"MANDI SERVICE | Fetched {len(insights_payload)} records from data.gov.in for State: {state}")
    logger.info(f"MANDI SERVICE | HEAD | {insights_payload['time_series'][:5]}")
    logger.info(f"MANDI SERVICE | TAIL | {insights_payload['time_series'][-5:]}")
    return insights_payload
