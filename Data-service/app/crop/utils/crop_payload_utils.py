from typing import List, Dict, Any

def group_varieties_by_crop(varieties_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Groups a flat list of variety dictionaries by their crop_name.
    Used for endpoints that return crops with their nested top varieties.
    """
    grouped = {}
    for var in varieties_data:
        crop_id = var.get("crop_id")
        crop_name = var.get("crop_name")
        if not crop_name:
            continue
            
        if crop_name not in grouped:
            grouped[crop_name] = {
                "crop_id": crop_id,
                "crop_name": crop_name,
                "varieties": []
            }
            
        # exclude crop info from nested variety object to save space
        clean_var = {k: v for k, v in var.items() if k not in ("crop_id", "crop_name")}
        grouped[crop_name]["varieties"].append(clean_var)
        
    return list(grouped.values())

def find_top_yield_variety(varieties: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Finds the variety with the highest yield_max from a list."""
    if not varieties:
        return {}
    
    def yield_or_zero(v):
        try:
            val = float(v.get("yield_max") or 0.0)
            return val
        except (ValueError, TypeError):
            return 0.0

    top_v = max(varieties, key=yield_or_zero)
    return {
        "name": top_v.get("name"),
        "type": top_v.get("type"),
        "yield_max": top_v.get("yield_max"),
        "year": top_v.get("year")
    }

def format_variety_essential(var: Dict[str, Any], include_raw_text: bool = False) -> Dict[str, Any]:
    """Formats a variety into a compact essential representation."""
    essential = {
        "name": var.get("name"),
        "type": var.get("type"),
        "source": var.get("source"),
        "year": var.get("year"),
        "yield_range": [var.get("yield_min"), var.get("yield_max")],
        "seed_rate_range": [var.get("seed_rate_min"), var.get("seed_rate_max")],
        "sowing_time_tags": var.get("sowing_time_tags") or [],
        "resistance": var.get("resistance_or_tolerance_lines") or [],
        "states": var.get("states") or []
    }
    
    # Strip nulls to reduce json size
    essential = {k: v for k, v in essential.items() if v is not None and v != [None, None]}
    
    if include_raw_text and var.get("raw_text"):
        essential["raw_text"] = var.get("raw_text")
        
    # include other metadata for explainability if provided
    if "matched_snippets" in var:
        essential["matched_snippets"] = var["matched_snippets"]
        
    return essential

def calculate_crop_stats(varieties: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates aggregate stats for a list of varieties of a single crop."""
    by_type = {"Variety": {"count": 0, "max_yield": 0.0, "total_yield": 0.0, "yield_count": 0},
               "Hybrid": {"count": 0, "max_yield": 0.0, "total_yield": 0.0, "yield_count": 0}}
    
    for v in varieties:
        v_type = v.get("type", "Variety")
        if v_type not in by_type:
             by_type[v_type] = {"count": 0, "max_yield": 0.0, "total_yield": 0.0, "yield_count": 0}
             
        by_type[v_type]["count"] += 1
        
        y_max = v.get("yield_max")
        if y_max is not None:
             try:
                 val = float(y_max)
                 if val > by_type[v_type]["max_yield"]:
                     by_type[v_type]["max_yield"] = val
                 by_type[v_type]["total_yield"] += val
                 by_type[v_type]["yield_count"] += 1
             except (ValueError, TypeError):
                 pass
                 
    # Finalize stats
    res = {}
    for t, data in by_type.items():
        if data["count"] > 0:
            avg_yield = round(data["total_yield"] / data["yield_count"], 2) if data["yield_count"] > 0 else None
            res[t] = {
                "count": data["count"],
                "max_yield": data["max_yield"] if data["max_yield"] > 0 else None,
                "avg_yield": avg_yield
            }
    return res
