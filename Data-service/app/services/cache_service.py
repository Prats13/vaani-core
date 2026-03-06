from app.core.cache_service import (
    redis_client, generate_cache_key,
    get_cached_weather, set_cached_weather,
    close_redis, get_cached_data, set_cached_data
)
