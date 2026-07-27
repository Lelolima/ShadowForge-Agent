"""
============================================================
 OODA Template - Padrão Template Method para o Loop OODA
 ============================================================
Implementa o padrão Template Method para definir a estrutura
do loop OODA (Observe-Orient-Decide-Act), permitindo que
subclasses definam o comportamento específico de cada fase.
"""

from __future__ import annotations

import abc
import asyncio
from typing import Any, Dict, List

from rich.console import Console

console = Console()


class ODDATemplate(abc.ABC):
    """Template abstrato para o loop OODA (Observe-Orient-Decide-Act)."""

    def __init__(self):
        self._iteracao = 0

    async def execute_ooda_cycle(self) -> None:
        """
        Template method que define o esqueleto do algoritmo OODA.
        Subclasses devem implementar os métodos abstratos para cada fase,
        mas não podem mudar a estrutura geral do algoritmo.
        """
        print(f"\n>> Ciclo OODA #{self._iteracao + 1}")

        # === OBSERVE ===
        observacoes = await self._observe()
        print(f"  [OBSERVE] {len(observacoes)} observações coletadas")
        await self._intervalo_observe()

        # === ORIENT ===
        orientacao = await self._orient(observacoes)
        fase_str = orientacao.get("fase_atual", "N/A")
        tecnicas = orientacao.get("tecnicas_sugeridas", [])
        print(f"  [ORIENT] Fase: {fase_str} | Técnicas RAG: {len(tecnicas)}")
        await self._intervalo_orient()

        # === DECIDE ===
        decisao = await self._decide(orientacao)
        acao = decisao.get("acao", "none")
        if acao == "etica_bloqueada":
            print(f"  [DECIDE] BLOQUEADA: {decisao.get('acao_original', '?')} - {decisao.get('motivo', '')}")
        else:
            print(f"  [DECIDE] Ação: {acao}")
        await self._intervalo_decide()

        # === ACT ===
        resultado = await self._act(decisao)
        sucesso = resultado.get("sucesso", False)
        status_icon = "✓" if sucesso else "✗"
        print(f"  [ACT] Resultado: {status_icon} | {acao}")

        # Registra na memória (se disponível)
        await self._pos_processamento(observacoes, decisao, resultado)

        self._iteracao += 1

    # Métodos abstratos que devem ser implementados pelas subclasses
    @abc.abstractmethod
    async def _observe(self) -> List[Dict[str, Any]]:
        """Fase OBSERVE: coleta informações do ambiente."""
        pass

    @abc.abstractmethod
    async def _orient(self, observacoes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fase ORIENT: analisa e contextualiza observações."""
        pass

    @abc.abstractmethod
    async def _decide(self, orientacao: Dict[str, Any]) -> Dict[str, Any]:
        """Fase DECIDE: escolhe a próxima ação."""
        pass

    @abc.abstractmethod
    async def _act(self, decisao: Dict[str, Any]) -> Dict[str, Any]:
        """Fase ACT: executa a ação decidida."""
        pass

    # Métodos de template que podem ser sobrescritos (hooks)
    async def _intervalo_observe(self) -> None:
        """Delay após a fase OBSERVE - pode ser sobrescrito."""
        await asyncio.sleep(0.1)  # Delay padrão, será substituído por config

    async def _intervalo_orient(self) -> None:
        """Delay após a fase ORIENT - pode ser sobrescrito."""
        await asyncio.sleep(0.1)  # Delay padrão, será substituído por config

    async def _intervalo_decide(self) -> None:
        """Delay após a fase DECIDE - pode ser sobrescrito."""
        await asyncio.sleep(0.1)  # Delay padrão, será substituído por config

    async def _pos_processamento(
        self,
        observacoes: List[Dict[str, Any]],
        decisao: Dict[str, Any],
        resultado: Dict[str, Any],
    ) -> None:
        """Processamento pós-ciclo - pode ser sobrescrito para logging, métricas, etc."""
        pass