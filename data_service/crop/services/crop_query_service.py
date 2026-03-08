from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from data_service.crop.models import Crop, CropVariety, State, VarietyState, CropCalendarWindow
from sqlalchemy import select, and_, or_, String, cast, desc

def get_crops_paginated(db: Session, query_str: str = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Fetch crops with basic info."""
    q = db.query(Crop)
    if query_str:
        q = q.filter(
            or_(
                Crop.crop_name.ilike(f"%{query_str}%"),
                Crop.crop_name_key.ilike(f"%{query_str}%")
            )
        )
    q = q.order_by(Crop.crop_name).limit(limit).offset(offset)
    
    return [
        {
            "id": c.id,
            "crop_name": c.crop_name,
            "crop_name_key": c.crop_name_key,
            "has_calendar": c.has_calendar,
            "varieties_count": c.varieties_count
        } for c in q.all()
    ]

def get_states_with_aliases(db: Session) -> List[Dict[str, Any]]:
    """Fetch all canonical states and their aliases."""
    states = db.query(State).order_by(State.state_name).all()
    return [{"name": s.state_name, "aliases": s.aliases or []} for s in states]

def get_varieties_for_state_by_crop(db: Session, state_name: str, limit: int = None) -> List[Dict[str, Any]]:
    """
    Returns ALL varieties joined with Crop for a given state name.
    Used to build nested payloads later. N+1 safe.
    """
    # Find State.id
    state_obj = db.query(State).filter(State.state_name == state_name).first()
    if not state_obj:
        return []
        
    q = db.query(CropVariety, Crop.crop_name).join(
        VarietyState, VarietyState.variety_id == CropVariety.id
    ).join(
        Crop, Crop.id == CropVariety.crop_id
    ).filter(
        VarietyState.state_id == state_obj.id
    ).order_by(
        desc(CropVariety.yield_max_q_per_ha), desc(CropVariety.year)
    )
    
    if limit:
        q = q.limit(limit)
        
    results = q.all()
    return [
        {
            "id": v.id,
            "type": v.variety_type,
            "name": v.name,
            "source": v.source,
            "year": v.year,
            "yield_min": v.yield_min_q_per_ha,
            "yield_max": v.yield_max_q_per_ha,
            "seed_rate_min": v.seed_rate_min_g_per_ha,
            "seed_rate_max": v.seed_rate_max_g_per_ha,
            "sowing_time_tags": v.sowing_time_tags,
            "resistance_or_tolerance_lines": v.resistance_or_tolerance_lines,
            "other_lines": v.other_lines,
            "raw_text": v.raw_text,
            "crop_id": v.crop_id,
            "crop_name": crop_name
        } for (v, crop_name) in results
    ]

def get_varieties_for_crop_in_state(db: Session, crop_name_input: str, state_name: str, limit: int = 50) -> List[CropVariety]:
    """Fetch varieties specific to one crop in a specific state."""
    state_obj = db.query(State).filter(State.state_name == state_name).first()
    crop_obj = db.query(Crop).filter(Crop.crop_name.ilike(crop_name_input)).first()
    
    if not state_obj or not crop_obj:
        return []
        
    q = db.query(CropVariety).join(
        VarietyState, VarietyState.variety_id == CropVariety.id
    ).filter(
        VarietyState.state_id == state_obj.id,
        CropVariety.crop_id == crop_obj.id
    ).order_by(
         desc(CropVariety.yield_max_q_per_ha), desc(CropVariety.year)
    ).limit(limit)
    
    return q.all()

def find_resistant_varieties(db: Session, crop_name: str, state_name: str, disease: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Finds varieties resistant to a specific disease via keyword match."""
    state_obj = db.query(State).filter(State.state_name == state_name).first()
    crop_obj = db.query(Crop).filter(Crop.crop_name.ilike(crop_name)).first()
    
    if not state_obj or not crop_obj:
        return []

    # Using postgres Array to string casting and ILIKE on raw_text
    search_term = f"%{disease}%"
    
    q = db.query(CropVariety).join(
        VarietyState, VarietyState.variety_id == CropVariety.id
    ).filter(
        VarietyState.state_id == state_obj.id,
        CropVariety.crop_id == crop_obj.id,
        or_(
            cast(CropVariety.resistance_or_tolerance_lines, String).ilike(search_term),
            CropVariety.raw_text.ilike(search_term)
        )
    ).order_by(desc(CropVariety.yield_max_q_per_ha)).limit(limit)
    
    results = []
    for v in q.all():
        # Extractor for explainability
        lines = []
        if v.resistance_or_tolerance_lines:
            lines = [l for l in v.resistance_or_tolerance_lines if disease.lower() in l.lower()]
        if not lines and v.raw_text:
            # find surrounding text chunk
            lower_text = v.raw_text.lower()
            idx = lower_text.find(disease.lower())
            if idx != -1:
                start = max(0, idx - 40)
                end = min(len(v.raw_text), idx + 80)
                lines.append("..." + v.raw_text[start:end].replace('\n', ' ') + "...")
        results.append({
            "variety": v,
            "matched_snippets": lines
        })
    return results

def get_crop_calendar_windows(db: Session, crop_name: str) -> List[CropCalendarWindow]:
    """Fetch calendar windows for a given crop."""
    crop_obj = db.query(Crop).filter(Crop.crop_name.ilike(crop_name)).first()
    if not crop_obj:
        return []
        
    return db.query(CropCalendarWindow).filter(
        CropCalendarWindow.crop_id == crop_obj.id
    ).all()

def get_candidate_crops_for_state_season(db: Session, state_name: str, season: str, month: int = None) -> List[Crop]:
    """
    Finds crops viable in a state for a given season or month.
    Since 'season' metadata isn't always perfectly joined to 'state',
    we look for Crops that have at least one variety in the state, 
    and either calendar match or variety sowing tag match.
    """
    state_obj = db.query(State).filter(State.state_name == state_name).first()
    if not state_obj:
        return []

    # get all crops in state
    crops_in_state = db.query(Crop).join(
        CropVariety, CropVariety.crop_id == Crop.id
    ).join(
        VarietyState, VarietyState.variety_id == CropVariety.id
    ).filter(
        VarietyState.state_id == state_obj.id
    ).distinct().all()

    candidates = []
    
    for c in crops_in_state:
        # Check calendar first
        cals = get_crop_calendar_windows(db, c.crop_name)
        matched = False
        
        if cals and month:
             for cal in cals:
                 if cal.sowing_months and month in cal.sowing_months:
                     matched = True
                     break
        if cals and not matched and season:
             for cal in cals:
                 if cal.season and season.lower() in cal.season.lower():
                     matched = True
                     break
                     
        if not matched and c.varieties:
             # Check varieties if calendar didn't help
             v_q = db.query(CropVariety).join(
                 VarietyState, VarietyState.variety_id == CropVariety.id
             ).filter(
                 VarietyState.state_id == state_obj.id,
                 CropVariety.crop_id == c.id
             ).all()
             
             for v in v_q:
                 if v.sowing_time_tags:
                     for tag in v.sowing_time_tags:
                         if season and season.lower() in tag.lower():
                             matched = True
                             break
                             
        if matched:
             candidates.append(c)
             
    return candidates
