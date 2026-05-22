"""
NVIDIA ShadowForge - Recon Subpackage
Scanners de reconhecimento e OSINT para pentest autorizado.
"""

from hacker_tools.recon.scanner import ResultadoHost, ResultadoPorta

try:
    from hacker_tools.recon.scanner import ReconScanner
except ImportError:
    ReconScanner = None  # type: ignore[assignment,misc]

try:
    from hacker_tools.recon.osint import OSINTGatherer
except ImportError:
    OSINTGatherer = None  # type: ignore[assignment,misc]

__all__ = [
    "ReconScanner",
    "ResultadoHost",
    "ResultadoPorta",
    "OSINTGatherer",
]
