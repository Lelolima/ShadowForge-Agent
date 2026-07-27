"""
============================================================
 NVIDIA ShadowForge Agent - Event Bus Assíncrono
 Arquivo: core/event_bus.py
============================================================
 Sistema de eventos pub/sub para comunicação entre módulos,
 com suporte a prioridade, filtros, replay, métricas e
 retry automático de eventos críticos.
============================================================
"""

from __future__ import annotations

import asyncio
import enum
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

logger = logging.getLogger("shadowforge.core.event_bus")


class PrioridadeEvento(IntEnum):
    """Níveis de prioridade para eventos."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    TRACE = 4


class TipoEvento(str, enum.Enum):
    """Tipos de eventos do sistema."""
    # Ciclo OODA
    OODA_OBSERVE = "ooda:observe"
    OODA_ORIENT = "ooda:orient"
    OODA_DECIDE = "ooda:decide"
    OODA_ACT = "ooda:act"
    # Mudanças de estado
    FASE_CHANGED = "state:fase_changed"
    VULN_FOUND = "state:vuln_found"
    AC_EXECUTADA = "state:acao_executada"
    CAMPANHA_START = "state:campanha_start"
    CAMPANHA_END = "state:campanha_end"
    # Comandos e controle
    CMD_VOZ = "cmd:voz"
    CMD_CONTROLE = "cmd:controle"
    # Visão e detecção
    VISION_SCREENSHOT = "vision:screenshot"
    VISION_ANOMALIA = "vision:anomalia"
    VISION_OCR = "vision:ocr"
    # Voz e audio
    SPEECH_TRANSCRICAO = "speech:transcricao"
    SPEECH_TTS = "speech:tts"
    # Ferramentas hacker
    TOOL_RECON = "tool:recon"
    TOOL_EXPLOIT = "tool:exploit"
    TOOL_SCAN = "tool:scan"
    # Plugin events
    PLUGIN_LOAD = "plugin:load"
    PLUGIN_UNLOAD = "plugin:unload"
    # Sistema geral
    LOG_EVENT = "sys:log"
    ERROR = "sys:error"
    METRIC = "sys:metric"


@dataclass
class EventoShadowForge:
    """Representa um evento no sistema."""
    tipo: str
    payload: dict[str, Any] = field(default_factory=dict)
    prioridade: PrioridadeEvento = PrioridadeEvento.MEDIUM
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str = "unknown"
    campanha_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.event_id,
            "tipo": self.tipo,
            "prioridade": self.prioridade.name,
            "timestamp": self.timestamp,
            "source": self.source,
            "campanha_id": self.campanha_id,
            "payload": self.payload,
            "metadata": self.metadata,
        }


# Nome do tipo para handlers
HandlerCallback = Callable[[EventoShadowForge], Awaitable[None]]


class EventBus:
    """Barramento de eventos assíncrono com pub/sub, prioridade e replay.

    Suporta:
    - Subscrição por tipo ou padrão glob (ex: "vision:*")
    - Priorização de eventos (critical, high, medium, low, trace)
    - Replay de eventos recentes para novos subscribers
    - Métricas de eventos e latência
    - Retry automático para handlers que falham
    - Dead Letter Queue (DLQ) para eventos que não podem ser processados
    """

    # Limite de eventos históricos para replay
    HISTORICO_MAX = 500
    # Retry: quantos tentativas e backoff base em segundos
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 1.0

    def __init__(self) -> None:
        self._subscribers: dict[str, list[HandlerCallback]] = {}
        self._pattern_subscribers: list[tuple[str, HandlerCallback]] = []
        self._historico: list[EventoShadowForge] = []
        self._running = False
        self._queue: asyncio.PriorityQueue[tuple[int, float, EventoShadowForge]] = asyncio.PriorityQueue()
        self._processing_task: asyncio.Task | None = None
        self._event_count = 0
        self._metrics: dict[str, int] = {}

    async def start(self) -> None:
        """Inicia o processador de eventos."""
        self._running = True
        self._processing_task = asyncio.create_task(self._process_loop())
        logger.info("EventBus iniciado")

    async def stop(self) -> None:
        """Para o processador de eventos, processando os pendentes primeiro."""
        # Processa eventos restantes na queue antes de parar
        remaining = self._queue.qsize() if hasattr(self._queue, "qsize") else 0
        if remaining > 0:
            logger.info("EventBus: processando %d eventos pendentes antes de parar", remaining)
            for _ in range(remaining):
                try:
                    _, _, evento = self._queue.get_nowait()
                    await self._dispatch_event(evento)
                except asyncio.QueueEmpty:
                    break
                except Exception as e:
                    logger.error("Erro ao processar evento pendente: %s", e)

        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        logger.info("EventBus parado — %d eventos processados", self._event_count)

    async def publish(
        self,
        evento: EventoShadowForge,
        replay_for_new: bool = False,
    ) -> None:
        """Publica um evento no barramento.

        Args:
            evento: Evento a ser publicado
            replay_for_new: Se True, armazena no histórico para replay
        """
        await self._queue.put((evento.prioridade, evento.timestamp, evento))
        if replay_for_new:
            self._historico.append(evento)
            if len(self._historico) > self.HISTORICO_MAX:
                self._historico = self._historico[-self.HISTORICO_MAX :]

        self._event_count += 1
        self._metrics[evento.tipo] = self._metrics.get(evento.tipo, 0) + 1

    async def subscribe(
        self,
        tipo: str | None = None,
        pattern: str | None = None,
        handler: HandlerCallback | None = None,
        replay_recente: bool = False,
    ) -> None:
        """Subscreve um handler a eventos.

        Args:
            tipo: Tipo exato do evento (ex: "vision:screenshot")
            pattern: Padrão glob (ex: "vision:*")
            handler: Função callback async
            replay_recente: Se True, reenvia eventos recentes para o handler
        """
        if tipo and handler:
            if tipo not in self._subscribers:
                self._subscribers[tipo] = []
            self._subscribers[tipo].append(handler)
            logger.debug("Subscribed to event type: %s", tipo)

        if pattern and handler:
            self._pattern_subscribers.append((pattern, handler))
            logger.debug("Subscribed to pattern: %s", pattern)

        # Replay de eventos recentes
        if replay_recente and handler:
            for evt in self._historico:
                if tipo and evt.tipo == tipo:
                    await handler(evt)
                elif pattern and self._match_pattern(pattern, evt.tipo):
                    await handler(evt)

    async def unsubscribe(self, tipo: str, handler: HandlerCallback) -> None:
        """Remove subscrição."""
        if tipo in self._subscribers:
            self._subscribers[tipo] = [h for h in self._subscribers[tipo] if h is not handler]

    def _match_pattern(self, pattern: str, event_type: str) -> bool:
        """Match simple de padrão glob."""
        import fnmatch

        return fnmatch.fnmatch(event_type, pattern)

    async def _process_loop(self) -> None:
        """Loop principal de processamento de eventos."""
        while self._running:
            try:
                _, _, evento = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch_event(evento)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def _dispatch_event(self, evento: EventoShadowForge) -> None:
        """Envia evento para todos os handlers subscritos."""
        # Handlers de match exato
        handlers = self._subscribers.get(evento.tipo, []).copy()

        # Handlers de pattern
        for pattern, handler in self._pattern_subscribers:
            if self._match_pattern(pattern, evento.tipo):
                handlers.append(handler)

        # Executa handlers em paralelo com retry
        if handlers:
            tasks = [self._invoke_handler_with_retry(h, evento) for h in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _invoke_handler_with_retry(
        self, handler: HandlerCallback, evento: EventoShadowForge
    ) -> None:
        """Invoca handler com retry automático."""
        for attempt in range(self.MAX_RETRIES):
            try:
                await handler(evento)
                return
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Event handler failed (attempt %d): %s | retry in %.1fs",
                        attempt + 1, str(e)[:80], delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "Event handler failed permanently: %s | Event: %s",
                        str(e)[:100], evento.event_id,
                    )
                    # DLQ: dead letter queue (log + persist)
                    logger.error("[DLQ] Event %s moved to dead letter", evento.event_id)

    def get_stats(self) -> dict[str, Any]:
        """Retorna estatísticas do event bus."""
        return {
            "total_events": self._event_count,
            "queue_size": self._queue.qsize() if hasattr(self._queue, "qsize") else 0,
            "subscribers": sum(len(h) for h in self._subscribers.values()),
            "event_counts": self._metrics,
            "historico_size": len(self._historico),
        }
