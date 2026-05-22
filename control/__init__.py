"""
NVIDIA ShadowForge Agent - Control Package
Controle stealth de mouse, teclado, shell e anti-detecção.
"""

from control.shell import ResultadoComando, StealthShell

try:
    from control.mouse import StealthMouse
except ImportError:
    StealthMouse = None  # type: ignore[assignment,misc]

try:
    from control.keyboard import StealthKeyboard
except ImportError:
    StealthKeyboard = None  # type: ignore[assignment,misc]

try:
    from control.stealth import StealthManager
except ImportError:
    StealthManager = None  # type: ignore[assignment,misc]

__all__ = [
    "StealthMouse",
    "StealthKeyboard",
    "StealthShell",
    "ResultadoComando",
    "StealthManager",
]
