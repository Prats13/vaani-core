"""
Vaani Inbound Worker
====================
Entry point for LiveKit worker process that handles incoming voice sessions.
Handles inbound calls from farmers via Exotel SIP → LiveKit.
"""
import re
import asyncio

from livekit.agents import JobContext, AgentServer, AutoSubscribe, AgentSession

from core.config import settings, logger
from core.model_providers import model_providers
from core.room_event_handler import create_callback_registry, setup_room_listeners

root_folder = "INBOUND_WORKER"
sub_file_path = "ENTRYPOINT"

server = AgentServer()


@server.rtc_session(agent_name="vaani_inbound_agent")
async def entrypoint(ctx: JobContext):
    """
    Entry point for LiveKit inbound worker.
    Called when a farmer calls in via Exotel SIP trunk.
    """
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)

    # Phase 1: Register all room event listeners immediately after connect
    callbacks = create_callback_registry()
    setup_room_listeners(
        ctx.room,
        log_context={"room_name": ctx.room.name, "root_folder": root_folder, "sub_file_path": sub_file_path},
        callbacks=callbacks,
    )

    participant = list(ctx.room.remote_participants.values())[0] if ctx.room.remote_participants else None

    if not participant:
        logger.debug(f"{root_folder} | No participant in remote_participants, waiting...")
        participant = await ctx.wait_for_participant()

    room_name = ctx.room.name
    logger.debug(f"{room_name} | {root_folder} | Participant {participant.identity} joined")

    # Extract participant attributes
    call_direction = participant.attributes.get("call_direction", "")
    call_type = participant.attributes.get("call_type", "")
    call_provider = participant.attributes.get("call_provider", "")

    # Extract caller number from SIP P-Asserted-Identity header
    exotel_asserted_identity = participant.attributes.get("exotel_asserted_identity", "")
    caller_number = None
    if exotel_asserted_identity:
        match = re.search(r"<sip:([^@]+)@", exotel_asserted_identity)
        if match:
            caller_number = match.group(1)

    if not caller_number:
        logger.debug(f"{room_name} | {root_folder} | No caller number extracted — unauthorized connection")
        await ctx.room.disconnect()
        return None

    logger.debug(f"{room_name} | {root_folder} | Inbound call from {caller_number} via {call_provider}")

    if call_provider == "exotel":
        exotel_call_sid = participant.attributes.get("exotel_call_sid", "")

        try:
            # Build session with Vaani defaults: Sarvam STT (Hindi), Gemini LLM, Sarvam TTS
            stt = model_providers.get_stt("sarvam-saarika-2.5")
            llm = model_providers.get_llm("gemini-2.5-flash", temperature=0.7)
            tts = model_providers.get_tts("sarvam-bulbul")
            vad = model_providers.get_vad()
            turn_detector = model_providers.get_turn_detection()

            session = AgentSession(
                stt=stt,
                llm=llm,
                tts=tts,
                vad=vad,
                turn_detection=turn_detector,
                userdata={
                    "caller_number": caller_number,
                    "call_sid": exotel_call_sid,
                    "call_direction": call_direction,
                    "room_name": room_name,
                },
                min_endpointing_delay=0.5,
                max_endpointing_delay=2.0,
            )

            # TODO: Wire actual Vaani agent here once agents/farmer_advisory/ is built
            # await session.start(room=ctx.room, agent=vaani_agent)

            logger.debug(f"{room_name} | {root_folder} | Session created (agent not yet wired)")

        except Exception as e:
            logger.error(f"{room_name} | {root_folder} | SESSION_ERROR: {e}")
            raise
    else:
        logger.debug(f"{room_name} | {root_folder} | Unknown call_provider: {call_provider}")
        return None


if __name__ == "__main__":
    asyncio.run(server.run())
