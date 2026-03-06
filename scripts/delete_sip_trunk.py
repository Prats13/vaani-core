import asyncio
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from livekit import api
from core.config import settings
from livekit.protocol.sip import DeleteSIPTrunkRequest, GetSIPInboundTrunkRequest, GetSIPOutboundTrunkRequest
from scripts.list_sip_trunk import list_trunks



async def delete_trunk():
    """Delete SIP trunk(s) - single trunk by ID or all trunks"""
    
    livekit_api = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret
    )
    
    try:
        # List all trunks first
        total_count, outbound_trunks, inbound_trunks = await list_trunks()
        
        if total_count == 0:
            print("\nNo trunks found to delete")
            return
        
        # Get user input
        user_input = input("\nENTER TRUNK ID TO DELETE OR `*` TO DELETE ALL: ").strip()
        
        if user_input == "*":
            # Delete all trunks
            confirm = input(f"\nAre you sure you want to delete ALL {total_count} trunks? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Deletion cancelled")
                return
            
            print("\nDeleting all trunks...")
            
            # Delete outbound trunks
            for trunk in outbound_trunks:
                try:
                    await livekit_api.sip.delete_sip_trunk(
                        DeleteSIPTrunkRequest(sip_trunk_id=trunk.sip_trunk_id)
                    )
                    print(f"Deleted outbound trunk: {trunk.sip_trunk_id} ({trunk.name})")
                except Exception as e:
                    print(f"Failed to delete outbound trunk {trunk.sip_trunk_id}: {str(e)}")
            
            # Delete inbound trunks
            for trunk in inbound_trunks:
                try:
                    await livekit_api.sip.delete_sip_trunk(
                        DeleteSIPTrunkRequest(sip_trunk_id=trunk.sip_trunk_id)
                    )
                    print(f"Deleted inbound trunk: {trunk.sip_trunk_id} ({trunk.name})")
                except Exception as e:
                    print(f"Failed to delete inbound trunk {trunk.sip_trunk_id}: {str(e)}")
            
            print(f"\nDeletion complete")
            
        else:
            try:
                deleted_trunk = await livekit_api.sip.delete_trunk(
                    DeleteSIPTrunkRequest(sip_trunk_id=user_input)
                )
                print(f"Deleted trunk: {deleted_trunk}")
            except Exception as e:
                print(f"Failed to delete trunk {user_input}: {str(e)}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        await livekit_api.aclose()


async def main():
    """Main function"""
    await delete_trunk()


if __name__ == "__main__":
    asyncio.run(main())
