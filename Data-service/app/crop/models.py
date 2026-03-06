from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, MetaData, DateTime, Numeric
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import ARRAY, TEXT, UUID, JSONB
from sqlalchemy.sql import func
import uuid

crop_metadata = MetaData(schema="crop")
CropBase = declarative_base(metadata=crop_metadata)

class State(CropBase):
    __tablename__ = "states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_name = Column(String, unique=True, nullable=False)
    state_code = Column(String)
    aliases = Column(ARRAY(TEXT))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class Crop(CropBase):
    __tablename__ = "crops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_name = Column(String, nullable=False)
    crop_name_key = Column(String, unique=True, nullable=False)
    has_calendar = Column(Boolean, default=False)
    varieties_count = Column(Integer, default=0)
    metadata_col = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    calendars = relationship("CropCalendarWindow", back_populates="crop", lazy="noload")
    varieties = relationship("CropVariety", back_populates="crop", lazy="noload")

class CropCalendarWindow(CropBase):
    __tablename__ = "crop_calendar_windows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    region = Column(String)
    season = Column(String)
    window_label_raw = Column(String)
    source_document = Column(String)
    sowing_months = Column(ARRAY(TEXT))
    growth_months = Column(ARRAY(TEXT))
    harvest_months = Column(ARRAY(TEXT))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    crop = relationship("Crop", back_populates="calendars", lazy="noload")

class CropVariety(CropBase):
    __tablename__ = "crop_varieties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    variety_type = Column(String)
    name = Column(String, nullable=False)
    source = Column(String)
    year = Column(Integer)
    yield_min_q_per_ha = Column(Numeric)
    yield_max_q_per_ha = Column(Numeric)
    seed_rate_min_g_per_ha = Column(Numeric)
    seed_rate_max_g_per_ha = Column(Numeric)
    sowing_time_raw = Column(String)
    sowing_time_tags = Column(ARRAY(TEXT))
    states_raw = Column(String)
    raw_text = Column(String)
    page = Column(Integer)
    resistance_or_tolerance_lines = Column(ARRAY(TEXT))
    other_lines = Column(ARRAY(TEXT))
    extras = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    crop = relationship("Crop", back_populates="varieties", lazy="noload")

class VarietyState(CropBase):
    __tablename__ = "variety_states"

    variety_id = Column(UUID(as_uuid=True), ForeignKey("crop_varieties.id"), primary_key=True)
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), primary_key=True)
    source = Column(String)
