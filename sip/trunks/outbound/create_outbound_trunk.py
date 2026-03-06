import asyncio

from livekit import api
from livekit.protocol.sip import CreateSIPOutboundTrunkRequest, SIPOutboundTrunkInfo, SIPTransport

from sip.sip_config import (
OUTBOUND_TRUNK_NAME,
OUTBOUND_TRUNK_ADDRESS,
OUTBOUND_TRUNK_DESTINATION_COUNTRY,
OUTBOUND_TRUNK_NUMBERS,
)

from core.config import logger

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
      logger.debug(f"{root_folder} | {sub_file_path} | Created Outbound trunk '{trunk.name}' with ID: {trunk.sip_trunk_id}")
  except Exception as e:
      logger.error(f"{root_folder} | {sub_file_path} | Failed to create trunk: {e}")
      raise
  finally:
      await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(main())