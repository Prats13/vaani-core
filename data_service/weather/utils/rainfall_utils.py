def is_heavy_rain_day(day: dict) -> bool:
    ps = day.get("precipitation_sum", 0)
    if ps is None:
        ps = 0
    pmax = day.get("precipitation_probability_max", 0)
    if pmax is None:
        pmax = 0
    rain = day.get("rain_sum", 0)
    if rain is None:
        rain = 0

    if ps >= 50:
        return True
    if ps >= 30 and pmax >= 70:
        return True
    if rain >= 30:
        return True
    return False
