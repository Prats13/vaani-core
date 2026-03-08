import json
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from core.config import settings
from app.core.cache_service import redis_client
from app.weather.services.geocode_service import resolve_pincode
from app.weather.services.weather_features_service import get_weather_features_for_pincode
from app.crop.services.crop_query_service import get_candidate_crops_for_state_season, get_crop_calendar_windows, get_varieties_for_crop_in_state
from app.crop.utils.state_normalization import build_alias_map_from_db, normalize_state_token
from app.crop.utils.crop_time_utils import get_current_month_ist, month_int_to_name, month_to_season, determine_stage

logger = logging.getLogger(__name__)

async def _get_weather_features(db: Session, pincode: str, days_future: int, force_refresh: bool) -> Dict[str, Any]:
    """Helper to call existing weather v2 and handle caching if force_refresh."""
    return await get_weather_features_for_pincode(
        db=db,
        pincode=pincode,
        days_past=0,  # We only care about future for decisions
        days_future=days_future,
        include_hourly=False,
        force_refresh=force_refresh
    )

async def get_crop_suitability(db: Session, pincode: str, month: int = None, days_future: int = 16, limit_crops: int = 25, limit_varieties: int = 5, force_refresh: bool = False) -> Dict[str, Any]:
    m = month if month is not None else get_current_month_ist()
    key = f"crop:suitability:{pincode}:{m}:{days_future}:{limit_crops}:{limit_varieties}"
    
    if not force_refresh:
        try:
            cached = await redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"CROP INTELLIGENCE | REDIS GET ERROR: {e}")

    # 1. Resolve State
    loc = await resolve_pincode(db, pincode)
    alias_map = build_alias_map_from_db(db)
    canonical_state = normalize_state_token(loc.state, alias_map)

    # 2. Get Weather Risks
    weather = await _get_weather_features(db, pincode, days_future, force_refresh)
    heavy_rain_risk = weather.get("is_storm_heavy_rain_risk", False)
    heat_stress = weather.get("is_heat_stress_risk", False)
    dry_spell = weather.get("is_prolonged_dry_spell", False)

    # 3. Fetch candidate crops
    season, _ = month_to_season(m)
    crops = get_candidate_crops_for_state_season(db, canonical_state, season=None, month=m)
    if not crops:
        crops = get_candidate_crops_for_state_season(db, canonical_state, season=season)

    # 4. Score
    recommended = []
    avoid = []
    
    for c in crops[:limit_crops]:
        score = 0
        reasons = []
        reasons_negative = []
        
        # Determine if window is open
        sowing_window = False
        cals = get_crop_calendar_windows(db, c.crop_name)
        for cal in cals:
            if cal.sowing_months and m in cal.sowing_months:
                 sowing_window = True
                 break
        
        if sowing_window:
             score += 5
             reasons.append("Optimal Sowing Window Open.")
             
             if heavy_rain_risk:
                 score -= 3
                 reasons_negative.append("High heavy rain risk during early delicate sowing phase.")
             if heat_stress:
                 score -= 2
                 reasons_negative.append("Heat stress risk could affect seedling germination.")
        else:
             score -= 2
             reasons_negative.append("Not the ideal sowing month.")

        is_recommended = score >= 3
        
        # Attach top varieties if recommended
        top_vars = []
        if is_recommended:
             v_all = get_varieties_for_crop_in_state(db, c.crop_name, canonical_state, limit=limit_varieties)
             top_vars = [{"name": v.name, "yield_range": f"{v.yield_min_q_per_ha}-{v.yield_max_q_per_ha}"} for v in v_all]

        payload = {
            "crop_name": c.crop_name,
            "score": score,
            "pros": reasons,
            "cons": reasons_negative
        }
        
        if is_recommended:
            payload["recommended_varieties"] = top_vars
            recommended.append(payload)
        else:
            avoid.append(payload)

    # Sort
    recommended.sort(key=lambda x: x["score"], reverse=True)
    avoid.sort(key=lambda x: x["score"])

    final_payload = {
        "pincode": pincode,
        "state": canonical_state,
        "month": m,
        "weather_summary": {
            "heavy_rain_risk": heavy_rain_risk,
            "heat_stress": heat_stress,
            "dry_spell": dry_spell
        },
        "recommendations": recommended,
        "avoid": avoid
    }
    
    try:
         await redis_client.setex(key, settings.crop_cache_ttl_weather, json.dumps(final_payload))
    except:
         pass
         
    return final_payload

async def get_crop_risk(db: Session, pincode: str, crop_name: str, month: int = None, days_future: int = 16) -> Dict[str, Any]:
    # Simplified version, no caching decorator here to match suitbility style
    m = month if month is not None else get_current_month_ist()
    
    # 1. Base Resolution
    loc = await resolve_pincode(db, pincode)
    weather = await _get_weather_features(db, pincode, days_future, False)
    
    # 2. Stage
    cals = get_crop_calendar_windows(db, crop_name)
    best_guess = "Unknown"
    if cals:
        stages = []
        for c in cals:
             s = determine_stage(m, c.sowing_months, c.growth_months, c.harvest_months)
             if s: stages.append(s)
        if stages: best_guess = max(set(stages), key=stages.count)

    # 3. Map risks
    risks = []
    actions = []
    
    if weather.get("is_storm_heavy_rain_risk"):
        risks.append("Storm/Heavy Rain Expected")
        if best_guess == "Harvest":
            actions.append("Prioritize early harvesting to prevent crop damage.")
        elif best_guess == "Sowing":
            actions.append("Delay new sowing until heavy rains subside to prevent seed wash-off.")
        else:
            actions.append("Ensure proper drainage to prevent waterlogging.")
            
    if weather.get("is_heat_stress_risk"):
        risks.append("Heat Stress Risk")
        actions.append("Consider supplementary irrigation during cooler parts of the day.")
        
    if weather.get("is_prolonged_dry_spell"):
        risks.append("Dry Spell")
        actions.append("Optimize water usage. Postpone fertilizer applications until soil moisture improves.")
        
    if not weather.get("is_storm_heavy_rain_risk") and not weather.get("is_prolonged_dry_spell"):
         actions.append("Ideal conditions for spraying operations (fertilizers/pesticides).")

    return {
        "pincode": pincode,
        "crop": crop_name,
        "stage": best_guess,
        "month_name": month_int_to_name(m),
        "risks_identified": risks if risks else ["No major immediate weather risks identified."],
        "suggested_actions": actions
    }

async def get_sowing_window(db: Session, pincode: str, month: int = None, days_future: int = 16, limit_crops: int = 25) -> Dict[str, Any]:
    m = month if month is not None else get_current_month_ist()
    
    loc = await resolve_pincode(db, pincode)
    alias_map = build_alias_map_from_db(db)
    canonical_state = normalize_state_token(loc.state, alias_map)

    weather = await _get_weather_features(db, pincode, days_future, False)
    
    season, _ = month_to_season(m)
    crops = get_candidate_crops_for_state_season(db, canonical_state, season=None, month=m)
    
    suggested = []
    
    for c in crops[:limit_crops]:
        sowing_window = False
        cals = get_crop_calendar_windows(db, c.crop_name)
        for cal in cals:
            if cal.sowing_months and m in cal.sowing_months:
                 sowing_window = True
                 break
                 
        if not sowing_window:
             continue
             
        # simplistic window approach
        if weather.get("is_storm_heavy_rain_risk"):
            confidence = "Low"
            why = "Heavy rain expected in the forecast. Delay sowing."
        elif weather.get("is_prolonged_dry_spell"):
            confidence = "Medium"
            why = "Dry spell ahead. Ensure pre-sowing irrigation is available."
        else:
            confidence = "High"
            why = "Clear weather window, optimal temperatures, minimal rain disruptions."
            
        suggested.append({
            "crop_name": c.crop_name,
            "window": f"Next {days_future} Days",
            "confidence": confidence,
            "why": why
        })
        
    return {
        "pincode": pincode,
        "state": canonical_state,
        "month_evaluated": m,
        "sowing_windows": suggested
    }
