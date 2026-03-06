import asyncio
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from livekit import api
from livekit.protocol.sip import ListSIPDispatchRuleRequest
from core.config import settings



async def list_dispatch_rules() -> list:
    """
    List all SIP dispatch rules

    Returns:
        list: dispatch rules list
    """
    livekit_api = api.LiveKitAPI(
        settings.livekit_url,
        settings.livekit_api_key,
        settings.livekit_api_secret
    )

    try:
        response = await livekit_api.sip.list_dispatch_rule(
            ListSIPDispatchRuleRequest()
        )
        rules = response.items

        print("\n" + "-"*60)
        print("SIP DISPATCH RULES")
        print("-"*60)
        if rules:
            for rule in rules:
                print(f"\nRule ID: {rule.sip_dispatch_rule_id}")
                print(f"  Name: {rule.name}")
                print(f"  Trunk IDs: {list(rule.trunk_ids)}")
                print(f"  Attributes: {dict(rule.attributes) if rule.attributes else '{}'}")
                if rule.rule:
                    dispatch = rule.rule
                    if hasattr(dispatch, 'dispatch_rule_callee') and dispatch.dispatch_rule_callee:
                        callee = dispatch.dispatch_rule_callee
                        print(f"  Room Prefix: {callee.room_prefix}")
                        print(f"  Randomize: {callee.randomize}")
                    elif hasattr(dispatch, 'dispatch_rule_direct') and dispatch.dispatch_rule_direct:
                        direct = dispatch.dispatch_rule_direct
                        print(f"  Room Name: {direct.room_name}")
                        print(f"  Pin: {direct.pin}")
        else:
            print("No dispatch rules found")

        print("\n" + "-"*60)
        print(f"TOTAL DISPATCH RULES: {len(rules)}")
        print("-"*60 + "\n")

        return list(rules)

    finally:
        await livekit_api.aclose()


async def main():
    """Main function"""
    await list_dispatch_rules()


if __name__ == "__main__":
    asyncio.run(main())
