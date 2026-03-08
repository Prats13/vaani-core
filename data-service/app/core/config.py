from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://maheshdasika:pass@localhost:5432/VAANI"
    REDIS_URL: str = "redis://localhost:6379"
    OPEN_METEO_BASE: str = "https://api.open-meteo.com/v1/forecast"
    PINCODE_API_BASE: str = "http://api.zippopotam.us/in"
    FORECAST_REFRESH_TTL_HOURS: int = 3
    CACHE_TTL_SECONDS: int = 1800
    
    # Crop API Cache TTLs (in seconds)
    CROP_CACHE_TTL_LONG: int = 604800   # 7 days for /states
    CROP_CACHE_TTL_MEDIUM: int = 86400  # 24h for /crops
    CROP_CACHE_TTL_SHORT: int = 43200   # 12h for /varieties, /crops/state
    CROP_CACHE_TTL_SEARCH: int = 21600  # 6h for /search
    CROP_CACHE_TTL_WEATHER: int = 10800 # 3h for /crop/suitability (weather dependent)
    
    # Mandi API Config
    DATA_GOV_API_KEY: str = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
    MANDI_CACHE_TTL_V1: int = 10800      # 3 hours for raw v1
    MANDI_CACHE_TTL_V2: int = 21600      # 6 hours for insights v2


    class Config:
        env_file = ".env"
        extra = "ignore"
settings = Settings()
