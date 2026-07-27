"""
NVIDIA ShadowForge Agent - Speech Package
ASR, TTS, interface de voz e utilitários de áudio via NVIDIA Riva.
"""

try:
    from speech.voice_interface import VoiceInterface
except ImportError:
    VoiceInterface = None  # type: ignore[assignment,misc]

try:
    from speech.asr import RivaASR, TranscricaoASR
except ImportError:
    RivaASR = None  # type: ignore[assignment,misc]
    TranscricaoASR = None  # type: ignore[assignment,misc]

try:
    from speech.tts import RivaTTS
except ImportError:
    RivaTTS = None  # type: ignore[assignment,misc]

try:
    from speech.audio_utils import AudioConfig
except ImportError:
    AudioConfig = None  # type: ignore[assignment,misc]

__all__ = [
    "VoiceInterface",
    "RivaASR",
    "TranscricaoASR",
    "RivaTTS",
    "AudioConfig",
]
