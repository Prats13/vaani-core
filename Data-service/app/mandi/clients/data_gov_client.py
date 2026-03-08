import httpx
import logging
import asyncio
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

# Base URL for Data.gov.in Agmarknet resource
DATA_GOV_API_BASE = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"

async def fetch_mandi_prices_from_data_gov(
    state: str,
    district: str = None,
    market: str = None,
    commodity: str = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """
    Fetch raw mandi prices from Data.gov.in API.
    Raises HTTPException (502) if upstream fails.
    """
    api_key = settings.DATA_GOV_API_KEY
    if not api_key or api_key == "dummy-key-if-not-provided":
        logger.warning("WEATHER SERVICE | No valid DATA_GOV_API_KEY is configured.")

    params = {
        "api-key": api_key,
        "format": "json",
        "filters[State]": state,
        "limit": limit,
        "offset": offset
    }

    if district:
        params["filters[District]"] = district
    if market:
        params["filters[Market]"] = market
    if commodity:
        params["filters[Commodity]"] = commodity

    logger.info(f"WEATHER SERVICE | Fetching data.gov.in Mandi API for State: {state}, Limit: {limit}")

    max_retries = 10
    retry_delay = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(DATA_GOV_API_BASE, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            # We may not want to retry aggressively on 401s or 400s, but data.gov.in 
            # often throws random 502/504 errors which DO benefit from retries.
            if e.response.status_code < 500:
                logger.error(f"WEATHER SERVICE | Data.gov API returned non-retriable HTTP {e.response.status_code}")
                raise HTTPException(status_code=502, detail="Upstream Mandi API error")
                
            if attempt == max_retries:
                logger.error(f"WEATHER SERVICE | Data.gov API failed after {max_retries} attempts: {e}")
                raise HTTPException(status_code=502, detail="Upstream Mandi API error")
                
            logger.warning(f"WEATHER SERVICE | Data.gov API HTTP Error {e.response.status_code}. Retrying in {retry_delay}s (Attempt {attempt}/{max_retries})...")
            await asyncio.sleep(retry_delay)
            
        except httpx.RequestError as e:
            if attempt == max_retries:
                logger.error(f"WEATHER SERVICE | Data.gov API request failed completely after {max_retries} attempts: {e}")
                raise HTTPException(status_code=502, detail="Could not connect to upstream Mandi API")
                
            logger.warning(f"WEATHER SERVICE | Data.gov API request failed: {e}. Retrying in {retry_delay}s (Attempt {attempt}/{max_retries})...")
            await asyncio.sleep(retry_delay)
            
        except Exception as e:
            logger.error(f"WEATHER SERVICE | Unexpected error calling Data.gov API: {e}")
            raise HTTPException(status_code=500, detail="Internal Service Error while fetching Mandi prices")
