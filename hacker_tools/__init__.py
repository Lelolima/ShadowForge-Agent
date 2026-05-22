"""
NVIDIA ShadowForge - Security Testing Tools.

Ferramentas de pentest, exploit generation, scanners e reporting.
TODAS as ações verificam autorização antes de executar.
"""

try:
    from hacker_tools.recon import OSINTGatherer, ReconScanner
except ImportError:
    ReconScanner = None  # type: ignore[assignment,misc]
    OSINTGatherer = None  # type: ignore[assignment,misc]

try:
    from hacker_tools.exploit import NetworkExploiter, WebExploiter
except ImportError:
    WebExploiter = None  # type: ignore[assignment,misc]
    NetworkExploiter = None  # type: ignore[assignment,misc]

try:
    from hacker_tools.post_exploitation import PostExploitation
except ImportError:
    PostExploitation = None  # type: ignore[assignment,misc]

try:
    from hacker_tools.reporting import ReportGenerator
except ImportError:
    ReportGenerator = None  # type: ignore[assignment,misc]

__all__ = [
    "ReconScanner",
    "OSINTGatherer",
    "WebExploiter",
    "NetworkExploiter",
    "PostExploitation",
    "ReportGenerator",
]
