"""
============================================================
 NVIDIA ShadowForge Agent - Controle Stealth de Teclado
 Arquivo: control/keyboard.py
============================================================
 Digitação humana com delay variável, simulação de erros,
 atalhos e integração com ferramentas de segurança.
============================================================
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

logger = logging.getLogger("shadowforge.control.keyboard")


class StealthKeyboard:
    """Controle stealth de teclado com digitação humana.

    Simula delay variável entre teclas, erros de digitação
    ocasionais com correção automática, e suporte a
    atalhos de ferramentas de pentest.
    """

    # Atalhos comuns de ferramentas de segurança
    ATALHOS_FERRAMENTAS = {
        "burp_forward": ["ctrl", "right"],
        "burp_drop": ["ctrl", "d"],
        "terminal_new_tab": ["ctrl", "shift", "t"],
        "terminal_close_tab": ["ctrl", "shift", "w"],
        "terminal_copy": ["ctrl", "shift", "c"],
        "terminal_paste": ["ctrl", "shift", "v"],
        "browser_devtools": ["ctrl", "shift", "i"],
        "browser_refresh": ["ctrl", "f5"],
        "ide_search": ["ctrl", "shift", "f"],
        "ide_goto": ["ctrl", "g"],
    }

    def __init__(
        self,
        dig_delay_range: tuple[float, float] = (0.03, 0.08),
        erro_probabilidade: float = 0.02,
        erro_correcao_range: tuple[float, float] = (0.1, 0.3),
    ) -> None:
        self.dig_delay_range = dig_delay_range
        self.erro_probabilidade = erro_probabilidade
        self.erro_correcao_range = erro_correcao_range
        self._pyautogui = None

    def _ensure_pyautogui(self) -> Any:
        if self._pyautogui is None:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True
                pyautogui.PAUSE = 0.0
                self._pyautogui = pyautogui
            except ImportError:
                logger.warning("pyautogui não disponível")
        return self._pyautogui

    async def digitar(self, texto: str, delay: float | None = None) -> None:
        """Digita texto com timing humano e erros simulados.

        Args:
            texto: Texto a digitar
            delay: Delay base entre teclas (None = auto variável)
        """
        pag = self._ensure_pyautogui()
        if pag is None:
            return

        for _i, char in enumerate(texto):
            # Simula erro de digitação
            if random.random() < self.erro_probabilidade and char.isalpha():
                # Digita caractere errado
                char_errado = self._caractere_proximo(char)
                pag.press(char_errado, _pause=False)
                await asyncio.sleep(random.uniform(*self.erro_correcao_range))

                # Corrige
                pag.press("backspace", _pause=False)
                await asyncio.sleep(random.uniform(0.02, 0.06))

            # Digita caractere correto
            pag.press(char, _pause=False)

            # Delay variável entre teclas
            d = delay or random.uniform(*self.dig_delay_range)
            # Pausas mais longas em pontuação e espaços
            if char in ".;:,!?":
                d *= random.uniform(2.0, 4.0)
            elif char == " ":
                d *= random.uniform(1.2, 1.8)

            await asyncio.sleep(d)

    def _caractere_proximo(self, char: str) -> str:
        """Retorna um caractere próximo no teclado QWERTY."""
        teclado = {
            "a": "sq", "b": "vn", "c": "xv", "d": "sf", "e": "wr",
            "f": "dg", "g": "fh", "h": "gj", "i": "uo", "j": "hk",
            "k": "jl", "l": "k;", "m": "n,", "n": "bm", "o": "ip",
            "p": "o[", "q": "wa", "r": "et", "s": "ad", "t": "ry",
            "u": "yi", "v": "cb", "w": "qe", "x": "zc", "y": "tu",
            "z": "xa",
        }
        vizinhos = teclado.get(char.lower(), char)
        return random.choice(vizinhos)

    async def atalho(self, nome: str, personalizado: list[str] | None = None) -> None:
        """Executa um atalho de teclado.

        Args:
            nome: Nome do atalho predefinido ou lista de teclas
            personalizado: Lista customizada de teclas
        """
        pag = self._ensure_pyautogui()
        if pag is None:
            return

        teclas = personalizado or self.ATALHOS_FERRAMENTAS.get(nome)
        if teclas is None:
            logger.warning("Atalho desconhecido: %s", nome)
            return

        # Pressiona em sequência com micro-delay
        for tecla in teclas:
            pag.keyDown(tecla, _pause=False)
            await asyncio.sleep(random.uniform(0.01, 0.03))

        # Solta em ordem reversa
        for tecla in reversed(teclas):
            pag.keyUp(tecla, _pause=False)
            await asyncio.sleep(random.uniform(0.01, 0.02))

    async def executar_comando(self, comando: str) -> None:
        """Digita e executa comando no terminal.

        Args:
            comando: Comando shell para executar
        """
        await self.digitar(comando)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await self.atalho("enter", personalizado=["enter"])

    async def colar(self, texto: str) -> None:
        """Cola texto via clipboard (mais rápido que digitar para textos longos)."""
        try:
            import pyperclip
            pyperclip.copy(texto)
            await self.atalho("ctrl_v", personalizado=["ctrl", "v"])
        except ImportError:
            # Fallback: digita diretamente
            await self.digitar(texto)
