"""
Vaani Advisory — Session Starter
==================================
Called by the outbound worker via the agent registry.
Owns all session construction logic for the farmer advisory agent.

Flow:
  1. Load farmer profile from RDS
  2. If not registered → polite message → return
  3. Build FarmerAdvisoryData from DB row
  4. Create VaaniFarmerAdvisoryAgent (orchestrator)
  5. Start AgentSession + background audio
"""
import asyncio

from livekit.agents import (
    JobContext,
    Agent,
    AgentSession,
    BackgroundAudioPlayer,
    AudioConfig,
    BuiltinAudioClip,
)

from agents.vaani_advisory.models.advisory_data_model import FarmerAdvisoryData
from agents.vaani_advisory.orchestrator_agent import VaaniFarmerAdvisoryAgent
from agents.vaani_advisory.prompts import (
    build_orchestrator_instructions,
    NOT_REGISTERED_INSTRUCTION,
)
from core.model_providers import model_providers
from core.config import logger
from core.db.farmer_db import SessionLocal, get_farmer_by_phone, get_farmer_crops

root_folder = "AGENTS | VAANI_ADVISORY"
sub_file_path = "SESSION"


async def start_advisory_session(
    ctx: JobContext,
    agent_params: dict,
    stt_config: str,
    llm_config: str,
    tts_config: str,
):
    """Build and start an AgentSession for the farmer advisory agent."""
    room_name = ctx.room.name
    farmer_phone = agent_params.get("farmer_phone", "")

    logger.debug(
        f"{room_name} | {root_folder} | {sub_file_path} | "
        f"Starting advisory session for phone={farmer_phone}"
    )

    # =========================================================================
    # 1. Load farmer profile from RDS
    # =========================================================================
    farmer = await asyncio.to_thread(_load_farmer_from_db, farmer_phone)

    if not farmer or not farmer.is_profile_complete:
        # Farmer not registered — brief message and disconnect
        logger.debug(
            f"{room_name} | {root_folder} | {sub_file_path} | "
            f"Farmer not registered or profile incomplete — sending fallback message"
        )

        fallback_agent = Agent(instructions=NOT_REGISTERED_INSTRUCTION)

        session = AgentSession(
            stt=model_providers.get_stt(stt_config),
            llm=model_providers.get_llm(llm_config, temperature=0.7),
            tts=model_providers.get_tts(tts_config),
            vad=model_providers.get_vad(),
            turn_detection=model_providers.get_turn_detection(),
        )

        await session.start(room=ctx.room, agent=fallback_agent)
        logger.debug(f"{room_name} | {root_folder} | {sub_file_path} | Fallback session started")
        return

    # =========================================================================
    # 2. Build FarmerAdvisoryData from DB row
    # =========================================================================
    farmer_crops = await asyncio.to_thread(_load_farmer_crops, farmer.farmer_id)

    farmer_data = FarmerAdvisoryData(
        farmer_phone=farmer_phone,
        farmer_id=str(farmer.farmer_id),
        name=farmer.name,
        state=farmer.state,
        district=farmer.district,
        pincode=farmer.pincode,
        preferred_language=farmer.preferred_language,
        irrigation_type=farmer.irrigation_type,
        primary_crops=[c.crop_name for c in farmer_crops] if farmer_crops else None,
        is_registered=True,
        is_web_session=agent_params.get("is_web_session", False),
    )

    logger.debug(
        f"{room_name} | {root_folder} | {sub_file_path} | "
        f"Farmer loaded: name={farmer_data.name}, state={farmer_data.state}, "
        f"crops={farmer_data.primary_crops}"
    )

    # =========================================================================
    # 3. Create orchestrator agent and session
    # =========================================================================
    instructions = build_orchestrator_instructions(farmer_data)
    agent = VaaniFarmerAdvisoryAgent(instructions=instructions)

    session = AgentSession(
        stt=model_providers.get_stt(stt_config),
        llm=model_providers.get_llm(llm_config, temperature=0.7),
        tts=model_providers.get_tts(tts_config),
        vad=model_providers.get_vad(),
        turn_detection=model_providers.get_turn_detection(),
        userdata=farmer_data,
        min_endpointing_delay=0.5,
        max_endpointing_delay=2.0,
        preemptive_generation=True,
    )

    await session.start(room=ctx.room, agent=agent)
    logger.debug(f"{room_name} | {root_folder} | {sub_file_path} | Session started")

    # =========================================================================
    # Text input handler — receives button taps and typed messages from frontend
    # =========================================================================
    def _on_data_received(data: bytes, *args, **kwargs):
        try:
            text = data.decode("utf-8").strip()
            if not text or text.startswith('{"vaani_cta"'):
                return  # ignore our own outgoing CTA messages
            logger.debug(f"{room_name} | {root_folder} | {sub_file_path} | TEXT_INPUT | '{text}'")
            asyncio.ensure_future(session.generate_reply(user_input=text))
        except Exception as e:
            logger.error(f"{room_name} | {root_folder} | {sub_file_path} | TEXT_INPUT_ERROR | {e}")

    ctx.room.on("data_received", _on_data_received)
    logger.debug(f"{room_name} | {root_folder} | {sub_file_path} | Text input handler registered")

    # Background audio: subtle ambient sound for presence and warmth
    background_audio = BackgroundAudioPlayer(
        ambient_sound=AudioConfig(BuiltinAudioClip.OFFICE_AMBIENCE, volume=0.7),
    )
    await background_audio.start(room=ctx.room, agent_session=session)
    logger.debug(f"{room_name} | {root_folder} | {sub_file_path} | Background audio started")


# =============================================================================
# DB HELPERS (sync — run in thread via asyncio.to_thread)
# =============================================================================

def _load_farmer_from_db(phone_number: str):
    """Load farmer by phone. Sync — meant to be called via asyncio.to_thread."""
    db = SessionLocal()
    try:
        return get_farmer_by_phone(db, phone_number)
    except Exception as e:
        logger.error(f"{root_folder} | {sub_file_path} | DB_LOAD | ERROR | {e}")
        return None
    finally:
        db.close()


def _load_farmer_crops(farmer_id):
    """Load farmer's crops. Sync — meant to be called via asyncio.to_thread."""
    db = SessionLocal()
    try:
        return get_farmer_crops(db, farmer_id)
    except Exception as e:
        logger.error(f"{root_folder} | {sub_file_path} | DB_LOAD_CROPS | ERROR | {e}")
        return []
    finally:
        db.close()
