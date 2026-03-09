"""
Vaani Advisory — Government Schemes Agent (Stub)
==================================================
Specialist agent for government scheme queries.
No real data source yet — relies on LLM training knowledge about
Indian agricultural schemes (PM-Kisan, KCC, PMFBY, state subsidies).
"""
from typing import AsyncIterable, Optional

from livekit import rtc
from livekit.agents import Agent, ChatContext, ChatMessage, ModelSettings, function_tool, RunContext

from agents.vaani_advisory.models.advisory_data_model import FarmerAdvisoryData
from core.config import logger
from core.conversation_fillers import play_filler
from core.cta import send_cta
from core.pronunciation import apply_pronunciation_fixes, PRONUNCIATION_MAP

root_folder = "AGENTS | VAANI_ADVISORY"
sub_file_path = "GOVT_SCHEMES_AGENT"


class GovtSchemesAgent(Agent):
    """
    Specialist agent for government agricultural schemes (stub).

    No external data source — uses LLM knowledge to answer questions about
    PM-Kisan, KCC, PMFBY, state-level subsidies, and application guidance.

    On enter:
      1. Generates opening response based on farmer's state and crops

    Tools:
      - done_with_schemes: returns control to orchestrator
    """

    def __init__(self, instructions: str, farmer_data: FarmerAdvisoryData, chat_ctx=None):
        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )
        self._farmer_data = farmer_data

    async def on_enter(self) -> None:
        """Generate scheme advisory based on farmer profile."""
        data = self._farmer_data
        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"ON_ENTER | Schemes advisor for state={data.state}"
        )

        await self.session.generate_reply(
            instructions=(
                f"The farmer wants to learn about government agricultural schemes. "
                f"Based on their profile (state: {data.state or 'not specified'}, "
                f"crops: {', '.join(data.primary_crops) if data.primary_crops else 'various'}), "
                f"suggest 2-3 relevant schemes they might benefit from. "
                f"Explain eligibility in simple terms and where to apply. "
                f"Remember you are providing general guidance, not guaranteed eligibility."
            )
        )

        if data.is_web_session:
            await send_cta(self.session, "Kaunsi yojana ke baare mein aur jaanna chahte hain?",
                           ["PM-Kisan", "KCC Loan", "PMFBY Insurance", "Back to Home"])

    # =========================================================================
    # RETURN TO ORCHESTRATOR
    # =========================================================================

    @function_tool(description=(
        "Call when the farmer's scheme question is answered and they want to "
        "ask about something else, or when they are done with government schemes."
    ))
    async def done_with_schemes(
        self,
        context: RunContext[FarmerAdvisoryData],
    ) -> str:
        """Return control to the orchestrator."""
        data: FarmerAdvisoryData = context.userdata

        logger.debug(
            f"{data.farmer_phone} | {root_folder} | {sub_file_path} | "
            f"HANDOFF | → Orchestrator (done with schemes)"
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
