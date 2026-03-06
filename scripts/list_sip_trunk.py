import asyncio
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from livekit import api
from livekit.protocol.sip import ListSIPOutboundTrunkRequest, ListSIPInboundTrunkRequest
from core.config import settings



async def list_trunks() -> tuple:
    """
    List all SIP trunks (inbound and outbound)
    
    Returns:
        tuple: (total_count, outbound_trunks_list, inbound_trunks_list)
    """
    livekit_api = api.LiveKitAPI(
        settings.livekit_url,
        settings.livekit_api_key,
        settings.livekit_api_secret
    )
    
    try:
        # List outbound trunks
        outbound_response = await livekit_api.sip.list_outbound_trunk(
            ListSIPOutboundTrunkRequest()
        )
        outbound_trunks = outbound_response.items
        
        print("\n" + "-"*60)
        print("OUTBOUND TRUNKS")
        print("-"*60)
        if outbound_trunks:
            for trunk in outbound_trunks:
                print(f"\nTrunk ID: {trunk.sip_trunk_id}")
                print(f"  Name: {trunk.name}")
                print(f"  Address: {trunk.address}")
                print(f"  Transport: {trunk.transport}")
                print(f"  Numbers: {list(trunk.numbers)}")
        else:
            print("No outbound trunks found")
        
        # List inbound trunks
        inbound_response = await livekit_api.sip.list_inbound_trunk(
            ListSIPInboundTrunkRequest()
        )
        inbound_trunks = inbound_response.items
        
        print("\n" + "-"*60)
        print("INBOUND TRUNKS")
        print("-"*60)
        if inbound_trunks:
            for trunk in inbound_trunks:
                print(f"\nTrunk ID: {trunk.sip_trunk_id}")
                print(f"  Name: {trunk.name}")
                print(f"  Numbers: {list(trunk.numbers)}")
        else:
            print("No inbound trunks found")
        
        total_trunks = len(outbound_trunks) + len(inbound_trunks)
        
        print("\n" + "-"*60)
        print(f"TOTAL TRUNKS: {total_trunks}")
        print("-"*60 + "\n")
        
        return total_trunks, list(outbound_trunks), list(inbound_trunks)
        
    finally:
        await livekit_api.aclose()


async def main():
    """Main function"""
    await list_trunks()


if __name__ == "__main__":
    asyncio.run(main())