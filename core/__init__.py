"""
NVIDIA ShadowForge Agent - Core Package
Motor agentic, loops OODA, configuração, estado e memória.
"""

__version__ = "1.1.0"
__codinome__ = "SH4D0WF0RG3"

from core.config import ModoOperacao, ShadowForgeConfig
from core.memory import MemoriaCurtoPrazo, MemoriaLongoPrazo
from core.state import EstadoAgente, FaseOperacao, Severidade, TipoVulnerabilidade
from core.event_bus import EventBus, EventoShadowForge, TipoEvento, PrioridadeEvento
from core.plugins import PluginManager, ShadowForgePlugin, PluginInfo

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
    "MemoriaLongoPrazo",
    "EventBus",
    "EventoShadowForge",
    "TipoEvento",
    "PrioridadeEvento",
    "PluginManager",
    "ShadowForgePlugin",
    "PluginInfo",
]
