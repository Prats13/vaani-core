from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, MetaData, JSON, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from sqlalchemy.sql import func

crop_metadata = MetaData(schema="crop")
CropBase = declarative_base(metadata=crop_metadata)

class State(CropBase):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True)
    state_name = Column(String, unique=True, nullable=False)
    state_code = Column(String)
    aliases = Column(ARRAY(TEXT))
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), onupdate=func.now(), server_default=func.now())
    
class Crop(CropBase):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True)
    crop_name = Column(String, nullable=False)
    crop_name_key = Column(String, unique=True, nullable=False)
    has_calendar = Column(Boolean, default=False)
    varieties_count = Column(Integer, default=0)
    metadata_col = Column("metadata", JSON)  # renaming attribute to metadata_col to avoid SqlAlchemy internal conflicts
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), onupdate=func.now(), server_default=func.now())

    # Relationships are optional as requested, but defined for ORM joins if needed
    calendars = relationship("CropCalendarWindow", back_populates="crop", lazy="noload")
    varieties = relationship("CropVariety", back_populates="crop", lazy="noload")

class CropCalendarWindow(CropBase):
    __tablename__ = "crop_calendar_windows"

    id = Column(Integer, primary_key=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    region = Column(String)
    season = Column(String)
    window_label_raw = Column(String)
    source_document = Column(String)
    sowing_months = Column(ARRAY(Integer))
    growth_months = Column(ARRAY(Integer))
    harvest_months = Column(ARRAY(Integer))
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), onupdate=func.now(), server_default=func.now())

    crop = relationship("Crop", back_populates="calendars", lazy="noload")

class CropVariety(CropBase):
    __tablename__ = "crop_varieties"

    id = Column(Integer, primary_key=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    variety_type = Column(String)
    name = Column(String, nullable=False)
    source = Column(String)
    year = Column(Integer)
    yield_min_q_per_ha = Column(Float)
    yield_max_q_per_ha = Column(Float)
    seed_rate_min_g_per_ha = Column(Float)
    seed_rate_max_g_per_ha = Column(Float)
    sowing_time = Column(String)
    states_raw = Column(String)
    raw_text = Column(String)
    page = Column(Integer)
    resistance_or_tolerance_lines = Column(ARRAY(TEXT))
    other_lines = Column(ARRAY(TEXT))
    extras = Column(JSON)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), onupdate=func.now(), server_default=func.now())

    crop = relationship("Crop", back_populates="varieties", lazy="noload")

class VarietyState(CropBase):
    __tablename__ = "variety_states"

    variety_id = Column(Integer, ForeignKey("crop_varieties.id"), primary_key=True)
    state_id = Column(Integer, ForeignKey("states.id"), primary_key=True)
    source = Column(String)
