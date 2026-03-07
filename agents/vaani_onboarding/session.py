"""
Vaani Onboarding — Session Starter
====================================
Called by the outbound worker via the agent registry.
Owns all session construction logic for the onboarding agent.
"""
from livekit.agents import JobContext, AgentSession

from agents.vaani_onboarding.onboarding_agent import VaaniOnboardingAgent
from agents.vaani_onboarding.models.onboarding_data_model import FarmerOnboardingData
from agents.vaani_onboarding.prompts import build_agent_instructions
from core.model_providers import model_providers
from core.config import logger

root_folder = "AGENTS | VAANI_ONBOARDING"
sub_file_path = "SESSION"


async def start_onboarding_session(
    ctx: JobContext,
    agent_params: dict,
    stt_config: str,
    llm_config: str,
    tts_config: str,
):
    """Build and start an AgentSession for the farmer onboarding agent."""
    room_name = ctx.room.name

    farmer_data = FarmerOnboardingData(
        farmer_id=agent_params.get("farmer_id", ""),
        farmer_phone_number=agent_params.get("farmer_phone", ""),
        farmer_name=agent_params.get("farmer_name"),
    )

    instructions = build_agent_instructions(farmer_data)

    agent = VaaniOnboardingAgent(instructions=instructions)

    session = AgentSession(
        stt=model_providers.get_stt(stt_config),
        llm=model_providers.get_llm(llm_config, temperature=0.7),
        tts=model_providers.get_tts(tts_config),
        vad=model_providers.get_vad(),
        turn_detection=model_providers.get_turn_detection(),
        userdata=farmer_data,
        min_endpointing_delay=0.5,
        max_endpointing_delay=2.0,
    )

    await session.start(room=ctx.room, agent=agent)
    logger.debug(f"{room_name} | {root_folder} | {sub_file_path} | Session started")
