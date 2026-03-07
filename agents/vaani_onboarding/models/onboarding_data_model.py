from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class LandSizeUnit(str, Enum):
    ACRES = "acres"
    BIGHA = "bigha"
    HECTARE = "hectare"
    GUNTHA = "guntha"
    OTHER = "other"


class IrrigationType(str, Enum):
    IRRIGATED = "irrigated"
    RAINFED = "rainfed"
    MIXED = "mixed"


class PreferredLanguage(str, Enum):
    HINDI = "hindi"
    TELUGU = "telugu"
    KANNADA = "kannada"
    TAMIL = "tamil"
    BENGALI = "bengali"
    OTHER = "other"


class FarmerOnboardingData(BaseModel):
    # Pre-filled from call request
    farmer_id: str = Field(..., description="Unique farmer identifier")
    farmer_phone_number: str = Field(..., description="Farmer's phone number in E.164 format")

    # Collected during onboarding call
    farmer_name: Optional[str] = Field(None, description="Farmer's full name")

    # Location
    state: Optional[str] = Field(None, description="Indian state where the farm is located")
    district: Optional[str] = Field(None, description="District within the state")
    village: Optional[str] = Field(None, description="Village or town name")

    # Farm profile
    land_size: Optional[float] = Field(None, ge=0, description="Approximate farm size")
    land_size_unit: Optional[LandSizeUnit] = Field(None, description="Unit of land measurement")
    irrigation_type: Optional[IrrigationType] = Field(None, description="Primary irrigation method")

    # Crops
    primary_crops: Optional[List[str]] = Field(None, description="Crops the farmer regularly grows")
    current_season_crop: Optional[str] = Field(None, description="Crop currently in the field")

    # Language
    preferred_language: Optional[PreferredLanguage] = Field(None, description="Farmer's preferred language")

    def is_complete(self) -> bool:
        """Check if all required fields have been collected."""
        return all([
            self.farmer_name,
            self.state,
            self.district,
            self.primary_crops,
            self.preferred_language,
        ])

    def missing_fields(self) -> List[str]:
        """Return list of required fields not yet collected."""
        missing = []
        if not self.farmer_name: missing.append("farmer_name")
        if not self.state: missing.append("state")
        if not self.district: missing.append("district")
        if not self.primary_crops: missing.append("primary_crops")
        if not self.preferred_language: missing.append("preferred_language")
        return missing