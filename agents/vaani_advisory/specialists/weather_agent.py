"""
Vaani Advisory — Weather Advisory Agent
=========================================
Specialist agent for weather-related queries.
Fetches weather data from data_service directly (same process, no HTTP)
and presents it in farmer-friendly language.
"""
import asyncio
import json
from typing import AsyncIterable, Optional

from livekit import rtc
from livekit.agents import Agent, ChatContext, ChatMessage, ModelSettings, function_tool, RunContext

from agents.vaani_advisory.models.advisory_data_model import FarmerAdvisoryData
from core.config import logger
from core.conversation_fillers import play_filler
from core.cta import send_cta
from core.pronunciation import apply_pronunciation_fixes, PRONUNCIATION_MAP

root_folder = "AGENTS | VAANI_ADVISORY"
sub_file_path = "WEATHER_AGENT"


class WeatherAdvisoryAgent(Agent):
    """
    Specialist agent for weather advisory.

    On enter:
      1. Fetches weather for farmer's pincode from data_service
      2. Injects weather summary into chat context
      3. Generates opening response with weather insights

    Tools:
      - done_with_weather: returns control to orchestrator
    """

    def __init__(self, instructions: str, farmer_data: FarmerAdvisoryData, chat_ctx=None):
        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )
        self._farmer_data = farmer_data

    async def on_enter(self) -> None:
        """Fetch weather data and present to farmer."""
        data = self._farmer_data
        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"ON_ENTER | Fetching weather for pincode={data.pincode}"
        )

        weather_context = await self._fetch_weather_data(data)

        # Generate response with weather data injected
        await self.session.generate_reply(
            instructions=(
                f"You have just received the following weather data for the farmer's area. "
                f"Summarise it in simple, farmer-friendly language. "
                f"Highlight anything important for farming decisions.\n\n"
                f"Weather Data:\n{weather_context}"
            )
        )

        if data.is_web_session:
            await send_cta(self.session, "Mausam ke baare mein kuch aur poochna hai?",
                           ["Irrigation Timing", "Rain Forecast", "Back to Home"])

    async def _fetch_weather_data(self, data: FarmerAdvisoryData) -> str:
        """Fetch weather from data_service. Returns a string summary for the LLM."""
        if not data.pincode:
            return (
                "Weather data not available — farmer's pincode is not in their profile. "
                "Apologise and suggest they update their profile with their pincode."
            )

        try:
            from data_service.weather.services.weather_service import get_weather_for_pincode
            from data_service.core.db import SessionLocal

            db = SessionLocal()
            try:
                weather = await get_weather_for_pincode(db, data.pincode)
                weather_str = json.dumps(weather, default=str, indent=2)
                logger.debug(
                    f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
                    f"WEATHER_FETCH | Success for pincode={data.pincode}"
                )
                return weather_str
            finally:
                db.close()

        except Exception as e:
            logger.error(
                f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
                f"WEATHER_FETCH | ERROR | {e}"
            )
            return (
                "Weather data could not be fetched right now due to a temporary error. "
                "Apologise to the farmer and say you will try again later. "
                "Do NOT make up weather information."
            )

    # =========================================================================
    # RETURN TO ORCHESTRATOR
    # =========================================================================

    @function_tool(description=(
        "Call when the farmer's weather question is answered and they want to "
        "ask about something else, or when they are done with weather."
    ))
    async def done_with_weather(
        self,
        context: RunContext[FarmerAdvisoryData],
    ) -> str:
        """Return control to the orchestrator."""
        data: FarmerAdvisoryData = context.userdata

        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"HANDOFF | → Orchestrator (done with weather)"
        )

        from agents.vaani_advisory.orchestrator_agent import VaaniFarmerAdvisoryAgent
        from agents.vaani_advisory.prompts import build_orchestrator_instructions

        await self.session.update_agent(
            VaaniFarmerAdvisoryAgent(
                instructions=build_orchestrator_instructions(data),
                chat_ctx=self.chat_ctx,
            )
        )
        return "Returning to main menu"

    # =========================================================================
    # HOOKS
    # =========================================================================

    async def on_user_turn_completed(
        self,
        turn_ctx: ChatContext,
        new_message: ChatMessage,
    ) -> None:
        play_filler(self.session)

    async def tts_node(
        self,
        text: AsyncIterable[str],
        model_settings: ModelSettings,
    ) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        if PRONUNCIATION_MAP:
            corrected_text = apply_pronunciation_fixes(text)
            async for frame in Agent.default.tts_node(self, corrected_text, model_settings):
                yield frame
        else:
            async for frame in Agent.default.tts_node(self, text, model_settings):
                yield frame
