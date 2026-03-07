"""
Vaani SIP Telephony API Routes
===============================
FastAPI endpoints for outbound calling via LiveKit SIP.
"""
import json

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from core.config import settings, logger
from core.auth import verify_api_key
from core.livekit_manager import LiveKitManager
from sip.sip_config import OUTBOUND_TRUNK_ID, LIVEKIT_SIP_ENDPOINT
from sip.participants.create_sip_participant import create_outbound_sip_participant

root_folder = "API"
sub_file_path = "SIP_ROUTES"

router = APIRouter(prefix="/sip", tags=["SIP Telephony"])


# ============================================================================
# OUTBOUND CALL ENDPOINTS (via LiveKit SIP)
# ============================================================================

class AgentConfig(BaseModel):
    """Agent configuration for the outbound call"""
    agent_type: str = Field("farmer_advisory", description="Type of agent (farmer_advisory, farmer_onboarding)")
    stt_config: str = Field("sarvam-saarika-2.5", description="STT provider key")
    llm_config: str = Field("gemini-2.5-flash", description="LLM provider key")
    tts_config: str = Field("sarvam-bulbul", description="TTS provider key")


class CallConfig(BaseModel):
    """Call routing configuration"""
    call_direction: str = Field("outbound", description="Call direction")
    call_type: str = Field("pstn", description="Call type (pstn, sip)")
    call_provider: str = Field("exotel", description="SIP provider (exotel)")
    call_from: str = Field(..., description="Caller ID / exophone number (E.164)")
    call_to: str = Field(..., description="Farmer phone number to call (E.164)")


class OutboundCallRequest(BaseModel):
    """Request to make outbound call via LiveKit SIP"""
    agent_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Agent-specific parameters (farmer_name, farmer_phone, query context, etc.)"
    )
    agent_config: AgentConfig = Field(..., description="Agent configuration (agent_type, stt, llm, tts)")
    call_config: CallConfig = Field(..., description="Call routing configuration")


class OutboundCallResponse(BaseModel):
    """Outbound call response"""
    success: bool
    room_name: str
    farmer_phone: str
    sip_participant_id: Optional[str]
    status: str
    message: str


@router.get("/health")
async def sip_health_check():
    """Health check endpoint for SIP routes"""
    return {"status": "healthy", "service": "vaani-sip"}


@router.post(path="/call/outbound", response_model=OutboundCallResponse, status_code=status.HTTP_201_CREATED)
async def make_outbound_call(
        request: OutboundCallRequest,
        api_key: str = Depends(verify_api_key)
):
    """
    Make outbound call to a farmer via LiveKit SIP participant creation.
    Creates a LiveKit room and SIP participant to initiate the outbound call
    through the configured Exotel outbound trunk.

    Requires API key authentication via X-API-Key header.
    """
    try:
        # Validate outbound trunk is configured
        if not OUTBOUND_TRUNK_ID:
            raise ValueError("No Outbound Trunk configured. Create an outbound trunk first.")

        # Get farmer phone number from call_config
        farmer_phone = request.call_config.call_to
        if not farmer_phone.startswith('+'):
            farmer_phone = f"+91{farmer_phone.lstrip('0')}"

        agent_params = request.agent_params or {}
        agent_config = request.agent_config
        call_config = request.call_config

        exophone_number = call_config.call_from

        logger.debug(
            f"{root_folder} | {sub_file_path} | OUTBOUND_CALL | "
            f"Farmer: {farmer_phone}, From: {exophone_number}, Agent: {agent_config.agent_type}"
        )

        # participant_attributes: agent_config + call_config as flat key-value strings
        participant_attributes = {
            **{str(k): str(v) for k, v in agent_config.model_dump().items()},
            **{str(k): str(v) for k, v in call_config.model_dump().items()},
        }

        # participant_metadata: agent_params as JSON string
        participant_metadata = json.dumps(agent_params)

        # Prepare custom SIP headers
        headers = {}
        if exophone_number:
            headers["P-Asserted-Identity"] = f"<sip:{exophone_number}@{LIVEKIT_SIP_ENDPOINT}>"

        # Create SIP participant (creates room + initiates outbound call via trunk)
        result = await create_outbound_sip_participant(
            customer_name=agent_params.get("farmer_name", "Kisan"),
            customer_phone_number=farmer_phone,
            customer_metadata=participant_metadata,
            sip_call_from_number=exophone_number,
            headers=headers,
            participant_attributes=participant_attributes,
        )

        room_name = result.room_name
        sip_participant_id = result.participant_id

        logger.debug(
            f"{room_name} | {root_folder} | {sub_file_path} | OUTBOUND_CALL | "
            f"Call initiated, SIP participant: {sip_participant_id}"
        )

        return OutboundCallResponse(
            success=True,
            room_name=room_name,
            farmer_phone=farmer_phone,
            sip_participant_id=sip_participant_id,
            status="ringing",
            message=f"Outbound call initiated to {farmer_phone}",
        )

    except Exception as e:
        logger.error(f"{root_folder} | {sub_file_path} | OUTBOUND_CALL | ERROR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate outbound call: {str(e)}"
        )
