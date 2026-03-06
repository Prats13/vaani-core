import json
import os
import re
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.dialects.postgresql import insert

# Config: Update DATABASE_URL or rely on env
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/VAANI"
)

def parse_range(value):
    if value is None:
        return None, None
    if isinstance(value, (int, float)):
        return float(value), float(value)
    if isinstance(value, list):
        nums = [float(v) for v in value if isinstance(v, (int, float))]
        if nums:
            return min(nums), max(nums)
        return None, None
    if isinstance(value, str):
        # Find all numbers in the string
        nums = [float(n) for n in re.findall(r"\d+\.?\d*", value)]
        if nums:
            return min(nums), max(nums)
    return None, None

def parse_sowing_time(sowing_time_raw):
    if not sowing_time_raw:
        return []
    # split on typical separators
    tokens = re.split(r'(?i)\band\b|,|-|/|&|;', sowing_time_raw)
    return [t.strip() for t in tokens if t.strip()]

def parse_states_raw(states_raw):
    if not states_raw:
        return []
    tokens = re.split(r'(?i)\band\b|,|;|/', states_raw)
    return [t.strip() for t in tokens if t.strip()]

def get_canonical_state(state_name, state_map):
    s = state_name.strip()
    if not s:
        return None
        
    s_lower = s.lower()
    
    # Check canonical names
    for canonical in state_map:
        if canonical.lower() == s_lower:
            return canonical
            
    # Check aliases
    for canonical, data in state_map.items():
        if s_lower in [a.lower() for a in data['aliases']]:
            return canonical
            
    return s # return as-is, will be upserted later

def main():
    json_path = os.getenv("CROP_JSON_PATH", "/Users/prajwalnayak/code/project/Vaani---The-Farmer-Buddy/merged_crop_calendar_and_varieties.json")
    
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found at {json_path}")
        return

    print("Loading JSON...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    engine = create_engine(DATABASE_URL)
    metadata = MetaData(schema="crop")
    
    # Reflect tables
    metadata.reflect(bind=engine)
    t_crops = metadata.tables['crop.crops']
    t_calendar = metadata.tables['crop.crop_calendar_windows']
    t_varieties = metadata.tables['crop.crop_varieties']
    t_states = metadata.tables['crop.states']
    t_variety_states = metadata.tables['crop.variety_states']
    
    counts = {
        "crops": 0,
        "calendars": 0,
        "varieties": 0,
        "variety_states": 0,
        "unknown_states": set()
    }
    
    with engine.begin() as conn:
        # Load existing states map
        states_records = conn.execute(t_states.select()).mappings().all()
        state_map = {row['state_name']: {'id': row['id'], 'aliases': row['aliases']} for row in states_records}
        
        crops_data = data.get("crops", [])
        
        for crop in crops_data:
            crop_name = crop.get("crop_name")
            crop_name_key = crop.get("crop_name_key")
            
            if not crop_name_key:
                continue
                
            # 1. Upsert Crop
            stmt = insert(t_crops).values(
                crop_name=crop_name,
                crop_name_key=crop_name_key,
                has_calendar=False, # will update at the end
                varieties_count=0
            ).on_conflict_do_update(
                index_elements=['crop_name_key'],
                set_={
                    "crop_name": crop_name
                }
            ).returning(t_crops.c.id)
            
            crop_id = conn.execute(stmt).scalar()
            counts["crops"] += 1
            
            # 2. Upsert Calendars
            has_calendar = False
            for cal in crop.get("calendar", []):
                stmt_cal = insert(t_calendar).values(
                    crop_id=crop_id,
                    region=cal.get("region"),
                    season=cal.get("season"),
                    window_label_raw=cal.get("window_label_raw"),
                    source_document=cal.get("source_reference", {}).get("document"),
                    sowing_months=cal.get("sowing_months", []),
                    growth_months=cal.get("growth_months", []),
                    harvest_months=cal.get("harvest_months", [])
                ).on_conflict_do_nothing() 
                # Doing do_nothing here because unique constraint has many coalesce constraints
                conn.execute(stmt_cal)
                counts["calendars"] += 1
                has_calendar = True
                
            # 3. Upsert Varieties
            var_count = 0
            for var in crop.get("varieties", []):
                y_min, y_max = parse_range(var.get("yield_q_per_ha"))
                sr_min, sr_max = parse_range(var.get("seed_rate_g_per_ha"))
                sowing_time = var.get("sowing_time")
                variety_type = var.get("type", "Variety")
                name = var.get("name")
                
                if not name:
                    continue
                    
                stmt_var = insert(t_varieties).values(
                    crop_id=crop_id,
                    variety_type=variety_type,
                    name=name,
                    source=var.get("source"),
                    year=var.get("year"),
                    yield_min_q_per_ha=y_min,
                    yield_max_q_per_ha=y_max,
                    seed_rate_min_g_per_ha=sr_min,
                    seed_rate_max_g_per_ha=sr_max,
                    sowing_time_raw=sowing_time,
                    sowing_time_tags=parse_sowing_time(sowing_time),
                    states_raw=var.get("states_raw"),
                    resistance_or_tolerance_lines=var.get("resistance_or_tolerance_lines", []),
                    other_lines=var.get("other_lines", []),
                    raw_text=var.get("raw_text"),
                    page=var.get("page"),
                    extras=var
                ).on_conflict_do_update(
                    constraint='uq_crop_varieties',
                    set_={
                        "yield_min_q_per_ha": y_min,
                        "yield_max_q_per_ha": y_max,
                        "seed_rate_min_g_per_ha": sr_min,
                        "seed_rate_max_g_per_ha": sr_max,
                        "extras": var
                    }
                ).returning(t_varieties.c.id)
                
                variety_id = conn.execute(stmt_var).scalar()
                
                # If there was a conflict, SQLAlchemy might not return the inserted ID with scalar() on some combinations,
                # let's fallback to select if variety_id is None
                if variety_id is None:
                    variety_id = conn.execute(
                        text("SELECT id FROM crop.crop_varieties WHERE crop_id = :cid AND variety_type = :vt AND name = :n AND source IS NOT DISTINCT FROM :s AND year IS NOT DISTINCT FROM :y"),
                        {"cid": crop_id, "vt": variety_type, "n": name, "s": var.get("source"), "y": var.get("year")}
                    ).scalar()
                    
                counts["varieties"] += 1
                var_count += 1
                
                # Link States
                states_list = var.get("states", [])
                if not states_list:
                    states_list = parse_states_raw(var.get("states_raw"))
                
                for s in states_list:
                    # Resolve to canonical
                    canonical = get_canonical_state(s, state_map)
                    if not canonical:
                        continue
                        
                    if canonical not in state_map:
                        counts["unknown_states"].add(canonical)
                        # Upsert unknown state
                        stmt_state = insert(t_states).values(
                            state_name=canonical,
                            aliases=[]
                        ).on_conflict_do_nothing().returning(t_states.c.id)
                        
                        s_id = conn.execute(stmt_state).scalar()
                        if not s_id: # fetch it
                            s_id = conn.execute(text("SELECT id FROM crop.states WHERE state_name = :n"), {"n": canonical}).scalar()
                            
                        state_map[canonical] = {'id': s_id, 'aliases': []}
                        
                    state_id = state_map[canonical]['id']
                    
                    # Link Variety to State
                    stmt_vs = insert(t_variety_states).values(
                        variety_id=variety_id,
                        state_id=state_id,
                        source='parsed'
                    ).on_conflict_do_nothing()
                    
                    res = conn.execute(stmt_vs)
                    if res.rowcount > 0:
                        counts["variety_states"] += 1
                        
            # Update Crop with aggregates
            conn.execute(
                t_crops.update().where(t_crops.c.id == crop_id).values(
                    has_calendar=has_calendar,
                    varieties_count=var_count
                )
            )

    print("\n--- Load Summary ---")
    print(f"Crops Upserted:           {counts['crops']}")
    print(f"Calendar Rows Upserted:   {counts['calendars']}")
    print(f"Varieties Upserted:       {counts['varieties']}")
    print(f"Variety-State Links:      {counts['variety_states']}")
    if counts["unknown_states"]:
        print("\nNotice: The following states were dynamically added (not in predefined list):")
        for u in counts["unknown_states"]:
            print(f"  - {u}")

if __name__ == "__main__":
    main()
