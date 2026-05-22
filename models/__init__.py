"""
NVIDIA ShadowForge Agent - Models Package
NIM Client, multimodal, prompts e embeddings.
"""

from models.prompts import PromptManager

try:
    from models.nim_client import NIMClient
except ImportError:
    NIMClient = None  # type: ignore[assignment,misc]

try:
    from models.multimodal import NemotronVision
except ImportError:
    NemotronVision = None  # type: ignore[assignment,misc]

try:
    from models.embeddings import NVIDIAEmbeddings
except ImportError:
    NVIDIAEmbeddings = None  # type: ignore[assignment,misc]

__all__ = [
    "NIMClient",
    "NemotronVision",
    "PromptManager",
    "NVIDIAEmbeddings",
]
