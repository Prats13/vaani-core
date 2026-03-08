"""
Vaani CTA Protocol
==================
Helper for sending CTA (Call-To-Action) JSON messages to the frontend
via the LiveKit chat data channel.

Frontend expects this exact format:
{
  "vaani_cta": true,
  "message": "Helper text above buttons",
  "buttons": ["Button 1", "Button 2"]
}

Plain string messages are rendered as regular chat bubbles.
CTA messages are rendered as button pill groups.
"""
import json
import logging
from livekit.agents import AgentSession

logger = logging.getLogger("vaani")


async def send_cta(session: AgentSession, message: str, buttons: list[str]) -> None:
    """Send a CTA message to the frontend via LiveKit chat."""
    try:
        payload = json.dumps({
            "vaani_cta": True,
            "message": message,
            "buttons": buttons,
        })
        await session.chat.send_message(payload)
        logger.debug(f"CTA | SENT | message='{message}' | buttons={buttons}")
    except Exception as e:
        logger.error(f"CTA | SEND_ERROR | {e}")


async def send_text(session: AgentSession, message: str) -> None:
    """Send a plain text chat message to the frontend."""
    try:
        await session.chat.send_message(message)
        logger.debug(f"CTA | TEXT_SENT | message='{message}'")
    except Exception as e:
        logger.error(f"CTA | TEXT_SEND_ERROR | {e}")


# Predefined CTA payloads

HOME_BUTTONS = ["Know Your Crop", "Mandi Prices", "Weather", "Government Schemes"]


def home_cta(farmer_name: str) -> tuple[str, list[str]]:
    return (
        f"Namaste {farmer_name} ji! Aaj main aapki kya madad kar sakti hoon?",
        HOME_BUTTONS,
    )


def know_your_crop_cta() -> tuple[str, list[str]]:
    return (
        "Apni fasal ke baare mein kya jaanna chahte hain?",
        ["Ask Me Anything", "Back to Home"],
    )


def newsletter_cta() -> tuple[str, list[str]]:
    return (
        "Kaunsi jaankari chahiye aapko?",
        ["Local News", "National News", "Government Schemes", "Back to Home"],
    )
