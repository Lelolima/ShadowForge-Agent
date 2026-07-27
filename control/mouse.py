"""
============================================================
 NVIDIA ShadowForge Agent - Controle Stealth de Mouse
 Arquivo: control/mouse.py
============================================================
 Movimentos humanos-like com curvas Bézier, jitter,
 variação de velocidade e integração com detector UI.
============================================================
"""

from __future__ import annotations

import asyncio
import logging
import math
import random
from typing import Any

logger = logging.getLogger("shadowforge.control.mouse")


class StealthMouse:
    """Controle stealth de mouse com movimentos humanos.

    Usa curvas Bézier para movimentos naturais que não
    são detectáveis por anti-bot / behavior analysis.
    Inclui jitter, variação de velocidade e timing humano.
    """

    def __init__(
        self,
        velocidade_base: float = 0.5,
        variacao_velocidade: float = 0.15,
        bezier_pontos: int = 50,
        jitter_pixels: int = 3,
        clique_delay_range: tuple[float, float] = (0.05, 0.15),
    ) -> None:
        self.velocidade_base = velocidade_base
        self.variacao_velocidade = variacao_velocidade
        self.bezier_pontos = bezier_pontos
        self.jitter_pixels = jitter_pixels
        self.clique_delay_range = clique_delay_range
        self._pyautogui = None

    def _ensure_pyautogui(self) -> Any:
        """Lazy import do pyautogui."""
        if self._pyautogui is None:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True
                pyautogui.PAUSE = 0.0  # Controlamos timing manualmente
                self._pyautogui = pyautogui
            except ImportError:
                logger.warning("pyautogui não disponível")
        return self._pyautogui

    def _bezier_curve(
        self, inicio: tuple[int, int], fim: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """Gera pontos de uma curva Bézier cúbica entre dois pontos.

        Adiciona pontos de controle randômicos para simular
        movimento humano não-linear.
        """
        x0, y0 = inicio
        x3, y3 = fim

        # Distância para calibrar controle
        dist = math.sqrt((x3 - x0) ** 2 + (y3 - y0) ** 2)
        offset = dist * 0.3  # 30% da distância como desvio

        # Pontos de controle aleatórios
        x1 = x0 + random.uniform(-offset, offset)
        y1 = y0 + random.uniform(-offset, offset)
        x2 = x3 + random.uniform(-offset, offset)
        y2 = y3 + random.uniform(-offset, offset)

        pontos = []
        for i in range(self.bezier_pontos):
            t = i / (self.bezier_pontos - 1)

            # Bézier cúbica: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
            u = 1 - t
            x = u**3 * x0 + 3 * u**2 * t * x1 + 3 * u * t**2 * x2 + t**3 * x3
            y = u**3 * y0 + 3 * u**2 * t * y1 + 3 * u * t**2 * y2 + t**3 * y3

            # Jitter humano
            if 0 < i < self.bezier_pontos - 1:
                x += random.gauss(0, self.jitter_pixels * 0.5)
                y += random.gauss(0, self.jitter_pixels * 0.5)

            pontos.append((int(x), int(y)))

        return pontos

    async def mover_para(self, x: int, y: int, duracao: float | None = None) -> None:
        """Move mouse para posição com movimento humano.

        Args:
            x: Coordenada X alvo
            y: Coordenada Y alvo
            duracao: Duração em segundos (None = auto)
        """
        pag = self._ensure_pyautogui()
        if pag is None:
            return

        pos_atual = pag.position()
        duracao = duracao or self.velocidade_base + random.uniform(
            -self.variacao_velocidade, self.variacao_velocidade
        )
        duracao = max(0.1, duracao)

        # Gera caminho Bézier
        caminho = self._bezier_curve(pos_atual, (x, y))

        # Move ao longo do caminho com velocidade variável
        tempo_por_ponto = duracao / len(caminho)

        for i, (px, py) in enumerate(caminho):
            # Aceleração humana: mais lento no início e fim
            progresso = i / len(caminho)
            fator_vel = 1.0 - 0.5 * (2 * progresso - 1) ** 2  # Smoothstep

            delay = tempo_por_ponto / max(0.3, fator_vel)
            delay += random.gauss(0, delay * 0.05)  # Micro-variação

            pag.moveTo(px, py, _pause=False)
            await asyncio.sleep(max(0.001, delay))

    async def clicar(
        self,
        x: int,
        y: int,
        botao: str = "left",
        cliques: int = 1,
        mover: bool = True,
    ) -> None:
        """Clica em posição com timing humano.

        Args:
            x: Coordenada X
            y: Coordenada Y
            botao: "left", "right", "middle"
            cliques: Número de cliques (2 = double-click)
            mover: Se deve mover antes de clicar
        """
        pag = self._ensure_pyautogui()
        if pag is None:
            return

        if mover:
            await self.mover_para(x, y)

        # Delay humano antes do clique
        pre_delay = random.uniform(*self.clique_delay_range)
        await asyncio.sleep(pre_delay)

        for click_num in range(cliques):
            pag.mouseDown(x, y, botao, _pause=False)
            # Hold time humano
            hold_time = random.uniform(0.04, 0.12)
            await asyncio.sleep(hold_time)
            pag.mouseUp(x, y, botao, _pause=False)

            # Delay entre cliques (double-click)
            if click_num < cliques - 1:
                entre_cliques = random.uniform(0.05, 0.15)
                await asyncio.sleep(entre_cliques)

    async def clicar_elemento(self, elemento: Any) -> None:
        """Clica em um ElementoUI detectado pelo vision.

        Args:
            elemento: ElementoUI com centro e bbox
        """
        if hasattr(elemento, "centro"):
            cx, cy = elemento.centro
            # Jitter dentro do elemento
            jx = random.randint(-elemento.largura // 4, elemento.largura // 4)
            jy = random.randint(-elemento.altura // 4, elemento.altura // 4)
            await self.clicar(cx + jx, cy + jy)

    async def scroll(self, direcao: int = -3, pausa: float = 0.1) -> None:
        """Scroll com timing natural.

        Args:
            direcao: Negativo = scroll down, Positivo = scroll up
            pausa: Pausa entre scrolls
        """
        pag = self._ensure_pyautogui()
        if pag is None:
            return

        for _ in range(abs(direcao)):
            pag.scroll(direcao // abs(direcao), _pause=False)
            await asyncio.sleep(pausa + random.uniform(0, 0.05))

    async def arrastar(
        self, de: tuple[int, int], para: tuple[int, int], duracao: float = 0.8
    ) -> None:
        """Drag & drop com movimento suave."""
        pag = self._ensure_pyautogui()
        if pag is None:
            return

        await self.mover_para(*de)
        pag.mouseDown(_pause=False)
        await asyncio.sleep(random.uniform(0.05, 0.1))
        await self.mover_para(*para, duracao=duracao)
        await asyncio.sleep(random.uniform(0.05, 0.1))
        pag.mouseUp(_pause=False)
