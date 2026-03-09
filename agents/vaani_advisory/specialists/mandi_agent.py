"""
Vaani Advisory — Mandi Price Agent
=====================================
Specialist agent for market price queries.
Fetches mandi insights from data_service directly (same process, no HTTP)
and presents price trends, best markets in farmer-friendly language.
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
sub_file_path = "MANDI_AGENT"


class MandiAgent(Agent):
    """
    Specialist agent for mandi (market) price advisory.

    On enter:
      1. Fetches mandi insights for farmer's state + crop from data_service
      2. Injects price summary into chat context
      3. Generates opening response with market insights

    Tools:
      - done_with_mandi: returns control to orchestrator
    """

    def __init__(self, instructions: str, farmer_data: FarmerAdvisoryData, chat_ctx=None):
        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )
        self._farmer_data = farmer_data

    async def on_enter(self) -> None:
        """Fetch mandi data and present to farmer."""
        data = self._farmer_data
        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"ON_ENTER | Fetching mandi data for state={data.state}, crop={data.active_crop}"
        )

        mandi_context = await self._fetch_mandi_data(data)

        await self.session.generate_reply(
            instructions=(
                f"You have just received mandi (market) price data for the farmer. "
                f"Summarise the key insights: current prices, trends, and best markets to sell at. "
                f"Keep it simple and actionable.\n\n"
                f"Mandi Data:\n{mandi_context}"
            )
        )

        if data.is_web_session:
            await send_cta(self.session, "Mandi ke baare mein kuch aur poochna hai?",
                           ["Best Market Near Me", "Price Trend", "When to Sell", "Back to Home"])

    async def _fetch_mandi_data(self, data: FarmerAdvisoryData) -> str:
        """Fetch mandi insights from data_service. Returns a string summary for the LLM."""
        if not data.state:
            return (
                "Mandi data not available — farmer's state is not in their profile. "
                "Ask them which state they want market prices for."
            )

        try:
            from data_service.mandi.services.mandi_service import get_mandi_insights
            from data_service.core.db import SessionLocal

            db = SessionLocal()
            try:
                insights = await get_mandi_insights(
                    db=db,
                    state=data.state,
                    district=data.district,
                    commodity=data.active_crop,
                    days=30,
                    group_by="market",
                )

                mandi_str = json.dumps(insights, default=str, indent=2)
                logger.debug(
                    f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
                    f"MANDI_FETCH | Success for state={data.state}, crop={data.active_crop}"
                )
                return mandi_str
            finally:
                db.close()

        except Exception as e:
            logger.error(
                f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
                f"MANDI_FETCH | ERROR | {e}"
            )
            return (
                "Mandi price data could not be fetched right now due to a temporary error. "
                "Apologise to the farmer and say prices are temporarily unavailable. "
                "Do NOT make up price numbers."
            )

    # =========================================================================
    # RETURN TO ORCHESTRATOR
    # =========================================================================

    @function_tool(description=(
        "Call when the farmer's mandi/price question is answered and they want to "
        "ask about something else, or when they are done with market prices."
    ))
    async def done_with_mandi(
        self,
        context: RunContext[FarmerAdvisoryData],
    ) -> str:
        """Return control to the orchestrator."""
        data: FarmerAdvisoryData = context.userdata

        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"HANDOFF | → Orchestrator (done with mandi)"
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
