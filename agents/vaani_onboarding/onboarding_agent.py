"""
Vaani Onboarding Agent
======================
Orchestrating agent for farmer onboarding.
Delegates profile collection to CollectFarmerProfileTask and handles
post-completion messaging.

Also provides:
  - on_user_turn_completed: conversation fillers to mask LLM latency
  - tts_node: pronunciation correction scaffold

Architecture:
  VaaniOnboardingAgent.on_enter()
      → starts CollectFarmerProfileTask (awaits completion)
      → thanks the farmer
      → session ends naturally
"""
import asyncio
from typing import AsyncIterable, Optional

from livekit import rtc
from livekit.agents import Agent, ChatContext, ChatMessage, ModelSettings

from agents.vaani_onboarding.models.onboarding_data_model import FarmerOnboardingData
from agents.vaani_onboarding.tasks.collect_profile_task import CollectFarmerProfileTask
from agents.vaani_onboarding.prompts import COMPLETION_INSTRUCTION
from core.config import logger
from core.conversation_fillers import play_filler
from core.pronunciation import apply_pronunciation_fixes, PRONUNCIATION_MAP
from core.db.farmer_db import SessionLocal, upsert_farmer, add_farmer_crop

root_folder = "AGENTS | VAANI_ONBOARDING"
sub_file_path = "ONBOARDING_AGENT"


class VaaniOnboardingAgent(Agent):
    """
    Orchestrating agent for farmer onboarding.

    On enter:
      1. Starts CollectFarmerProfileTask — bounded conversation for data collection
      2. Awaits task completion (auto-completes when 5 required fields filled)
      3. Thanks the farmer and says goodbye

    Hooks:
      - on_user_turn_completed: plays a conversation filler to mask LLM latency
      - tts_node: applies pronunciation fixes (when map is populated)

    Session userdata: FarmerOnboardingData (pre-filled with farmer_id + phone)
    Instructions: Injected at construction time by the worker via build_agent_instructions()
    """

    def __init__(self, instructions: str):
        super().__init__(instructions=instructions)

    async def on_enter(self) -> None:
        """Start the onboarding task and handle completion."""
        try:
            data: FarmerOnboardingData = self.session.userdata
            logger.debug(
                f"{data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | ON_ENTER | Starting profile collection task"
            )

            # Start the bounded profile collection task
            # This awaits until all required fields are collected
            completed_data: FarmerOnboardingData = await CollectFarmerProfileTask(
                farmer_data=data,
                chat_ctx=self.chat_ctx,
            )

            logger.debug(
                f"{data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | ON_ENTER | Profile collection complete | "
                f"name={completed_data.farmer_name}, state={completed_data.state}, "
                f"district={completed_data.district}, crops={completed_data.primary_crops}, "
                f"language={completed_data.preferred_language}"
            )

            # Save farmer profile to RDS
            await asyncio.to_thread(self._save_farmer_to_db, completed_data)

            # Thank the farmer and say goodbye
            await self.session.generate_reply(instructions=COMPLETION_INSTRUCTION)

            logger.debug(
                f"{data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | ON_ENTER | Completion message sent"
            )

        except Exception as e:
            logger.error(f"{root_folder} | {sub_file_path} | ON_ENTER | ERROR | {e}")
            raise

    def _save_farmer_to_db(self, data: FarmerOnboardingData) -> None:
        """Save completed farmer profile to RDS. Runs in a thread (sync SQLAlchemy)."""
        db = SessionLocal()
        try:
            farmer = upsert_farmer(
                db,
                phone_number=data.farmer_phone_number,
                name=data.farmer_name,
                state=data.state,
                district=data.district,
                village=data.village,
                land_area_acres=data.land_size,
                irrigation_type=data.irrigation_type.value if data.irrigation_type else None,
                preferred_language=data.preferred_language.value if data.preferred_language else None,
                is_profile_complete=True,
            )
            if data.primary_crops:
                for crop_name in data.primary_crops:
                    add_farmer_crop(db, farmer_id=farmer.farmer_id, crop_name=crop_name)
            logger.info(
                f"{data.farmer_phone_number} | {root_folder} | {sub_file_path} | "
                f"DB_SAVE | farmer_id={farmer.farmer_id}"
            )
        except Exception as e:
            logger.error(f"{root_folder} | {sub_file_path} | DB_SAVE | ERROR | {e}")
        finally:
            db.close()

    async def on_user_turn_completed(
        self,
        turn_ctx: ChatContext,
        new_message: ChatMessage,
    ) -> None:
        """
        Play a conversation filler to mask LLM thinking latency.
        Fires before the LLM generates its response — the filler plays in parallel.
        """
        play_filler(self.session)

    async def tts_node(
        self,
        text: AsyncIterable[str],
        model_settings: ModelSettings,
    ) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        """
        Apply pronunciation corrections before TTS.
        Currently a no-op (empty PRONUNCIATION_MAP).
        Populate core/pronunciation.py from real call feedback.
        """
        if PRONUNCIATION_MAP:
            corrected_text = apply_pronunciation_fixes(text)
            async for frame in Agent.default.tts_node(self, corrected_text, model_settings):
                yield frame
        else:
            # No-op pass-through when map is empty
            async for frame in Agent.default.tts_node(self, text, model_settings):
                yield frame
