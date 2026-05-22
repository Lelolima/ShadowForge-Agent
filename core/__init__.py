"""
NVIDIA ShadowForge Agent - Core Package
Motor agentic, loops OODA, configuração, estado e memória.
"""

__version__ = "1.0.0"
__codinome__ = "SH4D0WF0RG3"

from core.config import ModoOperacao, ShadowForgeConfig
from core.memory import MemoriaCurtoPrazo, MemoriLongoPrazo
from core.state import EstadoAgente, FaseOperacao, Severidade, TipoVulnerabilidade

try:
    from core.agent import ShadowForgeAgent
except ImportError:
    ShadowForgeAgent = None  # type: ignore[assignment,misc]

__all__ = [
    "ShadowForgeAgent",
    "ShadowForgeConfig",
    "ModoOperacao",
    "EstadoAgente",
    "FaseOperacao",
    "TipoVulnerabilidade",
    "Severidade",
    "MemoriaCurtoPrazo",
    "MemoriLongoPrazo",
]
