"""
Vaani Onboarding — Collect Farmer Profile Task
================================================
AgentTask that bounds the conversation to farmer profile collection.
Uses unordered collection pattern: farmer can provide fields in any order.
Auto-completes when all 5 required fields are collected.

Required fields: farmer_name, state, district, primary_crops, preferred_language.
"""
from typing import Optional, List

from livekit.agents import AgentTask, function_tool, RunContext

from agents.vaani_onboarding.models.onboarding_data_model import (
    FarmerOnboardingData,
    IrrigationType,
    LandSizeUnit,
    PreferredLanguage,
)
from agents.vaani_onboarding.prompts import build_task_instructions, build_greeting_instruction
from core.config import logger

root_folder = "AGENTS | VAANI_ONBOARDING"
sub_file_path = "COLLECT_PROFILE_TASK"


class CollectFarmerProfileTask(AgentTask[FarmerOnboardingData]):
    """
    Bounded task for collecting a farmer's profile.

    Takes control of the session, collects data via @function_tool methods,
    and auto-completes when all required fields (farmer_name, state, district,
    primary_crops, preferred_language) are filled.

    Uses the unordered collection pattern — farmer can provide info in any order.
    """

    def __init__(self, farmer_data: FarmerOnboardingData, chat_ctx=None):
        super().__init__(
            instructions=build_task_instructions(farmer_data),
            chat_ctx=chat_ctx,
        )
        self._farmer_data = farmer_data

    async def on_enter(self) -> None:
        """Send greeting when the task starts."""
        try:
            greeting = build_greeting_instruction(self._farmer_data)
            await self.session.generate_reply(instructions=greeting)
            logger.debug(
                f"{self._farmer_data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | ON_ENTER | Greeting sent"
            )
        except Exception as e:
            logger.error(f"{root_folder} | {sub_file_path} | ON_ENTER | ERROR | {e}")
            raise

    # =========================================================================
    # TOOLS — Progressive data capture
    # =========================================================================

    @function_tool(description=(
        "Save the farmer's name once they have clearly stated it. "
        "Call this as soon as you hear or confirm their name."
    ))
    async def save_farmer_name(
        self,
        context: RunContext[FarmerOnboardingData],
        farmer_name: str,
    ) -> dict:
        """Save the farmer's name."""
        try:
            data: FarmerOnboardingData = context.userdata
            data.farmer_name = farmer_name.strip()
            logger.debug(
                f"{data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | SAVE_FARMER_NAME | {farmer_name}"
            )
            return self._check_and_respond(data, {"farmer_name": data.farmer_name})
        except Exception as e:
            logger.error(f"{root_folder} | {sub_file_path} | SAVE_FARMER_NAME | ERROR | {e}")
            return {"status": "error", "message": str(e)}

    @function_tool(description=(
        "Save the farmer's location. state and district are required. "
        "village is optional — save it if the farmer mentions it. "
        "Call this once the farmer has stated where their farm is."
    ))
    async def save_location(
        self,
        context: RunContext[FarmerOnboardingData],
        state: str,
        district: str,
        village: Optional[str] = None,
    ) -> dict:
        """Save farmer's location."""
        try:
            data: FarmerOnboardingData = context.userdata
            data.state = state.strip()
            data.district = district.strip()
            if village:
                data.village = village.strip()
            logger.debug(
                f"{data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | SAVE_LOCATION | {state}, {district}, {village}"
            )
            return self._check_and_respond(
                data,
                {"state": data.state, "district": data.district, "village": data.village},
            )
        except Exception as e:
            logger.error(f"{root_folder} | {sub_file_path} | SAVE_LOCATION | ERROR | {e}")
            return {"status": "error", "message": str(e)}

    @function_tool(description=(
        "Save the farmer's farm profile — land size and irrigation type. "
        "All fields are optional — save whatever the farmer provides. "
        "land_size_unit must be one of: acres, bigha, hectare, guntha, other. "
        "irrigation_type must be one of: irrigated, rainfed, mixed."
    ))
    async def save_farm_profile(
        self,
        context: RunContext[FarmerOnboardingData],
        land_size: Optional[float] = None,
        land_size_unit: Optional[str] = None,
        irrigation_type: Optional[str] = None,
    ) -> dict:
        """Save farm profile details."""
        try:
            data: FarmerOnboardingData = context.userdata
            if land_size is not None:
                data.land_size = land_size
            if land_size_unit:
                data.land_size_unit = LandSizeUnit(land_size_unit)
            if irrigation_type:
                data.irrigation_type = IrrigationType(irrigation_type)
            logger.debug(
                f"{data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | SAVE_FARM_PROFILE | size={land_size} {land_size_unit}, irrigation={irrigation_type}"
            )
            return self._check_and_respond(
                data,
                {"land_size": data.land_size, "land_size_unit": str(data.land_size_unit), "irrigation_type": str(data.irrigation_type)},
            )
        except ValueError as e:
            logger.error(f"{root_folder} | {sub_file_path} | SAVE_FARM_PROFILE | INVALID_VALUE | {e}")
            return {"status": "error", "message": f"Invalid value: {e}"}
        except Exception as e:
            logger.error(f"{root_folder} | {sub_file_path} | SAVE_FARM_PROFILE | ERROR | {e}")
            return {"status": "error", "message": str(e)}

    @function_tool(description=(
        "Save the crops the farmer grows. primary_crops is a list of crop names (at least one required). "
        "current_season_crop is what they are growing right now (optional). "
        "Call this once the farmer has named at least one crop."
    ))
    async def save_crops(
        self,
        context: RunContext[FarmerOnboardingData],
        primary_crops: List[str],
        current_season_crop: Optional[str] = None,
    ) -> dict:
        """Save crop information."""
        try:
            data: FarmerOnboardingData = context.userdata
            data.primary_crops = [c.strip() for c in primary_crops if c.strip()]
            if current_season_crop:
                data.current_season_crop = current_season_crop.strip()
            logger.debug(
                f"{data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | SAVE_CROPS | {primary_crops}, current={current_season_crop}"
            )
            return self._check_and_respond(
                data,
                {"primary_crops": data.primary_crops, "current_season_crop": data.current_season_crop},
            )
        except Exception as e:
            logger.error(f"{root_folder} | {sub_file_path} | SAVE_CROPS | ERROR | {e}")
            return {"status": "error", "message": str(e)}

    @function_tool(description=(
        "Save the farmer's preferred language. "
        "Must be one of: hindi, telugu, kannada, tamil, bengali, other. "
        "Infer this from the language the farmer has been speaking in, "
        "and confirm with them before saving."
    ))
    async def save_preferred_language(
        self,
        context: RunContext[FarmerOnboardingData],
        preferred_language: str,
    ) -> dict:
        """Save farmer's preferred language."""
        try:
            data: FarmerOnboardingData = context.userdata
            data.preferred_language = PreferredLanguage(preferred_language.lower())
            logger.debug(
                f"{data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | SAVE_PREFERRED_LANGUAGE | {preferred_language}"
            )
            return self._check_and_respond(
                data,
                {"preferred_language": str(data.preferred_language)},
            )
        except ValueError:
            logger.error(
                f"{root_folder} | {sub_file_path} | SAVE_PREFERRED_LANGUAGE | "
                f"INVALID_VALUE | {preferred_language}"
            )
            return {
                "status": "error",
                "message": f"Invalid language: {preferred_language}. Must be one of: hindi, telugu, kannada, tamil, bengali, other",
            }
        except Exception as e:
            logger.error(f"{root_folder} | {sub_file_path} | SAVE_PREFERRED_LANGUAGE | ERROR | {e}")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # COMPLETION CHECK
    # =========================================================================

    def _check_and_respond(self, data: FarmerOnboardingData, saved: dict) -> dict:
        """
        Check if all required fields are collected.
        If complete → call self.complete(data) to end the task.
        Otherwise → return missing_fields for the LLM to continue collecting.
        """
        missing = data.missing_fields()

        if not missing:
            logger.debug(
                f"{data.farmer_phone_number} | {root_folder} | "
                f"{sub_file_path} | PROFILE_COMPLETE | All required fields collected"
            )
            self.complete(data)
            return {
                "status": "complete",
                "message": "All required fields collected. Profile is complete!",
                "saved": saved,
            }

        return {
            "status": "saved",
            "saved": saved,
            "missing_fields": missing,
        }
