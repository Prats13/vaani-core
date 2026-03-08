"""
Vaani Web Worker
================
Handles browser-based LiveKit sessions from the Vaani web frontend.

Participant identity format (set by Next.js frontend):
  farmer_{digits}   e.g. farmer_919876543210

On participant join:
  1. Extract phone number from identity
  2. Load farmer from RDS
  3. If registered → start advisory session
  4. If not registered → brief message asking them to complete onboarding via phone call

This worker runs separately from outbound_worker (PSTN calls).
"""
import asyncio
import json
import re

from livekit.agents import JobContext, AgentServer, AutoSubscribe, Agent, AgentSession, WorkerOptions

from agents.registry import OUTBOUND_AGENT_REGISTRY
from core.config import settings, logger
from core.model_providers import model_providers
from core.room_event_handler import create_callback_registry, setup_room_listeners

root_folder = "WEB_WORKER"
sub_file_path = "ENTRYPOINT"

server = AgentServer()


def _extract_phone_from_identity(identity: str) -> str | None:
    """
    Extract E.164 phone number from participant identity.
    farmer_919876543210 → +919876543210
    """
    match = re.match(r"^farmer_(\d+)$", identity)
    if match:
        digits = match.group(1)
        return f"+{digits}"
    return None


@server.rtc_session(agent_name="vaani_web_agent")
async def entrypoint(ctx: JobContext):
    """Entry point for web browser sessions."""
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)

    callbacks = create_callback_registry()
    setup_room_listeners(
        ctx.room,
        log_context={
            "room_name": ctx.room.name,
            "root_folder": root_folder,
            "sub_file_path": sub_file_path,
        },
        callbacks=callbacks,
    )

    participant = (
        list(ctx.room.remote_participants.values())[0]
        if ctx.room.remote_participants
        else None
    )
    if not participant:
        logger.debug(f"{root_folder} | No participant yet, waiting...")
        participant = await ctx.wait_for_participant()

    room_name = ctx.room.name
    identity = participant.identity
    logger.debug(f"{room_name} | {root_folder} | Participant joined: identity={identity}")

    # Parse phone from identity
    farmer_phone = _extract_phone_from_identity(identity)
    if not farmer_phone:
        logger.debug(
            f"{room_name} | {root_folder} | "
            f"Invalid identity format: {identity} — expected farmer_{{digits}}"
        )
        return

    logger.debug(f"{room_name} | {root_folder} | Resolved phone={farmer_phone}")

    # Read metadata dispatched from the token endpoint (may carry farmer_phone too)
    metadata = {}
    if ctx.job.metadata:
        try:
            metadata = json.loads(ctx.job.metadata)
        except Exception:
            pass

    # Dispatch to advisory session via registry
    session_starter = OUTBOUND_AGENT_REGISTRY.get("farmer_advisory")
    if not session_starter:
        logger.error(f"{room_name} | {root_folder} | farmer_advisory not in registry")
        return

    agent_params = {
        "farmer_phone": farmer_phone,
        "farmer_id": metadata.get("farmer_id", ""),
        "is_web_session": True,
    }

    stt_config = "sarvam-saarika-2.5"
    llm_config = "gemini-2.5-flash"
    tts_config = "sarvam-bulbul"

    logger.debug(
        f"{room_name} | {root_folder} | Dispatching farmer_advisory for phone={farmer_phone}"
    )

    try:
        await session_starter(ctx, agent_params, stt_config, llm_config, tts_config)
    except Exception as e:
        logger.error(f"{room_name} | {root_folder} | SESSION_ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(server.run(WorkerOptions(http_port=8082)))
