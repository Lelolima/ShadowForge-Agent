"""
NVIDIA ShadowForge Agent - Planning Package
Orquestrador de campanhas e RAG MITRE ATT&CK.
"""

from planning.orchestrator import CampaignOrchestrator, StatusTarefa, SubTarefa, TipoAgente

try:
    from planning.rag import MITRERAG
except ImportError:
    MITRERAG = None  # type: ignore[assignment,misc]

__all__ = [
    "CampaignOrchestrator",
    "SubTarefa",
    "StatusTarefa",
    "TipoAgente",
    "MITRERAG",
]
