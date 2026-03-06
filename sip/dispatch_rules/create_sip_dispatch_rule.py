import asyncio
from livekit import api
from sip.sip_config import (
    DISPATCH_RULE_ASSOCIATED_TRUNK_IDS,
    DISPATCH_RULE_NAME,
    DISPATCH_RULE_ATTRIBUTES,
    INBOUND_ROOM_EMPTY_TIMEOUT,
    INBOUND_ROOM_DEPARTURE_TIMEOUT,
    INBOUND_ROOM_MAX_PARTICIPANTS
)
from core.config import logger

root_folder = "SIP"
sub_file_path = "DISPATCH_RULES"

async def main():
  livekit_api = api.LiveKitAPI()

  rule = api.SIPDispatchRule(
      dispatch_rule_callee=api.SIPDispatchRuleCallee(
          room_prefix='inbound-',
          randomize=True,
      )
  )

  inbound_call_handler_agents = [api.RoomAgentDispatch(agent_name="vaani_inbound_agent")]

  room_config = api.RoomConfiguration(
      empty_timeout=INBOUND_ROOM_EMPTY_TIMEOUT,
      departure_timeout=INBOUND_ROOM_DEPARTURE_TIMEOUT,
      max_participants=INBOUND_ROOM_MAX_PARTICIPANTS,
      agents=inbound_call_handler_agents
  )

  request = api.CreateSIPDispatchRuleRequest(
    dispatch_rule = api.SIPDispatchRuleInfo(
      rule = rule,
      trunk_ids=DISPATCH_RULE_ASSOCIATED_TRUNK_IDS,
      name = DISPATCH_RULE_NAME,
      attributes=DISPATCH_RULE_ATTRIBUTES,
      room_config=room_config
    )
  )

  try:
    dispatch_rule = await livekit_api.sip.create_dispatch_rule(request)
    logger.debug(
        f"{root_folder} | {sub_file_path} | Created dispatch rule: '{dispatch_rule.name}' "
        f"with ID: {dispatch_rule.sip_dispatch_rule_id}"
    )
  except api.twirp_client.TwirpError as e:
      logger.error(f"{root_folder} | {sub_file_path} | Failed to create dispatch rule: {e}")
      raise
  finally:
      await livekit_api.aclose()

if __name__ == "__main__":
    asyncio.run(main())