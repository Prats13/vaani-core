"""
Vaani Outbound Worker
=====================
Entry point for LiveKit outbound call sessions.
Reads agent configuration from SIP participant attributes and metadata,
then delegates to core/agent_dispatcher.py for agent-type-specific wiring.

Participant data layout (set by sip_routes.py):
  - attributes: agent_config + call_config fields as flat key-value strings
  - metadata:   agent_params as JSON (native types preserved)
"""
import json
import asyncio
from typing import Dict, Any

from livekit.agents import JobContext, AgentServer, AutoSubscribe

from core.config import logger
from core.agent_dispatcher import VaaniDispatchContext, VaaniSessionData, dispatch_vaani_agent
from core.room_event_handler import create_callback_registry, setup_room_listeners

root_folder = "OUTBOUND_WORKER"
sub_file_path = "ENTRYPOINT"

# Session registry: room_name → VaaniSessionData (for post-processing access)
_session_registry: Dict[str, VaaniSessionData] = {}

server = AgentServer()


async def handle_outbound_session_end(ctx: JobContext) -> None:
    """
    Post-processing handler for outbound calls.
    Reads session_data from registry (populated during session start).
    """
    room_name = ctx.room.name
    logger.debug(f"{room_name} | {root_folder} | Outbound session ended")

    session_data = _session_registry.pop(room_name, None)

    if not session_data:
        logger.debug(f"{room_name} | {root_folder} | No session_data in registry, skipping post-processing")
        return

    # TODO: Add Vaani-specific post-processing here
    # e.g., save conversation transcript, update farmer profile, etc.
    logger.debug(
        f"{room_name} | {root_folder} | Post-processing complete for farmer: {session_data.farmer_name}"
    )


@server.rtc_session(on_session_end=handle_outbound_session_end)
async def entrypoint(ctx: JobContext):
    """
    Entry point for outbound LiveKit worker.
    Responsibility: parse participant data → delegate to agent_dispatcher.
    Does NOT contain any agent-specific logic.
    """
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)

    # Phase 1: Register all room event listeners immediately after connect
    callbacks = create_callback_registry()
    started_track_sids = setup_room_listeners(
        ctx.room,
        log_context={"room_name": ctx.room.name, "root_folder": root_folder, "sub_file_path": sub_file_path},
        callbacks=callbacks,
    )

    participant = list(ctx.room.remote_participants.values())[0] if ctx.room.remote_participants else None

    if not participant:
        logger.debug(f"{root_folder} | No participant in room yet, waiting...")
        participant = await ctx.wait_for_participant()

    room_name = ctx.room.name
    logger.debug(f"{room_name} | {root_folder} | Participant {participant.identity} joined")

    # =========================================================================
    # Parse participant.attributes → agent_config + call_config (flat strings)
    # =========================================================================
    attrs = participant.attributes or {}
    agent_type     = attrs.get("agent_type", "")
    stt_config     = attrs.get("stt_config", "sarvam-saarika-2.5")
    llm_config     = attrs.get("llm_config", "gemini-2.5-flash")
    tts_config     = attrs.get("tts_config", "sarvam-bulbul")
    call_direction = attrs.get("call_direction", "")
    call_provider  = attrs.get("call_provider", "")

    # =========================================================================
    # Parse participant.metadata → agent_params JSON (native types intact)
    # =========================================================================
    agent_params = json.loads(participant.metadata) if participant.metadata else {}
    farmer_phone = agent_params.get("farmer_phone", "")

    # =========================================================================
    # Validate required fields
    # =========================================================================
    if not agent_type:
        logger.debug(f"{room_name} | {root_folder} | No agent_type in participant attributes — REJECTED")
        return None

    if agent_type.lower() == "human":
        logger.debug(f"{room_name} | {root_folder} | Human agent call detected. Bypassing AI worker.")
        return None

    logger.debug(
        f"{room_name} | {root_folder} | Parsed: agent_type={agent_type}, direction={call_direction}, provider={call_provider}"
    )

    # =========================================================================
    # Delegate to agent dispatcher — all agent-specific logic lives there
    # =========================================================================
    dispatch_ctx = VaaniDispatchContext(
        agent_type=agent_type,
        stt_config=stt_config,
        llm_config=llm_config,
        tts_config=tts_config,
        call_direction=call_direction,
        call_provider=call_provider,
        agent_params=agent_params,
        room_name=room_name,
        participant_identity=participant.identity,
        farmer_phone=farmer_phone,
    )

    try:
        await dispatch_vaani_agent(ctx, dispatch_ctx, _session_registry, callbacks, started_track_sids)
    except Exception as e:
        _session_registry.pop(room_name, None)
        logger.error(f"{room_name} | {root_folder} | SESSION_ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(server.run())
