"""
Conversation Fillers
====================
Reusable, language-agnostic conversation fillers that mask LLM thinking latency.
Used via session.say() in on_user_turn_completed to create a natural, human feel.
These work across all agents (onboarding, advisory, etc.).
"""
import random

from core.config import logger

# Language-agnostic fillers that TTS renders as natural vocal sounds.
# These are universal across Hindi, Telugu, Kannada, Tamil, Bengali, etc.
FILLERS = [
    "Hmm",
    "Mm-hmm",
    "Hmm hmm",
]


def play_filler(session) -> None:
    """
    Fire-and-forget a conversation filler to mask LLM thinking latency.

    Uses session.say() with:
      - allow_interruptions=False: filler completes even if farmer speaks
      - add_to_chat_ctx=False: doesn't pollute conversation history

    IMPORTANT: Do NOT await this. The filler plays in parallel with LLM generation.
    """
    try:
        filler = random.choice(FILLERS)
        session.say(filler, allow_interruptions=False, add_to_chat_ctx=False)
        logger.debug(f"CORE | CONVERSATION_FILLERS | Played filler: '{filler}'")
    except Exception as e:
        # Fillers are non-critical — never let a filler error break the flow
        logger.debug(f"CORE | CONVERSATION_FILLERS | Error playing filler: {e}")
