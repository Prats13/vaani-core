import json
import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def generate_cache_key(pincode: str, from_ts: str, to_ts: str) -> str:
    return f"weather:{pincode}:{from_ts}:{to_ts}:v2"

async def get_cached_weather(key: str) -> dict:
    try:
        logger.info(f"WEATHER SERVICE | CACHE SERVICE | REDIS | GET | key: {key}")
        data = await redis_client.get(key)
        if data:
            logger.info(f"WEATHER SERVICE | CACHE SERVICE | REDIS | HIT SUCCESS | key: {key}")
            return json.loads(data)
        logger.info(f"WEATHER SERVICE | CACHE SERVICE | REDIS | MISS | key: {key}")
        return None
    except Exception as e:
        logger.error(f"WEATHER SERVICE | CACHE SERVICE | REDIS | ERROR | key: {key}: {e}")
        return None

async def set_cached_weather(key: str, data: dict):
    try:
        logger.info(f"WEATHER SERVICE | CACHE SERVICE | REDIS | SET | key: {key}")
        await redis_client.setex(
            key,
            settings.CACHE_TTL_SECONDS,
            json.dumps(data)
        )
        logger.info(f"WEATHER SERVICE | CACHE SERVICE | REDIS | SET SUCCESS | key: {key}")
    except Exception as e:
        logger.error(f"WEATHER SERVICE | CACHE SERVICE | REDIS | SET ERROR |  key: {key}: {e}")

async def close_redis():
    logger.info(f"WEATHER SERVICE | CACHE SERVICE | REDIS | CLOSING")
    await redis_client.close()
