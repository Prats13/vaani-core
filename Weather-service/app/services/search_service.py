from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.models_crop import Crop, CropVariety, State, VarietyState
from sqlalchemy import or_

async def execute_search(db: Session, q: str, state: str = None, limit: int = 25) -> Dict[str, Any]:
    """
    Perform a unified search across crops and varieties.
    TIER 6: Search logic
    """
    if not q or len(q.strip()) < 2:
        return {"crops": [], "varieties": []}
        
    search_term = f"%{q.strip()}%"
    
    # 1. Search crops
    crops_q = db.query(Crop).filter(
        or_(
            Crop.crop_name.ilike(search_term),
            Crop.crop_name_key.ilike(search_term)
        )
    ).limit(limit)
    
    crop_results = []
    for c in crops_q.all():
        crop_results.append({
            "id": c.id,
            "crop_name": c.crop_name,
            "crop_name_key": c.crop_name_key,
            "varieties_count": c.varieties_count
        })

    # 2. Search varieties
    var_q = db.query(CropVariety, Crop.crop_name).join(
        Crop, Crop.id == CropVariety.crop_id
    ).filter(
        CropVariety.name.ilike(search_term)
    )
    
    # Optional State Filter on varieties
    if state:
        state_obj = db.query(State).filter(State.state_name.ilike(f"%{state}%")).first()
        if state_obj:
            var_q = var_q.join(
                 VarietyState, VarietyState.variety_id == CropVariety.id
            ).filter(
                 VarietyState.state_id == state_obj.id
            )
            
    var_q = var_q.limit(limit)
    
    var_results = []
    for v, c_name in var_q.all():
        var_results.append({
            "id": v.id,
            "crop_name": c_name,
            "name": v.name,
            "type": v.variety_type,
            "year": v.year,
            "yield_range": [v.yield_min_q_per_ha, v.yield_max_q_per_ha]
        })

    return {
        "crops": crop_results,
        "varieties": var_results
    }
