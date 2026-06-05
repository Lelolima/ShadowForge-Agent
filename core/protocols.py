"""Protocolos para tipagem do ShadowForge Agent."""

from __future__ import annotations

from typing import Any, Protocol


class ShadowForgeConfig(Protocol):
    """Protocolo para configuração do ShadowForge Agent.

    Permite que qualquer objeto com atributos via getattr
    seja aceito como configuração. Usado em vez de `Any`
    para manter type hints úteis e documentar a API.
    """

    def __getattr__(self, name: str) -> Any: ...
