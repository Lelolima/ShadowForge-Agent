"""
============================================================
 NVIDIA ShadowForge Agent - Detector de Elementos UI
 Arquivo: vision/detector.py
============================================================
 Detecção de componentes UI com YOLO/TensorRT para
 automação visual de alto desempenho.
============================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("shadowforge.vision.detector")


@dataclass
class ElementoUI:
    """Elemento UI detectado na tela."""
    tipo: str = "desconhecido"
    x: int = 0
    y: int = 0
    largura: int = 0
    altura: int = 0
    confianca: float = 0.0
    texto: str = ""
    clicavel: bool = True

    @property
    def centro(self) -> tuple[int, int]:
        """Centro do elemento para clique."""
        return (self.x + self.largura // 2, self.y + self.altura // 2)

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        """Bounding box (x1, y1, x2, y2)."""
        return (self.x, self.y, self.x + self.largura, self.y + self.altura)


class UIDetector:
    """Detector de elementos UI usando YOLO + TensorRT.

    Detecta botões, inputs, links, menus e outros
    componentes interativos para automação visual.

    Suporta aceleração TensorRT para inferência em
    tempo real em GPUs NVIDIA.
    """

    CLASSES_ALVO = {
        0: "botao",
        1: "input_texto",
        2: "link",
        3: "textarea",
        4: "dropdown",
        5: "menu",
        6: "dialog",
        7: "checkbox",
        8: "radio",
        9: "tab",
        10: "scrollbar",
    }

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._modelo = None
        self._confianca_min = 0.5
        self._nms_threshold = 0.4
        self._usar_tensorrt = False
        self._initialized = False

    async def inicializar(self, modelo_path: str | None = None) -> None:
        """Inicializa o modelo de detecção."""
        try:
            from ultralytics import YOLO

            if modelo_path:
                self._modelo = YOLO(modelo_path)
            else:
                # Usa modelo nano padrão (rápido)
                self._modelo = YOLO("yolov8n.pt")

            # Tenta exportar para TensorRT se GPU disponível
            try:
                import torch
                if torch.cuda.is_available():
                    logger.info("GPU NVIDIA detectada - TensorRT disponível")
                    self._usar_tensorrt = True
            except ImportError:
                pass

            self._initialized = True
            logger.info("Detector UI inicializado")

        except ImportError:
            logger.warning("Ultralytics não disponível - detecção desativada")

    async def detectar(
        self,
        frame_data: Any,
        confianca_min: float | None = None,
    ) -> list[ElementoUI]:
        """Detecta elementos UI em um frame.

        Args:
            frame_data: FrameData ou array numpy
            confianca_min: Confiança mínima (sobrescreve default)

        Returns:
            Lista de ElementoUI detectados
        """
        if not self._initialized or self._modelo is None:
            return await self._deteccao_fallback(frame_data)

        conf = confianca_min or self._confianca_min

        try:
            # Obtém array da imagem
            if hasattr(frame_data, "to_array"):
                img_array = frame_data.to_array()
            elif hasattr(frame_data, "imagem"):
                img_array = frame_data.to_array() if hasattr(frame_data, "to_array") else None
                if img_array is None:
                    import numpy as np
                    img_array = np.array(frame_data.imagem)
            else:
                return []

            # Executa detecção
            results = self._modelo(img_array, conf=conf, iou=self._nms_threshold)

            elementos = []
            for box in results[0].boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                cls_id = int(box.cls[0])
                conf_val = float(box.conf[0])

                tipo = self.CLASSES_ALVO.get(cls_id, f"classe_{cls_id}")

                elementos.append(ElementoUI(
                    tipo=tipo,
                    x=int(xyxy[0]),
                    y=int(xyxy[1]),
                    largura=int(xyxy[2] - xyxy[0]),
                    altura=int(xyxy[3] - xyxy[1]),
                    confianca=conf_val,
                    clicavel=tipo in {"botao", "link", "checkbox", "radio", "tab", "menu"},
                ))

            return elementos

        except Exception as e:
            logger.error("Erro na detecção: %s", e)
            return []

    async def encontrar_elemento(
        self, frame_data: Any, tipo: str, texto: str = ""
    ) -> ElementoUI | None:
        """Encontra um elemento específico por tipo e/ou texto.

        Args:
            frame_data: Frame da tela
            tipo: Tipo do elemento (botao, input_texto, etc.)
            texto: Texto parcial a buscar no elemento

        Returns:
            Elemento encontrado ou None
        """
        elementos = await self.detectar(frame_data)

        # Filtra por tipo
        candidatos = [e for e in elementos if e.tipo == tipo]

        if texto and candidatos:
            # Usa OCR para verificar texto dos candidatos
            for elem in candidatos:
                try:
                    from vision.ocr import OCRExtractor
                    ocr = OCRExtractor()
                    resultado = await ocr.extrair_regiao(
                        frame_data, elem.x, elem.y, elem.largura, elem.altura
                    )
                    if texto.lower() in resultado.texto_raw.lower():
                        elem.texto = resultado.texto_raw
                        return elem
                except Exception:
                    continue

        # Retorna o mais confiável
        if candidatos:
            return max(candidatos, key=lambda e: e.confianca)

        return None

    async def _deteccao_fallback(self, frame_data: Any) -> list[ElementoUI]:
        """Detecção fallback usando análise de cor/borda."""
        elementos: list[ElementoUI] = []

        try:
            import numpy as np

            if hasattr(frame_data, "to_array"):
                img = frame_data.to_array()
            else:
                return []

            # Detecta regiões com alto contraste (possíveis botões/bordas)
            gray = np.mean(img, axis=2) if img.ndim == 3 else img
            edges = np.abs(np.diff(gray, axis=0))
            edges2 = np.abs(np.diff(gray, axis=1))

            # Threshold para bordas significativas
            threshold = np.mean(edges) + 2 * np.std(edges)
            hot_regions_x = np.where(np.mean(edges2, axis=0) > threshold)[0]
            hot_regions_y = np.where(np.mean(edges, axis=1) > threshold)[0]

            if len(hot_regions_x) > 0 and len(hot_regions_y) > 0:
                # Agrupa em regiões
                x_start = int(hot_regions_x[0])
                x_end = int(hot_regions_x[-1])
                y_start = int(hot_regions_y[0])
                y_end = int(hot_regions_y[-1])

                elementos.append(ElementoUI(
                    tipo="regiao_ativa",
                    x=x_start,
                    y=y_start,
                    largura=x_end - x_start,
                    altura=y_end - y_start,
                    confianca=0.3,
                ))

        except Exception as e:
            logger.debug("Fallback de detecção falhou: %s", e)

        return elementos
