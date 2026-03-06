import asyncio

from livekit import api
from livekit.protocol.sip import CreateSIPOutboundTrunkRequest, SIPOutboundTrunkInfo, SIPTransport

from sip.sip_config import (
OUTBOUND_TRUNK_NAME,
OUTBOUND_TRUNK_ADDRESS,
OUTBOUND_TRUNK_DESTINATION_COUNTRY,
OUTBOUND_TRUNK_NUMBERS,
)

from core.config import c_log

root_folder = "SIP | TRUNKS"
sub_file_path = "OUTBOUND"

async def main():
  lkapi = api.LiveKitAPI()

  trunk = SIPOutboundTrunkInfo(
    name = OUTBOUND_TRUNK_NAME,
    address = OUTBOUND_TRUNK_ADDRESS,
    destination_country=OUTBOUND_TRUNK_DESTINATION_COUNTRY,
    transport=SIPTransport.SIP_TRANSPORT_TCP,
    numbers = OUTBOUND_TRUNK_NUMBERS
  )

  request = CreateSIPOutboundTrunkRequest(
    trunk = trunk
  )

  try:
      trunk = await lkapi.sip.create_outbound_trunk(request)
      c_log.debug("-", "-", "-", root_folder, sub_file_path,
                  "CREATE_SIP_OUTBOUND_TRUNK",
                  f"Created Outbound trunk '{trunk.name}' with ID: {trunk.sip_trunk_id}",
                  "SUCCESS")
  except Exception as e:
      c_log.error("-", "-", "-", root_folder, sub_file_path,
                  "CREATE_SIP_OUTBOUND_TRUNK",
                  f"Failed to create trunk: {str(e)}",
                  "ERROR")
      raise
  finally:
      await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(main())