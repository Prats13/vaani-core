from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, UniqueConstraint, Index, ForeignKey
from sqlalchemy.sql import func
from app.db import Base

class PincodeLocation(Base):
    __tablename__ = "pincode_location"

    pincode = Column(String, primary_key=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    state = Column(String)
    district = Column(String)
    timezone = Column(String, default="Asia/Kolkata")
    source = Column(String)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), onupdate=func.now(), server_default=func.now())

class WeatherDaily(Base):
    __tablename__ = "weather_daily"

    id = Column(Integer, primary_key=True, index=True)
    pincode = Column(String, ForeignKey("pincode_location.pincode"), nullable=False)
    provider = Column(String, nullable=False)
    date_local = Column(String, nullable=False)  # Storing as string 'YYYY-MM-DD'
    temperature_max = Column(Float)
    temperature_min = Column(Float)
    precipitation_sum = Column(Float)
    rain_sum = Column(Float)
    showers_sum = Column(Float)
    precip_probability_max = Column(Float)
    wind_max = Column(Float)
    gust_max = Column(Float)
    is_heavy_rain = Column(Boolean, default=False)
    ingested_at = Column(DateTime(timezone=False), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('pincode', 'provider', 'date_local', name='uq_weather_daily_pincode_provider_date'),
    )

class WeatherHourly(Base):
    __tablename__ = "weather_hourly"

    id = Column(Integer, primary_key=True, index=True)
    pincode = Column(String, ForeignKey("pincode_location.pincode"), nullable=False)
    provider = Column(String, nullable=False)
    ts_utc = Column(DateTime(timezone=False), nullable=False)
    temperature_c = Column(Float)
    precip_mm = Column(Float)
    rh_pct = Column(Float)
    wind_kmh = Column(Float)
    ingested_at = Column(DateTime(timezone=False), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('pincode', 'provider', 'ts_utc', name='uq_weather_hourly_pincode_provider_ts'),
        Index('idx_weather_hourly_pincode_ts', 'pincode', 'ts_utc'),
    )

class WeatherCoverage(Base):
    __tablename__ = "weather_coverage"

    pincode = Column(String, ForeignKey("pincode_location.pincode"), primary_key=True)
    provider = Column(String, primary_key=True)
    min_ts_utc = Column(DateTime(timezone=False))
    max_ts_utc = Column(DateTime(timezone=False))
    last_refresh_at = Column(DateTime(timezone=False))
    last_success_at = Column(DateTime(timezone=False))
    updated_at = Column(DateTime(timezone=False), onupdate=func.now(), server_default=func.now())

from pydantic import BaseModel
from typing import List, Dict, Any

class WeatherResponse(BaseModel):
    pincode: str
    lat: float
    lon: float
    timezone: str
    daily: List[Dict[str, Any]]
    heavy_rain_days: List[str]
    hourly: Dict[str, List[Dict[str, Any]]]

