"""
============================================================
 NVIDIA ShadowForge Agent - Orquestrador de Campanhas
 Arquivo: planning/orchestrator.py
============================================================
 Decomposição de objetivos, multi-agent coordination,
 dependency management, paralelização e failure recovery.
============================================================
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.config import ShadowForgeConfig

logger = logging.getLogger("shadowforge.planning.orchestrator")


class StatusTarefa(str, Enum):
    """Status de uma subtarefa."""
    PENDENTE = "pendente"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDA = "concluido"
    FALHOU = "falhou"
    BLOQUEADA = "bloqueada"


class TipoAgente(str, Enum):
    """Tipos de sub-agentes especializados."""
    RECON = "recon_agent"
    EXPLOIT = "exploit_agent"
    REPORT = "report_agent"
    VISION = "vision_agent"
    COORDINATOR = "coordinator"


@dataclass
class SubTarefa:
    """Uma subtarefa decomposta do objetivo principal."""
    id: str = ""
    titulo: str = ""
    descricao: str = ""
    tipo_agente: TipoAgente = TipoAgente.COORDINATOR
    dependencias: list[str] = field(default_factory=list)
    status: StatusTarefa = StatusTarefa.PENDENTE
    resultado: dict[str, Any] = field(default_factory=dict)
    prioridade: int = 5
    retry_count: int = 0
    max_retries: int = 3
    timestamp_inicio: str | None = None
    timestamp_fim: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"TASK-{uuid.uuid4().hex[:8]}"

    @property
    def duracao_s(self) -> float | None:
        """Duração da tarefa em segundos."""
        if self.timestamp_inicio and self.timestamp_fim:
            inicio = datetime.fromisoformat(self.timestamp_inicio)
            fim = datetime.fromisoformat(self.timestamp_fim)
            return (fim - inicio).total_seconds()
        return None


class CampaignOrchestrator:
    """Orquestrador de campanhas de pentest multi-agente.

    Recebe objetivos de alto nível ("comprometa esta máq. de teste com permissão"),
    decompõe em subtarefas, gerencia dependências e coordena
    sub-agentes especializados em paralelo.

    Features:
    - Decomposição hierárquica de objetivos
    - Multi-agent coordination (recon, exploit, report)
    - Dependency management entre fases
    - Paralelização de tarefas independentes
    - Failure recovery com retry e backoff
    - Progress tracking em tempo real
    """

    # Templates de decomposição por tipo de objetivo
    TEMPLATES_DECOMPOSICAO = {
        "pentest_completo": [
            {"titulo": "Reconhecimento Passivo", "tipo": TipoAgente.RECON, "dependencias": [], "prioridade": 1},
            {"titulo": "Reconhecimento Ativo", "tipo": TipoAgente.RECON, "dependencias": ["Reconhecimento Passivo"], "prioridade": 2},
            {"titulo": "Scanning de Portas", "tipo": TipoAgente.RECON, "dependencias": ["Reconhecimento Ativo"], "prioridade": 2},
            {"titulo": "Enumeration de Serviços", "tipo": TipoAgente.RECON, "dependencias": ["Scanning de Portas"], "prioridade": 3},
            {"titulo": "Análise de Vulnerabilidades", "tipo": TipoAgente.EXPLOIT, "dependencias": ["Enumeration de Serviços"], "prioridade": 3},
            {"titulo": "Geração de PoCs", "tipo": TipoAgente.EXPLOIT, "dependencias": ["Análise de Vulnerabilidades"], "prioridade": 4},
            {"titulo": "Validação Visual de Exploits", "tipo": TipoAgente.VISION, "dependencias": ["Geração de PoCs"], "prioridade": 4},
            {"titulo": "Análise Pós-Exploração", "tipo": TipoAgente.EXPLOIT, "dependencias": ["Validação Visual de Exploits"], "prioridade": 5},
            {"titulo": "Geração de Relatório", "tipo": TipoAgente.REPORT, "dependencias": ["Análise Pós-Exploração"], "prioridade": 5},
        ],
        "recon_only": [
            {"titulo": "Reconhecimento Passivo", "tipo": TipoAgente.RECON, "dependencias": [], "prioridade": 1},
            {"titulo": "Reconhecimento Ativo", "tipo": TipoAgente.RECON, "dependencias": ["Reconhecimento Passivo"], "prioridade": 2},
            {"titulo": "Scanning de Portas", "tipo": TipoAgente.RECON, "dependencias": ["Reconhecimento Ativo"], "prioridade": 2},
            {"titulo": "Enumeration de Serviços", "tipo": TipoAgente.RECON, "dependencias": ["Scanning de Portas"], "prioridade": 3},
        ],
        "bug_bounty": [
            {"titulo": "Reconhecimento de Superfície", "tipo": TipoAgente.RECON, "dependencias": [], "prioridade": 1},
            {"titulo": "Fuzzing de Endpoints", "tipo": TipoAgente.EXPLOIT, "dependencias": ["Reconhecimento de Superfície"], "prioridade": 2},
            {"titulo": "Teste de Vulnerabilidades Web", "tipo": TipoAgente.EXPLOIT, "dependencias": ["Fuzzing de Endpoints"], "prioridade": 3},
            {"titulo": "Geração de PoCs para Bug Bounty", "tipo": TipoAgente.EXPLOIT, "dependencias": ["Teste de Vulnerabilidades Web"], "prioridade": 4},
            {"titulo": "Relatório Bug Bounty", "tipo": TipoAgente.REPORT, "dependencias": ["Geração de PoCs para Bug Bounty"], "prioridade": 5},
        ],
    }

    def __init__(self, config: ShadowForgeConfig | None = None) -> None:
        self._config = config
        self._tarefas: list[SubTarefa] = []
        self._resultado_global: dict[str, Any] = {}
        self._callbacks_progresso: list[Callable] = []
        self._running = False

    def decompor_objetivo(self, objetivo: str, tipo_campanha: str = "pentest_completo") -> list[SubTarefa]:
        """Decompõe objetivo de alto nível em subtarefas.

        Args:
            objetivo: Objetivo textual ("comprometa máquina X")
            tipo_campanha: Template de decomposição

        Returns:
            Lista de SubTarefas com dependências
        """
        template = self.TEMPLATES_DECOMPOSICAO.get(tipo_campanha, self.TEMPLATES_DECOMPOSICAO["pentest_completo"])

        # Cria tarefas a partir do template
        titulo_para_id: dict[str, str] = {}
        tarefas = []

        for item in template:
            tarefa = SubTarefa(
                titulo=item["titulo"],
                descricao=f"Subtarefa de '{objetivo}': {item['titulo']}",
                tipo_agente=item["tipo"],
                dependencias=[],  # Resolve depois
                prioridade=item["prioridade"],
            )
            titulo_para_id[item["titulo"]] = tarefa.id
            tarefas.append(tarefa)

        # Resolve dependências (nomes → IDs)
        for tarefa, item in zip(tarefas, template, strict=True):
            tarefa.dependencias = [
                titulo_para_id.get(dep, "")
                for dep in item["dependencias"]
                if dep in titulo_para_id
            ]

        self._tarefas = tarefas
        logger.info("Objetivo decomposto: %d subtarefas", len(tarefas))

        return tarefas

    async def executar_campanha(self, estado: Any) -> dict[str, Any]:
        """Executa campanha completa com orquestração.

        Args:
            estado: EstadoAgente para tracking

        Returns:
            Resultado global da campanha
        """
        self._running = True
        logger.info("Iniciando orquestração de campanha...")

        while self._running:
            # Encontra tarefas prontas (sem dependências pendentes)
            prontas = self._tarefas_prontas()

            if not prontas:
                # Verifica se todas completaram ou se travou
                all_done = all(t.status in (StatusTarefa.CONCLUIDA, StatusTarefa.FALHOU) for t in self._tarefas)
                if all_done:
                    break
                # Deadlock recovery: verifica se há tarefas bloqueadas
                bloqueadas = [t for t in self._tarefas if t.status == StatusTarefa.BLOQUEADA]
                if bloqueadas:
                    logger.warning("Deadlock detectado, desbloqueando tarefa: %s", bloqueadas[0].titulo)
                    bloqueadas[0].status = StatusTarefa.PENDENTE
                else:
                    await asyncio.sleep(1.0)
                continue

            # Executa tarefas prontas em paralelo (até 3 simultâneas)
            batches = [prontas[i:i+3] for i in range(0, len(prontas), 3)]

            for batch in batches:
                coroutines = [self._executar_tarefa(t, estado) for t in batch]
                await asyncio.gather(*coroutines, return_exceptions=True)

        # Compila resultado
        resultado = self._compilar_resultado()
        self._running = False

        logger.info("Campanha orquestrada: %d/%d tarefas concluídas",
                     sum(1 for t in self._tarefas if t.status == StatusTarefa.CONCLUIDA),
                     len(self._tarefas))

        return resultado

    def _tarefas_prontas(self) -> list[SubTarefa]:
        """Retorna tarefas cujas dependências foram satisfeitas."""
        concluidas_ids = {t.id for t in self._tarefas if t.status == StatusTarefa.CONCLUIDA}

        prontas = []
        for tarefa in self._tarefas:
            if tarefa.status != StatusTarefa.PENDENTE:
                continue
            # Todas dependências satisfeitas?
            deps_ok = all(dep_id in concluidas_ids for dep_id in tarefa.dependencias)
            if deps_ok:
                prontas.append(tarefa)

        return sorted(prontas, key=lambda t: t.prioridade)

    async def _executar_tarefa(self, tarefa: SubTarefa, estado: Any) -> None:
        """Executa uma subtarefa com retry."""
        tarefa.status = StatusTarefa.EM_EXECUCAO
        tarefa.timestamp_inicio = datetime.now().isoformat()

        # Notifica progresso
        for cb in self._callbacks_progresso:
            with contextlib.suppress(Exception):
                cb(tarefa.id, tarefa.titulo, tarefa.status.value)

        try:
            # Delega execução baseado no tipo de agente
            if tarefa.tipo_agente == TipoAgente.RECON:
                resultado = await self._executar_recon(tarefa, estado)
            elif tarefa.tipo_agente == TipoAgente.EXPLOIT:
                resultado = await self._executar_exploit(tarefa, estado)
            elif tarefa.tipo_agente == TipoAgente.REPORT:
                resultado = await self._executar_report(tarefa, estado)
            elif tarefa.tipo_agente == TipoAgente.VISION:
                resultado = await self._executar_vision(tarefa, estado)
            else:
                resultado = {"status": "skip", "motivo": "tipo não implementado"}

            tarefa.resultado = resultado
            tarefa.status = StatusTarefa.CONCLUIDA
            tarefa.timestamp_fim = datetime.now().isoformat()

            logger.info("[OK] %s (%.1fs)", tarefa.titulo, tarefa.duracao_s or 0)

        except Exception as e:
            tarefa.retry_count += 1

            if tarefa.retry_count < tarefa.max_retries:
                # Retry com backoff
                backoff = 2 ** tarefa.retry_count
                logger.warning("[RETRY] %s (tentativa %d, backoff %ds): %s",
                              tarefa.titulo, tarefa.retry_count, backoff, e)
                await asyncio.sleep(backoff)
                tarefa.status = StatusTarefa.PENDENTE
            else:
                tarefa.status = StatusTarefa.FALHOU
                tarefa.resultado = {"erro": str(e)}
                tarefa.timestamp_fim = datetime.now().isoformat()
                logger.error("[FALHA] %s após %d tentativas: %s", tarefa.titulo, tarefa.max_retries, e)

    async def _executar_recon(self, tarefa: SubTarefa, estado: Any) -> dict[str, Any]:
        """Delega tarefa de reconhecimento."""
        logger.info("[RECON] Executando: %s", tarefa.titulo)
        # Em integração real, chamaria hacker_tools.recon
        await asyncio.sleep(0.5)  # Simula execução
        return {"status": "simulado", "tarefa": tarefa.titulo}

    async def _executar_exploit(self, tarefa: SubTarefa, estado: Any) -> dict[str, Any]:
        """Delega tarefa de exploração."""
        logger.info("[EXPLOIT] Executando: %s", tarefa.titulo)
        await asyncio.sleep(0.5)
        return {"status": "simulado", "tarefa": tarefa.titulo}

    async def _executar_report(self, tarefa: SubTarefa, estado: Any) -> dict[str, Any]:
        """Delega tarefa de relatório."""
        logger.info("[REPORT] Executando: %s", tarefa.titulo)
        await asyncio.sleep(0.3)
        return {"status": "simulado", "tarefa": tarefa.titulo}

    async def _executar_vision(self, tarefa: SubTarefa, estado: Any) -> dict[str, Any]:
        """Delega tarefa de visão."""
        logger.info("[VISION] Executando: %s", tarefa.titulo)
        await asyncio.sleep(0.3)
        return {"status": "simulado", "tarefa": tarefa.titulo}

    def _compilar_resultado(self) -> dict[str, Any]:
        """Compila resultado global de todas as tarefas."""
        return {
            "total_tarefas": len(self._tarefas),
            "concluidas": sum(1 for t in self._tarefas if t.status == StatusTarefa.CONCLUIDA),
            "falharam": sum(1 for t in self._tarefas if t.status == StatusTarefa.FALHOU),
            "duracao_total_s": sum(t.duracao_s or 0 for t in self._tarefas),
            "tarefas": [
                {
                    "id": t.id,
                    "titulo": t.titulo,
                    "status": t.status.value,
                    "tipo_agente": t.tipo_agente.value,
                    "duracao_s": t.duracao_s,
                    "resultado": t.resultado,
                }
                for t in self._tarefas
            ],
        }

    def recuperar_falha(self, tarefa: SubTarefa, erro: str) -> dict[str, Any]:
        """Analisa falha e sugere ação de recovery.

        Args:
            tarefa: Tarefa que falhou
            erro: Mensagem de erro

        Returns:
            Dicionário com ação de recovery sugerida
        """
        acoes_recovery = {
            "timeout": {"acao": "retry_com_timeout_maior", "novo_timeout": 600},
            "connection_refused": {"acao": "verificar_alvo_disponivel", "tentar_ping": True},
            "permission_denied": {"acao": "verificar_escopo_autorizacao", "abortar_se_nao_autorizado": True},
            "rate_limited": {"acao": "backoff_e_retry", "delay_s": 30},
        }

        erro_lower = erro.lower()
        for key, recovery in acoes_recovery.items():
            if key in erro_lower:
                return recovery

        return {"acao": "retry_padrao", "max_retries": tarefa.max_retries}

    def registrar_callback_progresso(self, callback: Callable) -> None:
        """Registra callback para notificações de progresso."""
        self._callbacks_progresso.append(callback)

    @property
    def progresso(self) -> dict[str, Any]:
        """Retorna progresso atual da campanha."""
        total = len(self._tarefas)
        if total == 0:
            return {"percentual": 0, "fase": "aguardando"}

        concluidas = sum(1 for t in self._tarefas if t.status == StatusTarefa.CONCLUIDA)
        em_execucao = [t.titulo for t in self._tarefas if t.status == StatusTarefa.EM_EXECUCAO]

        return {
            "percentual": int(concluidas / total * 100),
            "concluidas": concluidas,
            "total": total,
            "em_execucao": em_execucao,
        }
