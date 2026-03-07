import asyncio
import uuid
from dataclasses import dataclass
from typing import Optional, Dict

from livekit import api
from livekit.protocol.sip import CreateSIPParticipantRequest, SIPOutboundConfig, SIPHeaderOptions

from sip.sip_config import (
    OUTBOUND_TRUNK_ID,
    OUTBOUND_RINGING_TIMEOUT,
    SIP_HOSTNAME
)

from core.config import logger

root_folder = "SIP"
sub_file_path = "PARTICIPANTS"


@dataclass
class SIPParticipantResult:
    """Result of creating a SIP participant"""
    participant_id: str
    participant_identity: str
    room_name: str


async def create_sip_participant(
        sip_trunk_id: str,
        sip_call_to_number: str,
        sip_call_from_number: str,
        room_name: str,
        participant_name: str,
        participant_metadata: str,
        outbound_ringing_timeout,
        headers: Optional[Dict[str, str]] = None,
        participant_attributes: Optional[Dict[str, str]] = None
) -> SIPParticipantResult:
    """
    Create a LiveKit room and SIP participant to initiate an outbound call.

    Args:
        sip_trunk_id: Outbound trunk ID
        sip_call_to_number: Customer phone number (E.164)
        sip_call_from_number: Caller ID / exophone number
        room_name: LiveKit room name
        participant_name: Display name for the SIP participant
        participant_metadata: JSON metadata string
        outbound_ringing_timeout: Duration for ringing timeout
        headers: Optional custom SIP headers
        participant_attributes: Optional key-value attributes attached to the participant

    Returns:
        SIPParticipantResult with participant_id, identity, and room_name
    """
    livekit_api = api.LiveKitAPI()
    try:
        # Build From header number (Exotel validates this against registered trunk number)
        # Must use 0-prefix local format (e.g. 08048332547), NOT E.164 (+918048332547)
        from_number = sip_call_from_number.replace("+91", "0")

        # Exotel requires From header domain = account_sid.pstn.exotel.com
        # Per LiveKit proto: SIPOutboundConfig.hostname controls the From domain.
        # We pass it via trunk=SIPOutboundConfig(hostname=SIP_HOSTNAME)
        trunk_override = SIPOutboundConfig(hostname=SIP_HOSTNAME) if SIP_HOSTNAME else None

        request = CreateSIPParticipantRequest(
            sip_trunk_id=sip_trunk_id,
            sip_call_to=sip_call_to_number,
            sip_number=from_number,
            trunk=trunk_override,
            room_name=room_name,
            participant_identity=f"sip_participant_{sip_call_to_number}",
            participant_name=participant_name,
            participant_metadata=participant_metadata,
            participant_attributes=participant_attributes or {},
            krisp_enabled=True,
            wait_until_answered=False,
            ringing_timeout=outbound_ringing_timeout,
            headers=headers or {},
            include_headers=SIPHeaderOptions.SIP_ALL_HEADERS
        )

        participant = await livekit_api.sip.create_sip_participant(request)
        logger.debug(
            f"{room_name} | {root_folder} | {sub_file_path} | "
            f"Created SIP Participant - {participant.participant_identity} with ID - {participant.participant_id}"
        )

        return SIPParticipantResult(
            participant_id=participant.participant_id,
            participant_identity=participant.participant_identity,
            room_name=room_name,
        )

    except Exception as e:
        logger.error(f"{room_name} | {root_folder} | {sub_file_path} | Error creating SIP Participant: {e}")
        raise
    finally:
        await livekit_api.aclose()


async def create_outbound_sip_participant(
        customer_name: str,
        customer_phone_number: str,
        customer_metadata: str,
        sip_call_from_number: str,
        headers: Optional[Dict[str, str]] = None,
        participant_attributes: Optional[Dict[str, str]] = None,
        room_name: str = ""
) -> SIPParticipantResult:
    """
    Create outbound SIP participant for calling a customer.
    Uses configured OUTBOUND_TRUNK_ID and OUTBOUND_RINGING_TIMEOUT.

    Args:
        customer_name: Display name for the participant
        customer_phone_number: Customer phone number (E.164)
        customer_metadata: JSON metadata string
        sip_call_from_number: Caller ID / exophone number (E.164) — passed by the caller, not read from env
        headers: Optional custom SIP headers
        participant_attributes: Optional key-value attributes attached to the participant
        room_name: Optional pre-generated room name (auto-generated if not provided)

    Returns:
        SIPParticipantResult with participant_id, identity, and room_name
    """
    unique_id = str(uuid.uuid4())[:8]
    room_name = room_name or f"outbound_{customer_phone_number}_{unique_id}"

    return await create_sip_participant(
        sip_trunk_id=OUTBOUND_TRUNK_ID,
        sip_call_to_number=customer_phone_number,
        sip_call_from_number=sip_call_from_number,
        room_name=room_name,
        participant_name=customer_name,
        participant_metadata=customer_metadata,
        outbound_ringing_timeout=OUTBOUND_RINGING_TIMEOUT,
        headers=headers,
        participant_attributes=participant_attributes
    )
