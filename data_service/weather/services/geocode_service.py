import httpx
from sqlalchemy.orm import Session
from data_service.weather.models import PincodeLocation
from core.config import settings

async def resolve_pincode(db: Session, pincode: str) -> PincodeLocation:
    loc = db.query(PincodeLocation).filter(PincodeLocation.pincode == pincode).first()
    if loc:
        return loc
    
    import logging
    # Not found in DB, fetch from Zippopotam
    async with httpx.AsyncClient(timeout=10.0) as client:
        url = f"{settings.pincode_api_base}/{pincode}"
        logging.info(f"WEATHER SERVICE | PINCODE SERVICE | Fetching geocode for pincode: {pincode}")
        try:
            resp = await client.get(url)
        except httpx.TimeoutException as e:
            logging.error(f"WEATHER SERVICE | PINCODE SERVICE | TIMEOUT fetching geocode for pincode: {pincode} | error={e}")
            raise ValueError(f"Timeout fetching pincode: {pincode}")
        
        if resp.status_code != 200:
            logging.error(f"WEATHER SERVICE | PINCODE SERVICE | Invalid pincode or not found: {pincode}")
            raise ValueError(f"Invalid pincode or not found: {pincode}")
        data = resp.json()
        logging.info(f"WEATHER SERVICE | PINCODE SERVICE | Fetched geocode for pincode: {pincode}")
        
        place = data["places"][0]
        new_loc = PincodeLocation(
            pincode=pincode,
            lat=float(place["latitude"]),
            lon=float(place["longitude"]),
            state=place["state"],
            district=place.get("place name", ""),
            timezone="Asia/Kolkata",
            source="zippopotam"
        )
        db.add(new_loc)
        db.commit()
        db.refresh(new_loc)
        logging.info(f"WEATHER SERVICE | DB SERVICE | Added geocode for pincode: {pincode} to pincode_location table")
        return new_loc
