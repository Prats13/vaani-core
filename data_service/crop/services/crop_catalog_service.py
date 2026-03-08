import json
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from core.config import settings
from data_service.core.cache_service import redis_client
from data_service.crop.services.crop_query_service import (
    get_crops_paginated, get_states_with_aliases, get_varieties_for_state_by_crop,
    get_varieties_for_crop_in_state, find_resistant_varieties, get_crop_calendar_windows,
    get_candidate_crops_for_state_season
)
from data_service.crop.utils.state_normalization import build_alias_map_from_db, normalize_state_token
from data_service.crop.utils.crop_payload_utils import (
    group_varieties_by_crop, find_top_yield_variety, format_variety_essential, calculate_crop_stats
)
from data_service.crop.utils.crop_time_utils import month_int_to_name, month_to_season, get_current_month_ist, determine_stage

logger = logging.getLogger(__name__)

async def get_or_set_cache(key: str, fallback_fn, ttl: int):
    """Generic cache wrapper for crop APIs."""
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.error(f"CROP SERVICE | REDIS GET ERROR: {e}")

    # Not found in cache
    result = fallback_fn()
    
    try:
        if result is not None:
             await redis_client.setex(key, ttl, json.dumps(result))
    except Exception as e:
        logger.error(f"CROP SERVICE | REDIS SET ERROR: {e}")
        
    return result

# --- TIER 1: CROP CATALOG APIS ---
async def get_crops(db: Session, q: str = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    key = f"crop:crops:q={q}:l={limit}:o={offset}"
    def fetch():
        data = get_crops_paginated(db, q, limit, offset)
        return {"data": data, "limit": limit, "offset": offset, "total": len(data)}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_medium)

async def get_states(db: Session) -> Dict[str, Any]:
    key = "crop:states"
    def fetch():
        return {"states": get_states_with_aliases(db)}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_long)

async def get_crops_for_state(db: Session, state: str) -> Dict[str, Any]:
    key = f"crop:state_crops:{state.lower()}"
    def fetch():
        alias_map = build_alias_map_from_db(db)
        canonical_state = normalize_state_token(state, alias_map)
        
        # Get all varieties for state and group by crop
        vars_data = get_varieties_for_state_by_crop(db, canonical_state)
        grouped = group_varieties_by_crop(vars_data)
        
        results = []
        for c in grouped:
            var_list = c.get("varieties", [])
            top = find_top_yield_variety(var_list)
            results.append({
                "crop_id": c["crop_id"],
                "crop_name": c["crop_name"],
                "varieties_in_state_count": len(var_list),
                "top_yield_variety": top
            })
        return {"state": canonical_state, "crops": results}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_short)

async def get_crops_for_season(db: Session, season: str, state: str, limit_crops: int = 25, limit_varieties: int = 5) -> Dict[str, Any]:
    key = f"crop:season:{season}:{state}:lc={limit_crops}:lv={limit_varieties}"
    def fetch():
        alias_map = build_alias_map_from_db(db)
        canonical_state = normalize_state_token(state, alias_map)
        
        crops = get_candidate_crops_for_state_season(db, canonical_state, season)
        
        results = []
        for c in crops[:limit_crops]:
            # Get varieties locally
            v_all = get_varieties_for_crop_in_state(db, c.crop_name, canonical_state)
            
            # Filter specifically by season tag down to the requested chunk
            v_filtered = []
            for v in v_all:
                if v.sowing_time_tags:
                    for tag in v.sowing_time_tags:
                         if season.lower() in tag.lower():
                             v_filtered.append(format_variety_essential({"name": v.name, "type": v.variety_type, "yield_max": v.yield_max_q_per_ha, "year": v.year}))
                             break
            
            if not v_filtered and v_all:
                 # fallback, just take top yielding from the state
                 v_filtered = [format_variety_essential({"name": v.name, "type": v.variety_type, "yield_max": v.yield_max_q_per_ha, "year": v.year}) for v in v_all[:limit_varieties]]
            else:
                 v_filtered = v_filtered[:limit_varieties]
                 
            results.append({
                "crop_id": c.id,
                "crop_name": c.crop_name,
                "top_varieties_for_season": v_filtered
            })
            
        return {"state": canonical_state, "season": season, "crops": results}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_short)

async def get_crops_for_month(db: Session, month: int, state: str) -> Dict[str, Any]:
    # Month to season fallback
    season, candidates = month_to_season(month)
    month_name = month_int_to_name(month)
    
    key = f"crop:month:{month}:{state}"
    def fetch():
        alias_map = build_alias_map_from_db(db)
        canonical_state = normalize_state_token(state, alias_map)
        
        # Reuse logic from candidate finder, injecting month
        crops = get_candidate_crops_for_state_season(db, canonical_state, season=None, month=month)
        
        # Fill gap: if no crops by explicit calendar month, fallback to season via variety tags
        if not crops:
             crops = get_candidate_crops_for_state_season(db, canonical_state, season=season)
             
        # Format response
        res = []
        for c in crops:
             res.append({
                 "crop_name": c.crop_name,
                 "id": c.id
             })
        return {"state": canonical_state, "month": month, "month_name": month_name, "inferred_season": season, "crops": res[:25]}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_short)

# --- TIER 2: VARIETY APIS ---
async def get_varieties_by_crop(db: Session, crop_name: str, state: str, limit: int = 50, include_raw_text: bool = False) -> Dict[str, Any]:
    key = f"crop:variety:{crop_name}:{state}:{limit}:{include_raw_text}"
    def fetch():
        alias_map = build_alias_map_from_db(db)
        canonical_state = normalize_state_token(state, alias_map)
        
        vs = get_varieties_for_crop_in_state(db, crop_name, canonical_state, limit)
        fmt_vs = []
        for v in vs:
            v_dict = v.__dict__.copy()
            v_dict.pop('_sa_instance_state', None)
            # map new names to old keys expected by helper
            v_dict["type"] = v_dict.pop("variety_type", None)
            v_dict["yield_min"] = v_dict.pop("yield_min_q_per_ha", None)
            v_dict["yield_max"] = v_dict.pop("yield_max_q_per_ha", None)
            v_dict["seed_rate_min"] = v_dict.pop("seed_rate_min_g_per_ha", None)
            v_dict["seed_rate_max"] = v_dict.pop("seed_rate_max_g_per_ha", None)
            v_dict["sowing_time_tags"] = v_dict.pop("sowing_time_tags", None)
            
            fmt_vs.append(format_variety_essential(v_dict, include_raw_text))
            
        return {"crop": crop_name, "state": canonical_state, "varieties": fmt_vs}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_short)

async def get_top_varieties_overall(db: Session, state: str, limit: int = 10) -> Dict[str, Any]:
    key = f"crop:topvar:{state}:{limit}"
    def fetch():
        alias_map = build_alias_map_from_db(db)
        canonical_state = normalize_state_token(state, alias_map)
        
        vars_data = get_varieties_for_state_by_crop(db, canonical_state, limit)
        fmt_vs = []
        for v in vars_data:
             fmt_vs.append({
                 "crop_name": v["crop_name"],
                 "variety": format_variety_essential(v)
             })
        return {"state": canonical_state, "top_varieties": fmt_vs}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_short)

async def search_resistant_varieties(db: Session, crop_name: str, state: str, disease: str, limit: int = 50) -> Dict[str, Any]:
    key = f"crop:resist:{crop_name}:{state}:{disease}:{limit}"
    def fetch():
        alias_map = build_alias_map_from_db(db)
        canonical_state = normalize_state_token(state, alias_map)
        
        res = find_resistant_varieties(db, crop_name, canonical_state, disease, limit)
        
        fmt_vs = []
        for item in res:
             v_dict = item["variety"].__dict__.copy()
             v_dict.pop('_sa_instance_state', None)
             v_dict["matched_snippets"] = item["matched_snippets"]
             # Exclude raw text unless manually passed, use snippets instead
             fmt_vs.append(format_variety_essential(v_dict, False))
        return {"crop": crop_name, "state": canonical_state, "disease": disease, "matches": fmt_vs}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_short)

# --- TIER 3: CALENDAR APIS ---
async def get_calendar_windows(db: Session, crop_name: str) -> Dict[str, Any]:
    key = f"crop:calendar:{crop_name}"
    def fetch():
        cals = get_crop_calendar_windows(db, crop_name)
        res = []
        for c in cals:
             res.append({
                 "region": c.region,
                 "season": c.season,
                 "sowing_months": c.sowing_months or [],
                 "growth_months": c.growth_months or [],
                 "harvest_months": c.harvest_months or [],
                 "source_document": c.source_document
             })
        return {"crop": crop_name, "windows": res}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_medium)

async def get_crop_stage(db: Session, crop_name: str, month: int = None) -> Dict[str, Any]:
    m = month if month is not None else get_current_month_ist()
    key = f"crop:stage:{crop_name}:{m}"
    
    def fetch():
        cals = get_crop_calendar_windows(db, crop_name)
        possible_stages = []
        
        for c in cals:
            stage = determine_stage(m, c.sowing_months, c.growth_months, c.harvest_months)
            if stage:
                possible_stages.append({
                    "region": c.region,
                    "season": c.season,
                    "stage": stage
                })
        
        best_guess = "Unknown"
        if possible_stages:
            # Most common stage
            stages = [s["stage"] for s in possible_stages]
            best_guess = max(set(stages), key=stages.count)
            
        return {
            "crop": crop_name,
            "month": m,
            "month_name": month_int_to_name(m),
            "possible_stages": possible_stages,
            "best_guess": best_guess
        }
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_medium)

# --- TIER 5: DECISION SUPPORT APIS ---
async def compare_crops(db: Session, crops: List[str], state: str, month: int = None) -> Dict[str, Any]:
    crops_str = "-".join(sorted(crops))
    m = month if month is not None else get_current_month_ist()
    key = f"crop:compare:{crops_str}:{state}:{m}"
    
    def fetch():
        alias_map = build_alias_map_from_db(db)
        canonical_state = normalize_state_token(state, alias_map)
        
        comparison = []
        season, _ = month_to_season(m)
        
        for crop_name in crops:
            # 1. Varieties in state
            v_all = get_varieties_for_crop_in_state(db, crop_name, canonical_state)
            
            # 2. Max yield
            top_yield = 0.0
            best_var = None
            for v in v_all:
                try:
                    y = float(v.yield_max_q_per_ha)
                    if y > top_yield:
                        top_yield = y
                        best_var = v.name
                except:
                     pass
                     
            # 3. Sowing Window open?
            sowing_open = False
            cals = get_crop_calendar_windows(db, crop_name)
            for c in cals:
                if c.sowing_months and m in c.sowing_months:
                     sowing_open = True
                     break
                     
            comparison.append({
                "crop_name": crop_name,
                "varieties_available_count": len(v_all),
                "max_yield_variety": best_var,
                "max_yield_value": top_yield,
                "sowing_window_open_now": sowing_open,
                "season_match": season
            })
            
        return {"state": canonical_state, "month": m, "comparison": comparison}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_short)

async def get_crop_types_stats(db: Session, crop_name: str, state: str) -> Dict[str, Any]:
    key = f"crop:types:{crop_name}:{state}"
    def fetch():
        alias_map = build_alias_map_from_db(db)
        canonical_state = normalize_state_token(state, alias_map)
        
        v_all = get_varieties_for_crop_in_state(db, crop_name, canonical_state, 500)
        
        v_dicts = []
        for v in v_all:
             d = v.__dict__.copy()
             d.pop('_sa_instance_state', None)
             d["type"] = d.get("variety_type")
             d["yield_max"] = d.get("yield_max_q_per_ha")
             v_dicts.append(d)
             
        stats = calculate_crop_stats(v_dicts)
        return {"crop": crop_name, "state": canonical_state, "types": stats}
    return await get_or_set_cache(key, fetch, settings.crop_cache_ttl_medium)
