"""
Vaani Outbound Worker
=====================
Entry point for LiveKit outbound call sessions.
Reads agent_type from SIP participant attributes and looks up the correct
agent via the registry — no agent-specific logic lives here.

Participant data layout (set by sip_routes.py):
  - attributes: agent_config + call_config fields as flat key-value strings
  - metadata:   agent_params as JSON (native types preserved)
"""
import json
import asyncio

from livekit.agents import JobContext, AgentServer, AutoSubscribe

from agents.registry import OUTBOUND_AGENT_REGISTRY
from core.config import logger
from core.room_event_handler import create_callback_registry, setup_room_listeners

root_folder = "OUTBOUND_WORKER"
sub_file_path = "ENTRYPOINT"

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)

    callbacks = create_callback_registry()
    setup_room_listeners(
        ctx.room,
        log_context={"room_name": ctx.room.name, "root_folder": root_folder, "sub_file_path": sub_file_path},
        callbacks=callbacks,
    )

    participant = list(ctx.room.remote_participants.values())[0] if ctx.room.remote_participants else None
    if not participant:
        logger.debug(f"{root_folder} | No participant yet, waiting...")
        participant = await ctx.wait_for_participant()

    room_name = ctx.room.name

    # =========================================================================
    # Parse participant data
    # =========================================================================
    attrs = participant.attributes or {}
    agent_type = attrs.get("agent_type", "")
    stt_config = attrs.get("stt_config", "sarvam-saarika-2.5")
    llm_config = attrs.get("llm_config", "gemini-2.5-flash")
    tts_config = attrs.get("tts_config", "sarvam-bulbul")

    agent_params = json.loads(participant.metadata) if participant.metadata else {}

    # =========================================================================
    # Validate
    # =========================================================================
    if not agent_type:
        logger.debug(f"{room_name} | {root_folder} | No agent_type in attributes — REJECTED")
        return

    if agent_type.lower() == "human":
        logger.debug(f"{room_name} | {root_folder} | Human agent — bypassing AI worker")
        return

    # =========================================================================
    # Registry lookup and dispatch
    # =========================================================================
    session_starter = OUTBOUND_AGENT_REGISTRY.get(agent_type)

    if not session_starter:
        logger.debug(f"{room_name} | {root_folder} | No agent registered for type: '{agent_type}'")
        return

    logger.debug(f"{room_name} | {root_folder} | Dispatching agent_type='{agent_type}'")

    try:
        await session_starter(ctx, agent_params, stt_config, llm_config, tts_config)
    except Exception as e:
        logger.error(f"{room_name} | {root_folder} | SESSION_ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(server.run())