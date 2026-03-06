"""
Vaani Configuration Module
==========================
Centralized configuration for the Vaani project.
Uses Pydantic Settings for env management and standard Python logging.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from dataclasses import dataclass
from enum import Enum
import os
import logging

load_dotenv()

# ===========================================================================
# Logger Setup — standard Python logging
# ===========================================================================
os.makedirs(name="./logs", exist_ok=True)

logger = logging.getLogger("vaani")
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()

# File handler
file_handler = logging.FileHandler("./logs/vaani.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)

logger.propagate = False


# ===========================================================================
# Pydantic Settings
# ===========================================================================
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Security
    vaani_api_key: str = ""

    # LiveKit settings
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # AI Provider API Keys
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    eleven_labs_api_key: str | None = None
    deepgram_api_key: str | None = None
    cartesia_api_key: str | None = None
    sarvam_api_key: str | None = None

    # Agent Configuration
    assistant_name: str = "Vaani"

    external_livekit_url: str = "wss://localhost:7880"


settings = Settings()


# ===========================================================================
# Valid Model Configurations
# ===========================================================================

# STT Models
VALID_STT_MODELS = [
    # Deepgram
    "deepgram-nova-2-general",
    "deepgram-nova-2-conversationalai",
    "deepgram-nova-2-phonecall",
    "deepgram-nova-3",
    # OpenAI
    "openai-whisper-1",
    "openai-gpt-4o-transcribe",
    "openai-gpt-4o-mini-transcribe",
    # Sarvam
    "sarvam-saarika-2.5",
    "sarvam-saaras-2.5",
]

# LLM Models
VALID_LLM_MODELS = [
    # OpenAI
    "openai-gpt-4o-mini",
    "openai-gpt-4o",
    # Google
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-1.5-pro",
    # Realtime
    "gemini_2.5_flash_live_native_audio",
]

# TTS Models
VALID_TTS_MODELS = [
    # ElevenLabs
    "elevenlabs-eleven_multilingual_v2",
    "elevenlabs-eleven_turbo_v2_5",
    "elevenlabs-eleven_flash_v2_5",
    "elevenlabs-eleven_v3",
    # OpenAI
    "openai-tts-1",
    "openai-gpt-4o-mini-tts",
    # Cartesia
    "cartesia-sonic-2",
    "cartesia-sonic-3",
    "cartesia-sonic-turbo",
    # Sarvam
    "sarvam-bulbul",
]

VALID_AGENT_TYPES = ["farmer_advisory", "farmer_onboarding"]

default_model_config = {
    "agent_type": "farmer_advisory"
}


# ===========================================================================
# SIP Configuration Classes (Exotel)
# ===========================================================================
class SIPTransport(Enum):
    TCP = "tcp"
    TLS = "tls"
    UDP = "udp"


class CallDirection(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class ExotelRegion:
    name: str
    endpoint: str
    location: str
    port_tcp: int
    port_tls: int
