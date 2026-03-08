import logging
from uuid import UUID
from datetime import date
from typing import Optional

from sqlalchemy import create_engine, Column, String, Float, Boolean, Date, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from core.config import settings

logger = logging.getLogger("vaani")

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Farmer(Base):
    __tablename__ = "farmers"
    __table_args__ = {"schema": "farmer"}

    farmer_id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    phone_number = Column(String(15), unique=True, nullable=False)
    name = Column(String(255))
    state = Column(String(100))
    district = Column(String(100))
    village = Column(String(100))
    pincode = Column(String(10))
    land_area_acres = Column(Float)
    irrigation_type = Column(String(50))
    preferred_language = Column(String(50))
    is_profile_complete = Column(Boolean, default=False)


class FarmerCrop(Base):
    __tablename__ = "farmer_crops"
    __table_args__ = {"schema": "farmer"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    farmer_id = Column(PGUUID(as_uuid=True), ForeignKey("farmer.farmers.farmer_id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(255), nullable=False)
    sowing_date = Column(Date)
    area_acres = Column(Float)
    is_active = Column(Boolean, default=True)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_farmer_by_phone(db: Session, phone_number: str) -> Optional[Farmer]:
    return db.query(Farmer).filter(Farmer.phone_number == phone_number).first()


def get_farmer_by_id(db: Session, farmer_id: UUID) -> Optional[Farmer]:
    return db.query(Farmer).filter(Farmer.farmer_id == farmer_id).first()


def create_farmer(db: Session, phone_number: str, **kwargs) -> Farmer:
    farmer = Farmer(phone_number=phone_number, **kwargs)
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    logger.info(f"FARMER_DB | Created farmer: {farmer.farmer_id} | phone: {phone_number}")
    return farmer


def update_farmer(db: Session, farmer: Farmer, **kwargs) -> Farmer:
    for key, value in kwargs.items():
        if hasattr(farmer, key) and value is not None:
            setattr(farmer, key, value)
    db.commit()
    db.refresh(farmer)
    logger.info(f"FARMER_DB | Updated farmer: {farmer.farmer_id}")
    return farmer


def upsert_farmer(db: Session, phone_number: str, **kwargs) -> Farmer:
    farmer = get_farmer_by_phone(db, phone_number)
    if farmer:
        return update_farmer(db, farmer, **kwargs)
    return create_farmer(db, phone_number, **kwargs)


def get_farmer_crops(db: Session, farmer_id: UUID) -> list[FarmerCrop]:
    return db.query(FarmerCrop).filter(
        FarmerCrop.farmer_id == farmer_id,
        FarmerCrop.is_active == True
    ).all()


def add_farmer_crop(db: Session, farmer_id: UUID, crop_name: str, sowing_date: Optional[date] = None, area_acres: Optional[float] = None) -> FarmerCrop:
    crop = FarmerCrop(
        farmer_id=farmer_id,
        crop_name=crop_name,
        sowing_date=sowing_date,
        area_acres=area_acres
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)
    logger.info(f"FARMER_DB | Added crop '{crop_name}' for farmer: {farmer_id}")
    return crop
