"""
============================================================
 Subsystem Factory - Padrão Factory para criação de subsistemas
 ============================================================
Implementa o padrão Factory para criar subsistemas de forma
padronizada, reduzindo duplicação de código e melhorando
extensibilidade.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Callable

from rich.console import Console

console = Console()
logger = logging.getLogger("shadowforge.core")


class SubsystemFactory:
    """Factory para criação padronizada de subsistemas."""

    @staticmethod
    def create_subsystem(
        subsystem_name: str,
        creator_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Cria um subsistema usando o padrão Factory com tratamento padronizado de erros.

        Args:
            subsystem_name: Nome do subsistema para logging
            creator_func: Função que cria o subsistema
            *args, **kwargs: Argumentos para passar para a função criadora

        Returns:
            O subsistema criado ou None se falhar
        """
        try:
            subsystem = creator_func(*args, **kwargs)
            logger.info(f"[OK] Módulo {subsystem_name} inicializado")
            console.print(f"[green]  [+] Módulo {subsystem_name:<20} OK[/green]")
            return subsystem
        except ImportError as e:
            logger.warning(f"Módulo {subsystem_name} não disponível: {e}")
            console.print(f"[dim]  [ ] Módulo {subsystem_name:<20} DESATIVADO[/dim]")
            return None
        except Exception as e:
            logger.error(f"Erro ao inicializar {subsystem_name}: {e}")
            console.print(f"[red]  [-] Módulo {subsystem_name:<20} ERRO[/red]")
            return None


# Funções auxiliares para criar cada tipo de subsistema
def create_event_bus(agent_instance):
    """Cria e inicializa o Event Bus."""
    from core.event_bus import EventBus
    event_bus = EventBus()
    # Nota: EventBus precisa ser iniciado separadamente com await event_bus.start()
    return event_bus


def create_plugin_manager(agent_instance):
    """Cria o Plugin Manager."""
    from core.plugins import PluginManager
    return PluginManager(agent_instance.event_bus)


def create_dashboard(agent_instance):
    """Cria a Dashboard API."""
    try:
        from api.dashboard import app, update_dashboard_state
        return app  # update_dashboard_state será chamado separadamente
    except ImportError:
        return None  # Já será tratado pelo factory


def create_models(agent_instance):
    """Cria os modelos NVIDIA."""
    from models.multimodal import NemotronVision
    from models.nim_client import NIMClient
    from models.prompts import PromptManager

    return {
        "nim": NIMClient(config=agent_instance.config.nvidia),
        "vision": NemotronVision(config=agent_instance.config.nvidia),
        "prompts": PromptManager(),
    }


def create_vision(agent_instance):
    """Cria o subsistema de visão."""
    from vision.ocr import OCRExtractor
    from vision.screen import ScreenCapture
    from vision.understanding import ScreenUnderstanding

    return {
        "capture": ScreenCapture(config=agent_instance.config),
        "understanding": ScreenUnderstanding(config=agent_instance.config),
        "ocr": OCRExtractor(config=agent_instance.config),
    }


def create_speech(agent_instance):
    """Cria o subsistema de fala."""
    from speech.voice_interface import VoiceInterface
    return VoiceInterface(config=agent_instance.config)


def create_control(agent_instance):
    """Cria o subsistema de controle."""
    from control.keyboard import StealthKeyboard
    from control.mouse import StealthMouse
    from control.shell import StealthShell

    return {
        "mouse": StealthMouse(),
        "keyboard": StealthKeyboard(),
        "shell": StealthShell(config=agent_instance.config),
    }


def create_hacker_tools(agent_instance):
    """Cria o subsistema de ferramentas hacker."""
    from hacker_tools.exploit.web_attacks import WebExploiter
    from hacker_tools.recon.scanner import ReconScanner
    from hacker_tools.reporting.report_generator import ReportGenerator

    return {
        "recon": ReconScanner(config=agent_instance.config),
        "web_exploit": WebExploiter(config=agent_instance.config),
        "report": ReportGenerator(),
    }


def create_planning(agent_instance):
    """Cria o subsistema de planejamento."""
    from planning.orchestrator import CampaignOrchestrator
    from planning.rag import MITRERAG

    return {
        "orchestrator": CampaignOrchestrator(config=agent_instance.config),
        "rag": MITRERAG(config=agent_instance.config),
    }