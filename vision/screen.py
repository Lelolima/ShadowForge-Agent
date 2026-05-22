"""
============================================================
 NVIDIA ShadowForge Agent - Captura de Tela
 Arquivo: vision/screen.py
============================================================
 Captura contínua e inteligente da tela com diff detection,
 região de interesse e integração DeepStream.
============================================================
"""

from __future__ import annotations

import asyncio
import io
import time
from typing import Any

import numpy as np
from PIL import Image

logger_mod = __import__("logging").getLogger("shadowforge.vision.screen")


class FrameData:
    """Dados de um frame capturado."""

    def __init__(self, imagem: Image.Image, timestamp: float, monitor: int = 0) -> None:
        self.imagem = imagem
        self.timestamp = timestamp
        self.monitor = monitor
        self.array: np.ndarray | None = None
        self.hash_diff: float = 0.0
        self.regiao_interesse: tuple[int, int, int, int] | None = None

    def to_array(self) -> np.ndarray:
        """Converte imagem para array numpy."""
        if self.array is None:
            self.array = np.array(self.imagem)
        return self.array

    def to_bytes(self, formato: str = "PNG", qualidade: int = 85) -> bytes:
        """Converte para bytes no formato especificado."""
        buf = io.BytesIO()
        kwargs = {"format": formato.upper()}
        if formato.upper() == "JPEG":
            kwargs["quality"] = qualidade
        self.imagem.save(buf, **kwargs)
        return buf.getvalue()

    def redimensionar(self, largura: int, altura: int) -> FrameData:
        """Redimensiona mantendo aspect ratio."""
        resized = self.imagem.resize((largura, altura), Image.Resampling.LANCZOS)
        novo = FrameData(resized, self.timestamp, self.monitor)
        return novo


class ScreenCapture:
    """Captura de tela contínua e inteligente.

    Usa mss para captura multi-monitor de alta performance.
    Suporta diff detection para processar apenas frames modificados,
    região de interesse para focar em áreas específicas e
    FPS adaptativo para otimizar recursos.
    """

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._running = False
        self._ultimo_frame: FrameData | None = None
        self._ultimo_array: np.ndarray | None = None
        self._frame_count = 0
        self._fps_atual = 0.0
        self._diff_threshold = 0.05
        self._monitor_id = 0
        self._fps_min = 1
        self._fps_max = 30
        self._formato = "PNG"
        self._qualidade_jpeg = 85

        if config:
            cap_config = getattr(config, "visao_captura", None)
            if cap_config:
                self._monitor_id = getattr(cap_config, "monitor", 0)
                self._fps_min = getattr(cap_config, "fps_min", 1)
                self._fps_max = getattr(cap_config, "fps_max", 30)
                self._formato = getattr(cap_config, "formato", "PNG")
                self._diff_threshold = getattr(cap_config, "diff_threshold", 0.05)
                self._qualidade_jpeg = getattr(cap_config, "qualidade_jpeg", 85)

    async def capturar(self, monitor: int | None = None) -> FrameData | None:
        """Captura um frame da tela.

        Args:
            monitor: ID do monitor (None = usar config padrão)

        Returns:
            FrameData com a imagem capturada ou None se falhar
        """
        try:
            import mss

            monitor_id = monitor if monitor is not None else self._monitor_id

            with mss.mss() as sct:
                monitors = sct.monitors
                if monitor_id >= len(monitors):
                    monitor_id = 0

                monitor_info = monitors[monitor_id + 1]  # mss usa índice 1-based
                screenshot = sct.grab(monitor_info)

                # Converte para PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                frame = FrameData(
                    imagem=img,
                    timestamp=time.time(),
                    monitor=monitor_id,
                )

                # Calcula diff se temos frame anterior
                if self._ultimo_array is not None:
                    current_array = frame.to_array()
                    diff = np.mean(np.abs(
                        current_array.astype(float) - self._ultimo_array.astype(float)
                    )) / 255.0
                    frame.hash_diff = diff

                    # Pula se mudança muito pequena
                    if diff < self._diff_threshold:
                        return None  # Frame sem mudança significativa

                self._ultimo_frame = frame
                self._ultimo_array = frame.to_array().copy()
                self._frame_count += 1

                return frame

        except ImportError:
            logger_mod.warning("mss não disponível, usando fallback PIL")
            return await self._captura_fallback_pil(monitor)
        except Exception as e:
            logger_mod.error("Erro na captura de tela: %s", e)
            return None

    async def _captura_fallback_pil(self, monitor: int | None = None) -> FrameData | None:
        """Fallback usando PIL ImageGrab."""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            return FrameData(imagem=img, timestamp=time.time(), monitor=monitor or 0)
        except Exception as e:
            logger_mod.error("Fallback PIL falhou: %s", e)
            return None

    async def capturar_regiao(self, x: int, y: int, w: int, h: int) -> FrameData | None:
        """Captura uma região específica da tela (ROI).

        Args:
            x: Coordenada X do canto superior esquerdo
            y: Coordenada Y do canto superior esquerdo
            w: Largura da região
            h: Altura da região
        """
        frame = await self.capturar()
        if frame is None:
            return None

        cortada = frame.imagem.crop((x, y, x + w, y + h))
        roi_frame = FrameData(imagem=cortada, timestamp=frame.timestamp, monitor=frame.monitor)
        roi_frame.regiao_interesse = (x, y, w, h)
        return roi_frame

    async def capturar_continuo(
        self,
        callback: Any,
        fps_alvo: int | None = None,
        apenas_diff: bool = True,
    ) -> None:
        """Captura contínua com callback para cada frame.

        Args:
            callback: Função async chamada para cada frame
            fps_alvo: FPS alvo (None = auto-adaptativo)
            apenas_diff: Processa apenas frames com mudanças
        """
        self._running = True
        fps = fps_alvo or self._fps_max
        intervalo = 1.0 / fps

        while self._running:
            inicio = time.time()

            frame = await self.capturar()

            if frame is not None and (not apenas_diff or frame.hash_diff >= self._diff_threshold):
                    try:
                        await callback(frame)
                    except Exception as e:
                        logger_mod.error("Erro no callback de frame: %s", e)

            # FPS adaptativo
            elapsed = time.time() - inicio
            sleep_time = max(0, intervalo - elapsed)

            # Ajusta FPS baseado na carga
            if elapsed > intervalo * 1.5:
                fps = max(self._fps_min, fps - 1)
            elif elapsed < intervalo * 0.5 and fps < self._fps_max:
                fps = min(self._fps_max, fps + 1)

            self._fps_atual = fps
            intervalo = 1.0 / fps

            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    def parar(self) -> None:
        """Para a captura contínua."""
        self._running = False

    @property
    def fps_atual(self) -> float:
        """FPS atual da captura."""
        return self._fps_atual

    @property
    def frame_count(self) -> int:
        """Número de frames capturados."""
        return self._frame_count
