"""
Vaani Advisory — Crop Advisory Agent
======================================
Specialist agent for crop-related queries.
Fetches crop data from data_service directly (same process, no HTTP)
and presents varieties, calendar, stage info in farmer-friendly language.
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
sub_file_path = "CROP_AGENT"


class CropAdvisoryAgent(Agent):
    """
    Specialist agent for crop advisory.

    On enter:
      1. Fetches crop data (varieties, calendar, stage) from data_service
      2. Injects crop summary into chat context
      3. Generates opening response with crop insights

    Tools:
      - done_with_crop: returns control to orchestrator
    """

    def __init__(self, instructions: str, farmer_data: FarmerAdvisoryData, chat_ctx=None):
        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )
        self._farmer_data = farmer_data

    async def on_enter(self) -> None:
        """Fetch crop data and present to farmer."""
        data = self._farmer_data
        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"ON_ENTER | Fetching crop data for crop={data.active_crop}, state={data.state}"
        )

        crop_context = await self._fetch_crop_data(data)

        if data.is_web_session:
            await self.session.say(f"Chaliye {data.active_crop or 'fasal'} ke baare mein baat karte hain!")
            await send_cta(self.session, ["Varieties", "Sowing Time", "Fertilizer Tips", "Back to Home"])
        else:
            await self.session.generate_reply(
                instructions=(
                    f"You have just received crop data for the farmer. "
                    f"Present the most relevant information in simple language. "
                    f"Focus on what's actionable for the farmer right now.\n\n"
                    f"Crop Data:\n{crop_context}"
                )
            )

    async def _fetch_crop_data(self, data: FarmerAdvisoryData) -> str:
        """Fetch crop info from data_service. Returns a string summary for the LLM."""
        if not data.active_crop:
            return (
                "The farmer hasn't specified which crop they want advice about. "
                "Ask them which crop they would like to discuss."
            )

        try:
            from data_service.crop.services.crop_catalog_service import (
                get_varieties_by_crop,
                get_crop_stage,
                get_calendar_windows,
            )
            from data_service.core.db import SessionLocal

            db = SessionLocal()
            try:
                results = {}

                # Fetch varieties for crop + state
                if data.state:
                    try:
                        varieties = await get_varieties_by_crop(
                            db, data.active_crop, data.state, limit=5, include_raw_text=False
                        )
                        results["varieties"] = varieties
                    except Exception as e:
                        logger.warning(f"{sub_file_path} | varieties fetch failed: {e}")

                # Fetch current crop stage
                try:
                    stage = await get_crop_stage(db, data.active_crop)
                    results["current_stage"] = stage
                except Exception as e:
                    logger.warning(f"{sub_file_path} | stage fetch failed: {e}")

                # Fetch calendar windows
                try:
                    calendar = await get_calendar_windows(db, data.active_crop)
                    results["calendar"] = calendar
                except Exception as e:
                    logger.warning(f"{sub_file_path} | calendar fetch failed: {e}")

                if results:
                    crop_str = json.dumps(results, default=str, indent=2)
                    logger.debug(
                        f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
                        f"CROP_FETCH | Success for crop={data.active_crop}"
                    )
                    return crop_str
                else:
                    return (
                        f"No detailed data found for {data.active_crop} in the database. "
                        f"Provide general advice from your knowledge about this crop."
                    )
            finally:
                db.close()

        except Exception as e:
            logger.error(
                f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
                f"CROP_FETCH | ERROR | {e}"
            )
            return (
                f"Crop data could not be fetched right now due to a temporary error. "
                f"Provide general advice about {data.active_crop} from your knowledge, "
                f"but mention that detailed data is temporarily unavailable."
            )

    # =========================================================================
    # RETURN TO ORCHESTRATOR
    # =========================================================================

    @function_tool(description=(
        "Call when the farmer's crop question is answered and they want to "
        "ask about something else, or when they are done with crop advice."
    ))
    async def done_with_crop(
        self,
        context: RunContext[FarmerAdvisoryData],
    ) -> str:
        """Return control to the orchestrator."""
        data: FarmerAdvisoryData = context.userdata

        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"HANDOFF | → Orchestrator (done with crop)"
        )

        from agents.vaani_advisory.orchestrator_agent import VaaniFarmerAdvisoryAgent
        from agents.vaani_advisory.prompts import build_orchestrator_instructions

        self.session.update_agent(
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
