from datetime import date, timedelta

def safe_avg(values):
    valid_values = [v for v in values if v is not None]
    if not valid_values:
        return 0.0
    return round(sum(valid_values) / len(valid_values), 2)

def peak_with_date(rows, val_key, date_key, is_min=False):
    valid_rows = [r for r in rows if r.get(val_key) is not None]
    if not valid_rows:
        return {"value": 0.0, "date": None}
    if is_min:
        peak_row = min(valid_rows, key=lambda x: x[val_key])
    else:
        peak_row = max(valid_rows, key=lambda x: x[val_key])
    
    val = round(peak_row[val_key], 2)
    dt = peak_row[date_key]
    if hasattr(dt, "strftime"):
        dt = dt.strftime("%Y-%m-%d")
    return {"value": val, "date": dt}

def to_date(dt):
    if isinstance(dt, str):
        from datetime import datetime
        return datetime.strptime(dt[:10], "%Y-%m-%d").date()
    # Assume it's a date or datetime object
    if hasattr(dt, "date"):
        return dt.date()
    return dt

def date_to_str(dt):
    if dt is None:
        return None
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y-%m-%d")
    return str(dt)

def compute_features(daily_rows, heavy_rain_days, hourly_by_date, today_local, include_hourly):
    today = to_date(today_local)
    
    # We need all the date windows
    past_7d_start = today - timedelta(days=6) # [today-6, today] inclusive is 7 days
    next_7d_start = today + timedelta(days=1)
    next_7d_end = today + timedelta(days=7)
    next_16d_end = today + timedelta(days=16)

    past_7d_rows = []
    next_7d_rows = []
    next_16d_rows = []
    
    start_date = None
    end_date = None
    
    if daily_rows:
        start_date = date_to_str(daily_rows[0].get("date"))
        end_date = date_to_str(daily_rows[-1].get("date"))

    for row in daily_rows:
        r_date = to_date(row.get("date"))
        
        # past 7 days [today-6, today]
        if past_7d_start <= r_date <= today:
            past_7d_rows.append(row)
            
        # next 7 days [today+1, today+7]
        if next_7d_start <= r_date <= next_7d_end:
            next_7d_rows.append(row)
            
        # next 16 days [today+1, today+16]
        if next_7d_start <= r_date <= next_16d_end:
            next_16d_rows.append(row)

    # ----------------
    # Rainfall summary
    # ----------------
    def count_rain_days(rows):
        return sum(1 for r in rows if (r.get("precipitation_sum") or 0) > 0.1)

    def total_rain(rows):
        return round(sum((r.get("precipitation_sum") or 0) for r in rows), 2)

    past_7d_all_rain_dates = [r for r in past_7d_rows if (r.get("precipitation_sum") or 0) > 0.1]
    last_rain_date = date_to_str(max([r.get("date") for r in past_7d_all_rain_dates], default=None, key=to_date)) if past_7d_all_rain_dates else None

    next_7d_all_rain_dates = [r for r in next_7d_rows if (r.get("precipitation_sum") or 0) > 0.1]
    next_rain_date = date_to_str(min([r.get("date") for r in next_7d_all_rain_dates], default=None, key=to_date)) if next_7d_all_rain_dates else None

    past_7d_total = total_rain(past_7d_rows)
    next_7d_total = total_rain(next_7d_rows)

    rainfall_summary_mm = {
        "past_7d_total": past_7d_total,
        "past_7d_rain_days": count_rain_days(past_7d_rows),
        "last_rain_date": last_rain_date,
        "next_7d_total": next_7d_total,
        "next_7d_rain_days": count_rain_days(next_7d_rows),
        "next_rain_date": next_rain_date,
        "heavy_rain_days": [date_to_str(to_date(d)) for d in heavy_rain_days]
    }

    # ----------------
    # Temperature summary
    # ----------------
    next_7d_avg_max = safe_avg([r.get("temperature_max") for r in next_7d_rows])
    next_7d_avg_min = safe_avg([r.get("temperature_min") for r in next_7d_rows])
    next_7d_peak_max = peak_with_date(next_7d_rows, "temperature_max", "date", is_min=False)
    next_7d_low_min = peak_with_date(next_7d_rows, "temperature_min", "date", is_min=True)
    hot_days_max_ge_35_next_16d = sum(1 for r in next_16d_rows if (r.get("temperature_max") or 0.0) >= 35.0)

    temperature_summary_c = {
        "next_7d_avg_max": next_7d_avg_max,
        "next_7d_avg_min": next_7d_avg_min,
        "next_7d_peak_max": next_7d_peak_max,
        "next_7d_low_min": next_7d_low_min,
        "hot_days_max_ge_35_next_16d": hot_days_max_ge_35_next_16d
    }

    # ----------------
    # Wind summary
    # ----------------
    next_7d_peak_wind = peak_with_date(next_7d_rows, "wind_max", "date", is_min=False)
    next_16d_peak_wind = peak_with_date(next_16d_rows, "wind_max", "date", is_min=False)
    next_16d_peak_gust = peak_with_date(next_16d_rows, "gust_max", "date", is_min=False)
    windy_days_wind_ge_20_next_16d = sum(1 for r in next_16d_rows if (r.get("wind_max") or 0.0) >= 20.0)

    wind_summary_kmh = {
        "next_7d_peak_wind": next_7d_peak_wind,
        "next_16d_peak_wind": next_16d_peak_wind,
        "next_16d_peak_gust": next_16d_peak_gust,
        "windy_days_wind_ge_20_next_16d": windy_days_wind_ge_20_next_16d
    }

    # ----------------
    # Flags
    # ----------------
    dry_spell = past_7d_total < 5.0
    irrigation_needed = dry_spell and next_7d_total < 5.0
    
    storm_risk = len(heavy_rain_days) > 0 or any((r.get("precip_probability_max") or 0) >= 80 for r in next_7d_rows)
    high_wind_risk = (windy_days_wind_ge_20_next_16d > 0) or (next_16d_peak_gust["value"] >= 35.0)
    heat_stress_risk = hot_days_max_ge_35_next_16d > 0

    advisory_flags = {
        "dry_spell": dry_spell,
        "irrigation_needed_for_sowing": irrigation_needed,
        "storm_risk": storm_risk,
        "high_wind_risk": high_wind_risk,
        "heat_stress_risk": heat_stress_risk
    }

    # ----------------
    # Recommendations
    # ----------------
    
    # Prepare land
    prep_status = "OK"
    if storm_risk:
        prep_status = "WAIT"
    elif dry_spell:
        prep_status = "OK_WITH_IRRIGATION"
        
    prep_key_points = []
    if dry_spell:
        prep_key_points.append("Soil likely dry; consider pre-watering before ploughing.")
    if storm_risk:
        prep_key_points.append("Avoid land prep close to heavy rain; soil may become waterlogged.")
    if heat_stress_risk:
        prep_key_points.append("Do heavy work early morning/evening; midday heat is high.")
    if high_wind_risk:
        prep_key_points.append("Wind may dry topsoil; plan irrigation/moisture management.")
        
    # Sowing
    # If heavy rain exists in next 7 days -> WAIT
    heavy_rain_next_7d = [d for d in next_7d_rows if date_to_str(to_date(d.get("date"))) in rainfall_summary_mm["heavy_rain_days"]]
    
    sow_status = "SOW"
    sow_reasons = []
    
    if heavy_rain_next_7d:
        sow_status = "WAIT"
        sow_reasons.append("HEAVY_RAIN_EXPECTED")
    elif irrigation_needed:
        sow_status = "SOW_WITH_IRRIGATION"
        sow_reasons.append("NO_RAIN_FORECAST")
    else:
        sow_status = "SOW"
        if not storm_risk and not high_wind_risk and not heat_stress_risk:
            sow_reasons.append("TEMP_OK")
            sow_reasons.append("WIND_MODERATE")

    rec_start_date = None
    rec_end_date = None

    if sow_status == "WAIT":
        # choose window right after last heavy day (if exists) else next 3 days
        if heavy_rain_next_7d:
            # We already have next_7d_rows which are sorted. Just take max.
            last_heavy_date = max([to_date(r.get("date")) for r in heavy_rain_next_7d])
            rec_start_date = date_to_str(last_heavy_date + timedelta(days=1))
            rec_end_date = date_to_str(last_heavy_date + timedelta(days=3))
        else:
            rec_start_date = date_to_str(next_7d_start)
            rec_end_date = date_to_str(next_7d_start + timedelta(days=2))
    else:
        # earliest 3-day window from today+1 to today+3
        rec_start_date = date_to_str(next_7d_start)
        rec_end_date = date_to_str(next_7d_start + timedelta(days=2))

    if not sow_reasons and sow_status == "SOW":
        sow_reasons = ["TEMP_OK"]

    recommended_actions = {
        "prepare_land": {
            "status": prep_status,
            "key_points": prep_key_points
        },
        "sowing": {
            "status": sow_status,
            "recommended_window": {
                "start_date": rec_start_date,
                "end_date": rec_end_date,
                "reason_codes": sow_reasons
            }
        }
    }

    # ----------------
    # Final Result
    # ----------------
    result = {
        "window": {
            "start_date": start_date,
            "end_date": end_date,
            "today_date": date_to_str(today)
        },
        "rainfall_summary_mm": rainfall_summary_mm,
        "temperature_summary_c": temperature_summary_c,
        "wind_summary_kmh": wind_summary_kmh,
        "advisory_flags": advisory_flags,
        "recommended_actions": recommended_actions
    }
    
    if include_hourly:
        result["hourly_heavy_rain"] = hourly_by_date if hourly_by_date else {}
        
    return result
