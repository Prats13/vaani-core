"""
Pronunciation Map
=================
Custom pronunciation rules for TTS via the tts_node override.
Add entries when you hear mispronunciations during real calls.

Usage: Override tts_node in your agent and call apply_pronunciation_fixes(text).
"""
import re
from typing import AsyncIterable


# Add entries as: "original_term": "phonetic_replacement"
# Focus on words your TTS provider gets wrong — this is provider-dependent.
#
# Examples (uncomment and adjust based on testing):
#   "bigha": "bee-gha",
#   "guntha": "goon-tha",
#   "kharif": "kha-reef",
#   "rabi": "rah-bee",
#   "VAANI": "Vaa-nee",

PRONUNCIATION_MAP: dict[str, str] = {
    # Populate from real call feedback
}


async def apply_pronunciation_fixes(
    text_stream: AsyncIterable[str],
) -> AsyncIterable[str]:
    """
    Apply pronunciation replacements to a text stream before TTS.

    Use inside a tts_node override:
        async for frame in Agent.default.tts_node(
            self, apply_pronunciation_fixes(text), model_settings
        ):
            yield frame
    """
    if not PRONUNCIATION_MAP:
        # No-op if map is empty — zero overhead
        async for chunk in text_stream:
            yield chunk
        return

    async for chunk in text_stream:
        modified = chunk
        for term, phonetic in PRONUNCIATION_MAP.items():
            modified = re.sub(
                rf"\b{re.escape(term)}\b",
                phonetic,
                modified,
                flags=re.IGNORECASE,
            )
        yield modified
