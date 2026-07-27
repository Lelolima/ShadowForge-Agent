"""
NVIDIA ShadowForge - Reporting Subpackage
Gerador de relatórios profissionais de pentest.
"""

try:
    from hacker_tools.reporting.report_generator import ReportGenerator
except ImportError:
    ReportGenerator = None  # type: ignore[assignment,misc]

__all__ = ["ReportGenerator"]
