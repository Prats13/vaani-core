"""
Vaani Onboarding Agent
======================
Orchestrating agent for farmer onboarding.
Delegates profile collection to CollectFarmerProfileTask and handles
post-completion messaging.

Architecture:
  VaaniOnboardingAgent.on_enter()
      → starts CollectFarmerProfileTask (awaits completion)
      → thanks the farmer
      → session ends naturally
"""
from livekit.agents import Agent

from agents.vaani_onboarding.models.onboarding_data_model import FarmerOnboardingData
from agents.vaani_onboarding.tasks.collect_profile_task import CollectFarmerProfileTask
from agents.vaani_onboarding.prompts import COMPLETION_INSTRUCTION
from core.config import logger

root_folder = "AGENTS | VAANI_ONBOARDING"
sub_file_path = "ONBOARDING_AGENT"


class VaaniOnboardingAgent(Agent):
    """
    Orchestrating agent for farmer onboarding.

    On enter:
      1. Starts CollectFarmerProfileTask — bounded conversation for data collection
      2. Awaits task completion (auto-completes when 5 required fields filled)
      3. Thanks the farmer and says goodbye

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

            # Thank the farmer and say goodbye
            await self.session.generate_reply(instructions=COMPLETION_INSTRUCTION)

            logger.debug(
                f"{data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | ON_ENTER | Completion message sent"
            )

        except Exception as e:
            logger.error(f"{root_folder} | {sub_file_path} | ON_ENTER | ERROR | {e}")
            raise
