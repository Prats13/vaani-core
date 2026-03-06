import asyncio

from livekit import api
from livekit.protocol.sip import SIPHeaderOptions

from core.config import c_log
from sip.sip_config import (
    INBOUND_TRUNK_NAME,
    INBOUND_ALLOWED_NUMBERS,
    INBOUND_ALLOWED_ADDRESSES,
    INBOUND_HEADERS_TO_ATTRIBUTES,
    INBOUND_RINGING_TIMEOUT,
    INBOUND_MAX_CALL_DURATION
)

root_folder = "SIP"
sub_file_path = "TRUNKS | INBOUND"

async def main():
    livekit_api = api.LiveKitAPI()

    trunk = api.SIPInboundTrunkInfo(
        name=INBOUND_TRUNK_NAME,
        numbers=INBOUND_ALLOWED_NUMBERS,
        allowed_addresses=INBOUND_ALLOWED_ADDRESSES,
        headers_to_attributes=INBOUND_HEADERS_TO_ATTRIBUTES,
        include_headers=SIPHeaderOptions.SIP_ALL_HEADERS,
        ringing_timeout=INBOUND_RINGING_TIMEOUT,
        max_call_duration=INBOUND_MAX_CALL_DURATION,
        krisp_enabled=True,
    )

    request = api.CreateSIPInboundTrunkRequest(trunk=trunk)

    try:
        trunk = await livekit_api.sip.create_inbound_trunk(request)
        c_log.debug("-", "-", "-", root_folder, sub_file_path,
                   "CREATE_SIP_INBOUND_TRUNK",
                   f"Created Inbound trunk '{trunk.name}' with ID: {trunk.sip_trunk_id}",
                   "SUCCESS")
    except Exception as e:
        c_log.error("-", "-", "-", root_folder, sub_file_path,
                   "CREATE_SIP_INBOUND_TRUNK",
                   f"Failed to create trunk: {str(e)}",
                   "ERROR")
        raise
    finally:
        await livekit_api.aclose()

if __name__ == "__main__":
    asyncio.run(main())