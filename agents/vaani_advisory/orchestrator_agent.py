"""
Vaani Advisory — Orchestrator Agent
=====================================
Central conversational agent for the farmer advisory system.
Greets the farmer, detects intent, and hands off to specialist agents
via LiveKit's session.update_agent() API.

Architecture:
  VaaniFarmerAdvisoryAgent.on_enter()
      → greets farmer by name
      → farmer asks a question
      → orchestrator calls the matching function_tool
      → specialist agent takes over (session.update_agent)
      → specialist finishes → hands back to orchestrator
      → orchestrator asks "kuch aur?"
"""
from typing import AsyncIterable, Optional

from livekit import rtc
from livekit.agents import Agent, ChatContext, ChatMessage, ModelSettings, function_tool, RunContext

from agents.vaani_advisory.models.advisory_data_model import FarmerAdvisoryData
from agents.vaani_advisory.prompts import ORCHESTRATOR_GREETING
from core.config import logger
from core.conversation_fillers import play_filler
from core.cta import send_cta, home_cta
from core.pronunciation import apply_pronunciation_fixes, PRONUNCIATION_MAP

root_folder = "AGENTS | VAANI_ADVISORY"
sub_file_path = "ORCHESTRATOR"


class VaaniFarmerAdvisoryAgent(Agent):
    """
    Central orchestrator for the farmer advisory multi-agent system.

    On enter:
      1. Greets the farmer by name
      2. Asks what they need help with

    Function tools (handoff triggers):
      - get_weather_advisory → WeatherAdvisoryAgent
      - get_crop_advisory → CropAdvisoryAgent
      - get_mandi_prices → MandiAgent
      - get_govt_schemes → GovtSchemesAgent

    Each specialist calls done_with_<topic>() to return here.
    """

    def __init__(self, instructions: str, chat_ctx=None):
        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        """Greet the farmer and ask what they need help with."""
        try:
            data: FarmerAdvisoryData = self.session.userdata
            logger.debug(
                f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
                f"ON_ENTER | Orchestrator entered | topic={data.current_topic} | web={data.is_web_session}"
            )

            # If this is a return from a specialist, ask if they need anything else
            if data.current_topic:
                data.current_topic = None
                await self.session.generate_reply(
                    instructions=(
                        "The farmer just finished discussing a topic with a specialist. "
                        "Ask them warmly if they have any other questions or need help "
                        "with anything else. Keep it to 1-2 sentences."
                    )
                )
                # For web sessions: send home CTA buttons after the voice response
                if data.is_web_session:
                    msg, buttons = home_cta(data.name or "")
                    await send_cta(self.session, msg, buttons)
            else:
                # First entry — greet and ask what they need
                await self.session.generate_reply(instructions=ORCHESTRATOR_GREETING)
                # For web sessions: also send the home CTA immediately
                if data.is_web_session:
                    msg, buttons = home_cta(data.name or "")
                    await send_cta(self.session, msg, buttons)

        except Exception as e:
            logger.error(f"{root_folder} | {sub_file_path} | ON_ENTER | ERROR | {e}")
            raise

    # =========================================================================
    # HANDOFF TOOLS — route to specialist agents
    # =========================================================================

    @function_tool(description=(
        "Call when the farmer asks about weather, rain, temperature, humidity, "
        "irrigation timing, or farming conditions related to weather."
    ))
    async def get_weather_advisory(
        self,
        context: RunContext[FarmerAdvisoryData],
    ) -> str:
        """Hand off to the weather advisory specialist."""
        data: FarmerAdvisoryData = context.userdata
        data.current_topic = "weather"

        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"HANDOFF | → WeatherAdvisoryAgent"
        )

        from agents.vaani_advisory.specialists.weather_agent import WeatherAdvisoryAgent
        from agents.vaani_advisory.prompts import build_weather_instructions

        await self.session.update_agent(
            WeatherAdvisoryAgent(
                instructions=build_weather_instructions(data),
                farmer_data=data,
                chat_ctx=self.chat_ctx,
            )
        )
        return "Handing off to weather advisor"

    @function_tool(description=(
        "Call when the farmer asks about crop disease, crop varieties, sowing time, "
        "fertilizer, harvest, crop calendar, or any crop-related advice. "
        "If the farmer mentions a specific crop name, pass it as crop_name."
    ))
    async def get_crop_advisory(
        self,
        context: RunContext[FarmerAdvisoryData],
        crop_name: Optional[str] = None,
    ) -> str:
        """Hand off to the crop advisory specialist."""
        data: FarmerAdvisoryData = context.userdata
        data.current_topic = "crop"
        if crop_name:
            data.active_crop = crop_name.strip()

        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"HANDOFF | → CropAdvisoryAgent | crop={data.active_crop}"
        )

        from agents.vaani_advisory.specialists.crop_agent import CropAdvisoryAgent
        from agents.vaani_advisory.prompts import build_crop_instructions

        await self.session.update_agent(
            CropAdvisoryAgent(
                instructions=build_crop_instructions(data),
                farmer_data=data,
                chat_ctx=self.chat_ctx,
            )
        )
        return "Handing off to crop advisor"

    @function_tool(description=(
        "Call when the farmer asks about market prices, mandi rates, where to sell, "
        "price trends, or selling decisions. "
        "If the farmer mentions a specific crop name, pass it as crop_name."
    ))
    async def get_mandi_prices(
        self,
        context: RunContext[FarmerAdvisoryData],
        crop_name: Optional[str] = None,
    ) -> str:
        """Hand off to the mandi price specialist."""
        data: FarmerAdvisoryData = context.userdata
        data.current_topic = "mandi"
        if crop_name:
            data.active_crop = crop_name.strip()

        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"HANDOFF | → MandiAgent | crop={data.active_crop}"
        )

        from agents.vaani_advisory.specialists.mandi_agent import MandiAgent
        from agents.vaani_advisory.prompts import build_mandi_instructions

        await self.session.update_agent(
            MandiAgent(
                instructions=build_mandi_instructions(data),
                farmer_data=data,
                chat_ctx=self.chat_ctx,
            )
        )
        return "Handing off to mandi advisor"

    @function_tool(description=(
        "Call when the farmer asks about government schemes, subsidies, loans, "
        "PM-Kisan, crop insurance, KCC, or any government support program."
    ))
    async def get_govt_schemes(
        self,
        context: RunContext[FarmerAdvisoryData],
    ) -> str:
        """Hand off to the government schemes specialist."""
        data: FarmerAdvisoryData = context.userdata
        data.current_topic = "schemes"

        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"HANDOFF | → GovtSchemesAgent"
        )

        from agents.vaani_advisory.specialists.govt_schemes_agent import GovtSchemesAgent
        from agents.vaani_advisory.prompts import build_schemes_instructions

        await self.session.update_agent(
            GovtSchemesAgent(
                instructions=build_schemes_instructions(data),
                farmer_data=data,
                chat_ctx=self.chat_ctx,
            )
        )
        return "Handing off to schemes advisor"

    # =========================================================================
    # HOOKS — conversation fillers + pronunciation
    # =========================================================================

    async def on_user_turn_completed(
        self,
        turn_ctx: ChatContext,
        new_message: ChatMessage,
    ) -> None:
        """Play a conversation filler to mask LLM thinking latency."""
        play_filler(self.session)

    async def tts_node(
        self,
        text: AsyncIterable[str],
        model_settings: ModelSettings,
    ) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        """Apply pronunciation corrections before TTS."""
        if PRONUNCIATION_MAP:
            corrected_text = apply_pronunciation_fixes(text)
            async for frame in Agent.default.tts_node(self, corrected_text, model_settings):
                yield frame
        else:
            async for frame in Agent.default.tts_node(self, text, model_settings):
                yield frame
