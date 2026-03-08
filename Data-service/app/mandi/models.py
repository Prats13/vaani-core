import json
from sqlalchemy import Column, String, Integer, DateTime, BigInteger, UniqueConstraint, Index, Date, JSON
from sqlalchemy.sql import func
from app.crop.models import CropBase

class ApiRawSnapshot(CropBase):
    __tablename__ = "api_raw_snapshots"

    id = Column(BigInteger, primary_key=True)
    provider = Column(String, default="data.gov.in")
    resource_id = Column(String)
    request_params = Column(JSON)
    response_payload = Column(JSON)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

class MandiPrice(CropBase):
    __tablename__ = "mandi_prices"

    id = Column(BigInteger, primary_key=True)
    arrival_date = Column(Date, nullable=False)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    market = Column(String, nullable=False)
    commodity = Column(String, nullable=False)
    variety = Column(String)
    grade = Column(String)
    commodity_code = Column(String)
    min_price = Column(Integer)
    max_price = Column(Integer)
    modal_price = Column(Integer)
    source = Column(String, default="data.gov.in")
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            'arrival_date', 'state', 'district', 'market', 'commodity', 'variety', 'grade',
            name='uq_mandi_prices_all_keys'
        ),
        Index('idx_mandi_prices_sdca_desc', 'state', 'district', 'commodity', 'arrival_date'),
        Index('idx_mandi_prices_sca_desc', 'state', 'commodity', 'arrival_date'),
        Index('idx_mandi_prices_mca_desc', 'market', 'commodity', 'arrival_date'),
    )
