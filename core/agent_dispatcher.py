"""
Vaani Agent Dispatcher
======================
Routes incoming call sessions to the correct agent based on agent_type.

Architecture:
  dispatch_vaani_agent()            ← router: maps agent_type → child session creator
  create_farmer_advisory_session()  ← handles farmer_advisory agent_type
  create_farmer_onboarding_session()← handles farmer_onboarding agent_type

To add a new agent type:
  1. Write a new create_<agent_type>_session() method
  2. Add a single elif in dispatch_vaani_agent() mapping the agent_type to it
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, Set

from livekit.agents import JobContext, AgentSession

from core.config import settings, logger
from core.model_providers import model_providers
from core.room_event_handler import CallbackRegistry


@dataclass
class VaaniDispatchContext:
    """
    Fully resolved context for dispatching a Vaani agent session.
    Populated by workers from participant attributes + metadata.
    """
    # From participant.attributes (agent_config + call_config)
    agent_type: str
    stt_config: str
    llm_config: str
    tts_config: str
    call_direction: str
    call_provider: str

    # From participant.metadata (native types — bools, ints, floats intact)
    agent_params: Dict[str, Any]

    room_name: str
    participant_identity: str

    # Optional — populated from agent_params if available
    farmer_phone: str = ""


@dataclass
class VaaniSessionData:
    """Session data stored in the registry for post-processing."""
    room_name: str
    farmer_phone: str = ""
    farmer_name: str = ""
    agent_type: str = ""
    conversation_start_time: str = ""
    conversation_end_time: str = ""


# =============================================================================
# AGENT ROUTER
# =============================================================================

async def dispatch_vaani_agent(
    ctx: JobContext,
    dispatch_ctx: VaaniDispatchContext,
    session_registry: Dict[str, Any],
    callbacks: CallbackRegistry,
    started_track_sids: Set[str],
) -> Optional[AgentSession]:
    """
    Route by agent_type and delegate to the appropriate session creator.

    Returns:
        Started AgentSession, or None if agent_type is unrecognised
    """
    agent_type = dispatch_ctx.agent_type
    room_name = dispatch_ctx.room_name

    if agent_type == "farmer_advisory":
        return await create_farmer_advisory_session(ctx, dispatch_ctx, session_registry, callbacks, started_track_sids)

    elif agent_type == "farmer_onboarding":
        return await create_farmer_onboarding_session(ctx, dispatch_ctx, session_registry, callbacks, started_track_sids)

    elif agent_type == "human":
        logger.debug(f"{room_name} | AGENT_DISPATCHER | Human agent bypass caught in dispatcher")
        return None

    else:
        logger.debug(f"{room_name} | AGENT_DISPATCHER | Unknown agent_type: '{agent_type}' — no handler registered")
        return None


# =============================================================================
# SESSION CREATORS (Stubs — agent implementations will be added later)
# =============================================================================

async def create_farmer_advisory_session(
    ctx: JobContext,
    dispatch_ctx: VaaniDispatchContext,
    session_registry: Dict[str, Any],
    callbacks: CallbackRegistry,
    started_track_sids: Set[str],
) -> AgentSession:
    """
    Build and start an AgentSession for the farmer advisory agent.
    Delegates to agents/vaani_advisory/session.py which handles DB lookup,
    agent creation, and session startup.
    """
    from agents.vaani_advisory.session import start_advisory_session

    room_name = dispatch_ctx.room_name
    params = dispatch_ctx.agent_params
    farmer_name = params.get("farmer_name", "Kisan")

    # Store session data for post-processing
    session_data = VaaniSessionData(
        room_name=room_name,
        farmer_phone=dispatch_ctx.farmer_phone,
        farmer_name=farmer_name,
        agent_type=dispatch_ctx.agent_type,
    )
    session_registry[room_name] = session_data

    logger.debug(
        f"{room_name} | AGENT_DISPATCHER | farmer_advisory dispatching to start_advisory_session | "
        f"STT={dispatch_ctx.stt_config}, LLM={dispatch_ctx.llm_config}, TTS={dispatch_ctx.tts_config}"
    )

    await start_advisory_session(
        ctx=ctx,
        agent_params=params,
        stt_config=dispatch_ctx.stt_config,
        llm_config=dispatch_ctx.llm_config,
        tts_config=dispatch_ctx.tts_config,
    )

    return None


async def create_farmer_onboarding_session(
    ctx: JobContext,
    dispatch_ctx: VaaniDispatchContext,
    session_registry: Dict[str, Any],
    callbacks: CallbackRegistry,
    started_track_sids: Set[str],
) -> AgentSession:
    """
    Build and start an AgentSession for farmer onboarding (profile collection).
    This is a stub — the actual agent will be wired in once built.
    """
    room_name = dispatch_ctx.room_name
    params = dispatch_ctx.agent_params

    session_data = VaaniSessionData(
        room_name=room_name,
        farmer_phone=dispatch_ctx.farmer_phone,
        farmer_name=params.get("farmer_name", "Kisan"),
        agent_type=dispatch_ctx.agent_type,
    )
    session_registry[room_name] = session_data

    session = AgentSession(
        stt=model_providers.get_stt(dispatch_ctx.stt_config),
        llm=model_providers.get_llm(dispatch_ctx.llm_config, temperature=0.5),
        tts=model_providers.get_tts(dispatch_ctx.tts_config),
        vad=model_providers.get_vad(),
        userdata=session_data,
    )

    logger.debug(
        f"{room_name} | AGENT_DISPATCHER | farmer_onboarding session created | "
        f"STT={dispatch_ctx.stt_config}, LLM={dispatch_ctx.llm_config}, TTS={dispatch_ctx.tts_config}"
    )

    return session
