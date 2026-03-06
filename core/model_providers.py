"""
Centralized Model Provider System
==================================
Single source of truth for all STT, LLM, TTS, and Realtime model configurations.
Supports: Deepgram, OpenAI, Gemini, Sarvam, ElevenLabs, Cartesia.
"""
from typing import Any

from google.genai.types import ActivityHandling, ThinkingConfig
from livekit.plugins import openai, deepgram, elevenlabs, google, sarvam
from livekit.plugins import cartesia
from livekit.plugins.silero import vad as silero_vad
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from core.config import settings, logger

root_folder = "CORE"
sub_file_path = "MODEL_PROVIDERS"


class ModelProviderError(Exception):
    """Raised when model provider configuration fails"""
    pass


class ModelProviders:
    """
    Centralized model provider factory for STT, LLM, TTS, and Realtime models.
    Single source of truth for all model configurations.
    """

    def __init__(self):
        self.settings = settings

    # ==================== STT PROVIDERS ====================

    def get_stt(self, config: str, **kwargs) -> Any:
        """Get Speech-to-Text provider based on configuration string."""
        try:
            match config:
                # Deepgram variants
                case "deepgram-nova-2-general":
                    return deepgram.STT(
                        model="nova-2-general",
                        api_key=self.settings.deepgram_api_key,
                        language="hi",
                        **kwargs
                    )

                case "deepgram-nova-2-conversationalai":
                    return deepgram.STT(
                        model="nova-2-conversationalai",
                        api_key=self.settings.deepgram_api_key,
                        detect_language=True,
                        **kwargs
                    )

                case "deepgram-nova-2-phonecall":
                    return deepgram.STT(
                        model="nova-2-phonecall",
                        api_key=self.settings.deepgram_api_key,
                        detect_language=True,
                        **kwargs
                    )

                case "deepgram-nova-3":
                    return deepgram.STT(
                        model="nova-3",
                        api_key=self.settings.deepgram_api_key,
                        language="hi",
                        **kwargs
                    )

                # OpenAI variants
                case "openai-whisper-1":
                    return openai.STT(
                        model="whisper-1",
                        api_key=self.settings.openai_api_key,
                        **kwargs
                    )

                case "openai-gpt-4o-transcribe":
                    return openai.STT(
                        model="gpt-4o-transcribe",
                        api_key=self.settings.openai_api_key,
                        **kwargs
                    )

                case "openai-gpt-4o-mini-transcribe":
                    return openai.STT(
                        model="gpt-4o-mini-transcribe",
                        api_key=self.settings.openai_api_key,
                        **kwargs
                    )

                # Sarvam variants (Hindi-optimized)
                case "sarvam-saarika-2.5":
                    return sarvam.STT(
                        api_key=self.settings.sarvam_api_key,
                        model="saarika:v2.5",
                        language="hi-IN",
                        high_vad_sensitivity=True,
                        sample_rate=8000,
                        **kwargs
                    )

                case "sarvam-saaras-2.5":
                    return sarvam.STT(
                        api_key=self.settings.sarvam_api_key,
                        model="saaras:v2.5",
                        language="hi-IN",
                        high_vad_sensitivity=True,
                        sample_rate=8000,
                        **kwargs
                    )

                # Default fallback
                case _:
                    logger.debug(f"[{sub_file_path}] Unknown STT config '{config}', falling back to sarvam-saarika-2.5")
                    return sarvam.STT(
                        api_key=self.settings.sarvam_api_key,
                        model="saarika:v2.5",
                        language="hi-IN",
                        high_vad_sensitivity=True,
                        sample_rate=8000,
                        **kwargs
                    )

        except Exception as e:
            raise ModelProviderError(f"Failed to create STT provider for config '{config}': {e}")

    # ==================== LLM PROVIDERS ====================

    def get_llm(self, config: str, temperature: float = 0.8, **kwargs) -> Any:
        """Get Large Language Model provider based on configuration string."""
        try:
            match config:
                # OpenAI variants
                case "openai-gpt-4o-mini":
                    return openai.LLM(
                        model="gpt-4o-mini",
                        api_key=self.settings.openai_api_key,
                        temperature=temperature,
                        **kwargs
                    )

                case "openai-gpt-4o":
                    return openai.LLM(
                        model="gpt-4o",
                        api_key=self.settings.openai_api_key,
                        temperature=temperature,
                        **kwargs
                    )

                # Google Gemini variants
                case "gemini-2.5-pro":
                    return google.LLM(
                        model="models/gemini-2.5-pro",
                        api_key=self.settings.gemini_api_key,
                        temperature=temperature,
                        **kwargs
                    )

                case "gemini-2.5-flash":
                    return google.LLM(
                        model="models/gemini-2.5-flash",
                        api_key=self.settings.gemini_api_key,
                        temperature=temperature,
                        **kwargs
                    )

                case "gemini-1.5-pro":
                    return google.LLM(
                        model="models/gemini-1.5-pro",
                        api_key=self.settings.gemini_api_key,
                        temperature=temperature,
                        **kwargs
                    )

                # Default fallback
                case _:
                    logger.debug(f"[{sub_file_path}] Unknown LLM config '{config}', falling back to gemini-2.5-flash")
                    return google.LLM(
                        model="models/gemini-2.5-flash",
                        api_key=self.settings.gemini_api_key,
                        temperature=temperature,
                        **kwargs
                    )

        except Exception as e:
            raise ModelProviderError(f"Failed to create LLM provider for config '{config}': {e}")

    # ==================== TTS PROVIDERS ====================

    def get_tts(self, config: str, **kwargs) -> Any:
        """Get Text-to-Speech provider based on configuration string."""
        try:
            match config:
                # ElevenLabs variants
                case "elevenlabs-eleven_multilingual_v2":
                    return elevenlabs.TTS(
                        api_key=self.settings.eleven_labs_api_key,
                        model="eleven_multilingual_v2",
                        **kwargs
                    )

                case "elevenlabs-eleven_turbo_v2_5":
                    return elevenlabs.TTS(
                        api_key=self.settings.eleven_labs_api_key,
                        model="eleven_turbo_v2_5",
                        **kwargs
                    )

                case "elevenlabs-eleven_flash_v2_5":
                    return elevenlabs.TTS(
                        api_key=self.settings.eleven_labs_api_key,
                        model="eleven_flash_v2_5",
                        **kwargs
                    )

                case "elevenlabs-eleven_v3":
                    return elevenlabs.TTS(
                        api_key=self.settings.eleven_labs_api_key,
                        model="eleven_v3",
                        **kwargs
                    )

                # OpenAI variants
                case "openai-tts-1":
                    return openai.TTS(
                        api_key=self.settings.openai_api_key,
                        model="tts-1",
                        voice="nova",
                        **kwargs
                    )

                case "openai-gpt-4o-mini-tts":
                    return openai.TTS(
                        api_key=self.settings.openai_api_key,
                        model="gpt-4o-mini-tts",
                        voice="nova",
                        **kwargs
                    )

                # Cartesia variants
                case "cartesia-sonic-2":
                    return cartesia.TTS(
                        model="sonic-2",
                        api_key=self.settings.cartesia_api_key,
                        **kwargs
                    )

                case "cartesia-sonic-3":
                    return cartesia.TTS(
                        model="sonic-3",
                        api_key=self.settings.cartesia_api_key,
                        speed=1.0,
                        **kwargs
                    )

                case "cartesia-sonic-turbo":
                    return cartesia.TTS(
                        model="sonic-turbo",
                        api_key=self.settings.cartesia_api_key,
                        **kwargs
                    )

                # Sarvam variants (Hindi-optimized)
                case "sarvam-bulbul":
                    return sarvam.TTS(
                        api_key=self.settings.sarvam_api_key,
                        target_language_code="hi-IN",
                        model="bulbul:v2",
                        speaker="anushka",
                        **kwargs
                    )

                # Default fallback
                case _:
                    logger.debug(f"[{sub_file_path}] Unknown TTS config '{config}', falling back to sarvam-bulbul")
                    return sarvam.TTS(
                        api_key=self.settings.sarvam_api_key,
                        target_language_code="hi-IN",
                        model="bulbul:v2",
                        speaker="anushka",
                        **kwargs
                    )

        except Exception as e:
            raise ModelProviderError(f"Failed to create TTS provider for config '{config}': {e}")

    # ==================== REALTIME PROVIDERS ====================

    def get_realtime_llm(self, config: str, **kwargs) -> Any:
        """Get Realtime Language Model provider (Gemini native audio)."""
        try:
            from google.genai.types import (
                RealtimeInputConfig, AutomaticActivityDetection,
                StartSensitivity, EndSensitivity, AudioTranscriptionConfig
            )

            match config:
                case "gemini_2.5_flash_live_native_audio":
                    return google.beta.realtime.RealtimeModel(
                        api_key=self.settings.gemini_api_key,
                        model="gemini-2.5-flash-native-audio-preview-09-2025",
                        voice="Kore",
                        temperature=0.9,
                        realtime_input_config=RealtimeInputConfig(
                            automatic_activity_detection=AutomaticActivityDetection(
                                disabled=False,
                                start_of_speech_sensitivity=StartSensitivity.START_SENSITIVITY_HIGH,
                                end_of_speech_sensitivity=EndSensitivity.END_SENSITIVITY_HIGH,
                                silence_duration_ms=200
                            ),
                            activity_handling=ActivityHandling.START_OF_ACTIVITY_INTERRUPTS,
                        ),
                        input_audio_transcription=AudioTranscriptionConfig(),
                        output_audio_transcription=AudioTranscriptionConfig(),
                        thinking_config=ThinkingConfig(
                            include_thoughts=False
                        ),
                        **kwargs
                    )

                case _:
                    logger.debug(f"[{sub_file_path}] Unknown realtime config '{config}', falling back to gemini native audio")
                    return google.beta.realtime.RealtimeModel(
                        api_key=self.settings.gemini_api_key,
                        model="gemini-2.5-flash-native-audio-preview-09-2025",
                        voice="Kore",
                        temperature=0.9,
                        **kwargs
                    )

        except Exception as e:
            raise ModelProviderError(f"Failed to create realtime LLM provider for config '{config}': {e}")

    # ==================== VAD / TURN DETECTION ====================

    def get_vad(self, **kwargs) -> Any:
        """Get Voice Activity Detection provider (Silero VAD)."""
        try:
            return silero_vad.VAD.load(**kwargs)
        except Exception as e:
            raise ModelProviderError(f"Failed to load Silero VAD: {e}")

    def get_turn_detection(self, **kwargs) -> Any:
        """Get Turn Detection (MultilingualModel) for conversation turn management."""
        try:
            return MultilingualModel(**kwargs)
        except Exception as e:
            raise ModelProviderError(f"Failed to load turn detection: {e}")


model_providers = ModelProviders()
