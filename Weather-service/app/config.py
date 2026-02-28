from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://maheshdasika:pass@localhost:5432/weather"
    REDIS_URL: str = "redis://localhost:6379"
    OPEN_METEO_BASE: str = "https://api.open-meteo.com/v1/forecast"
    PINCODE_API_BASE: str = "http://api.zippopotam.us/in"
    FORECAST_REFRESH_TTL_HOURS: int = 3
    CACHE_TTL_SECONDS: int = 1800

    class Config:
        env_file = ".env"
        extra = "ignore"
settings = Settings()
