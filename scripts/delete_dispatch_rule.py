import asyncio
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from livekit import api
from livekit.protocol.sip import DeleteSIPDispatchRuleRequest
from core.config import settings
from scripts.list_dispatch_rules import list_dispatch_rules



async def delete_dispatch_rule():
    """Delete SIP dispatch rule(s) - single rule by ID or all rules"""

    livekit_api = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret
    )

    try:
        # List all rules first
        rules = await list_dispatch_rules()

        if len(rules) == 0:
            print("\nNo dispatch rules found to delete")
            return

        # Get user input
        user_input = input("\nENTER DISPATCH RULE ID TO DELETE OR `*` TO DELETE ALL: ").strip()

        if user_input == "*":
            # Delete all rules
            confirm = input(f"\nAre you sure you want to delete ALL {len(rules)} dispatch rules? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Deletion cancelled")
                return

            print("\nDeleting all dispatch rules...")

            for rule in rules:
                try:
                    await livekit_api.sip.delete_dispatch_rule(
                        DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=rule.sip_dispatch_rule_id)
                    )
                    print(f"Deleted dispatch rule: {rule.sip_dispatch_rule_id} ({rule.name})")
                except Exception as e:
                    print(f"Failed to delete dispatch rule {rule.sip_dispatch_rule_id}: {str(e)}")

            print(f"\nDeletion complete")

        else:
            try:
                await livekit_api.sip.delete_dispatch_rule(
                    DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=user_input)
                )
                print(f"Deleted dispatch rule: {user_input}")
            except Exception as e:
                print(f"Failed to delete dispatch rule {user_input}: {str(e)}")

    except Exception as e:
        print(f"Error: {str(e)}")

    finally:
        await livekit_api.aclose()


async def main():
    """Main function"""
    await delete_dispatch_rule()


if __name__ == "__main__":
    asyncio.run(main())
