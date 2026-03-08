"""
Vaani Advisory — Farmer Advisory Data Model
=============================================
Pydantic model that holds the farmer's profile and conversation state
throughout the advisory session. Loaded from RDS at session start,
updated by the orchestrator as conversation progresses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class FarmerAdvisoryData(BaseModel):
    """
    Session userdata for the farmer advisory agent.

    Pre-filled fields come from the call request (agent_params).
    RDS fields are loaded at session start from farmer_db.
    Conversation state fields are updated by the orchestrator during handoffs.
    """

    # -------------------------------------------------------------------------
    # From call request (pre-filled by outbound worker)
    # -------------------------------------------------------------------------
    farmer_phone: str = Field(..., description="Farmer's phone number in E.164 format")
    farmer_id: Optional[str] = Field(None, description="UUID from farmer.farmers table")

    # -------------------------------------------------------------------------
    # Loaded from RDS at session start (farmer_db.get_farmer_by_phone)
    # -------------------------------------------------------------------------
    name: Optional[str] = Field(None, description="Farmer's full name")
    state: Optional[str] = Field(None, description="Indian state where the farm is located")
    district: Optional[str] = Field(None, description="District within the state")
    pincode: Optional[str] = Field(None, description="Pincode for weather/crop lookups")
    preferred_language: Optional[str] = Field(None, description="Farmer's preferred language")
    primary_crops: Optional[List[str]] = Field(None, description="Crops the farmer grows")
    irrigation_type: Optional[str] = Field(None, description="irrigated / rainfed / mixed")
    is_registered: bool = Field(False, description="Whether farmer has completed onboarding")

    # -------------------------------------------------------------------------
    # Conversation state (updated by orchestrator during session)
    # -------------------------------------------------------------------------
    current_topic: Optional[str] = Field(
        None,
        description="Active specialist topic: weather | crop | mandi | schemes"
    )
    active_crop: Optional[str] = Field(
        None,
        description="Crop currently being discussed (set before handoff to crop/mandi agent)"
    )

    # -------------------------------------------------------------------------
    # Session channel (set at session start)
    # -------------------------------------------------------------------------
    is_web_session: bool = Field(
        False,
        description="True for browser/web sessions (enables CTA chat messages)"
    )
