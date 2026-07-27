"""
NVIDIA ShadowForge Agent - Vision Package
Captura de tela, OCR semântico, detecção UI e compreensão visual.
"""

try:
    from vision.screen import FrameData, ScreenCapture
except ImportError:
    FrameData = None  # type: ignore[assignment,misc]
    ScreenCapture = None  # type: ignore[assignment,misc]

try:
    from vision.ocr import OCRExtractor, ResultadoOCR
except ImportError:
    OCRExtractor = None  # type: ignore[assignment,misc]
    ResultadoOCR = None  # type: ignore[assignment,misc]

try:
    from vision.detector import ElementoUI, UIDetector
except ImportError:
    ElementoUI = None  # type: ignore[assignment,misc]
    UIDetector = None  # type: ignore[assignment,misc]

try:
    from vision.understanding import ScreenUnderstanding
except ImportError:
    ScreenUnderstanding = None  # type: ignore[assignment,misc]

__all__ = [
    "ScreenCapture",
    "FrameData",
    "OCRExtractor",
    "ResultadoOCR",
    "UIDetector",
    "ElementoUI",
    "ScreenUnderstanding",
]
