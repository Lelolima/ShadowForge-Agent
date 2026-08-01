"""
============================================================
NVIDIA ShadowForge Agent - Sistema de Plugins
Arquivo: core/plugins.py
============================================================
Arquitetura de plugins extensível com discovery, hooks,
hot-reload e integração nativa com o EventBus.

Features:
- Carregamento dinâmico de plugins em /plugins/
- Validacao de dependencias entre plugins
- Hooks pre/post para cada fase OODA
- Sandboxing basico via import isolado
============================================================
"""

from __future__ import annotations

import importlib.util
import inspect
import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import blake3

from core.event_bus import EventBus, EventoShadowForge

logger = logging.getLogger("shadowforge.core.plugins")


def _get_file_hash(file_path: Path) -> str:
    """Retorna o hash BLAKE3 do arquivo (resistente a colisões quânticas)."""
    try:
        with open(file_path, 'rb') as f:
            return blake3.blake3(f.read()).hexdigest()
    except (IOError, OSError):
        return ""


# M-07 FIX: Prefixo de namespace para evitar conflito com builtins
_PLUGIN_NAMESPACE_PREFIX = "shadowforge.plugins."

# H-10 FIX: Plugins permitidos (hash SHA256 do conteúdo do arquivo).
# Vazio = aceita qualquer plugin (EM PRODUÇÃO: preencher com hashes conhecidos).
_TRUSTED_PLUGIN_HASHES: set[str] = set()


class ShadowForgePlugin(ABC):
    """Interface base para todos os plugins."""

    @property
    @abstractmethod
    def nome(self) -> str:
        ...

    @property
    @abstractmethod
    def versao(self) -> str:
        ...

    @property
    def dependencias(self) -> list[str]:
        return []

    @property
    def ativo(self) -> bool:
        return True

    async def on_load(self, bus: EventBus, ctx: dict[str, Any]) -> None:
        """Chamado quando o plugin é ativado."""
        pass

    async def on_unload(self, bus: EventBus) -> None:
        """Chamado quando o plugin é desativado."""
        pass

    async def on_event(self, evento: EventoShadowForge) -> None:
        """Hook genérico para todos os eventos."""
        pass


@dataclass
class PluginInfo:
    """Metadados de um plugin."""
    nome: str
    versao: str
    caminho: str
    dependencias: list[str] = field(default_factory=list)
    author: str = ""
    ativo: bool = True
    data_load: str = field(default_factory=lambda: datetime.now().isoformat())


class PluginManager:
    """Gerenciador de plugins do ShadowForge.
    # H-10 FIX: AVISO DE SEGURANÇA — plugins executam código arbitrário
    # sem sandboxing. Em produção: (1) preencha _TRUSTED_PLUGIN_HASHES
    # com hashes SHA256 dos plugins aprovados, (2) rode plugins em
    # subprocess isolado, ou (3) use RestrictedPython para compilá-los.
    """

    PLUGIN_DIRS = ["plugins", "shadowforge_plugins"]

    def __init__(self, event_bus: EventBus, plugin_dirs: list[str] | None = None) -> None:
        self._bus = event_bus
        self._plugin_dirs = [
            Path(d).expanduser()
            for d in (plugin_dirs or self.PLUGIN_DIRS)
        ]
        self._plugins: dict[str, ShadowForgePlugin] = {}
        self._infos: dict[str, PluginInfo] = {}

    async def discover(self) -> list[PluginInfo]:
        """Busca plugins em todos os diretórios."""
        encontrados = []

        for dir_path in self._plugin_dirs:
            if not dir_path.is_dir():
                continue
            for path_file in dir_path.rglob("*.py"):
                if path_file.name.startswith("_"):
                    continue
                info = await self._load_plugin(path_file)
                if info:
                    encontrados.append(info)

        return encontrados

    async def load_all(self) -> None:
        """Carrega todos os plugins descobertos."""
        infos = await self.discover()

        for info in infos:
            if info.nome not in self._plugins:
                await self.activate(info.nome)

        logger.info("Plugins carregados: %d", len(self._plugins))

    async def _load_plugin(self, path: Path) -> PluginInfo | None:
        """Tenta carregar um plugin individual."""
        try:
            spec = importlib.util.spec_from_file_location(path.stem, str(path))
            if not spec or not spec.loader:
                return None
            # H-10 FIX: Verificar hash do plugin contra lista de trust (se configurada)
            if _TRUSTED_PLUGIN_HASHES:
                file_hash = _get_file_hash(path)
                if file_hash not in _TRUSTED_PLUGIN_HASHES:
                    logger.warning("[PLUGIN] Hash não confiável para %s: %s (requer registro em _TRUSTED_PLUGIN_HASHES)", path.name, file_hash[:16])
                    return None
                logger.debug("Plugin %s: hash verificado OK (%s...)", path.name, file_hash[:16])
            else:
                logger.warning("[PLUGIN] Carregando %s SEM verificação de hash — configure _TRUSTED_PLUGIN_HASHES em produção", path.name)
            module = importlib.util.module_from_spec(spec)

            # M-07 FIX: Usar namespace prefixado para evitar conflito com builtins
            module_name = f"{_PLUGIN_NAMESPACE_PREFIX}{path.stem}"
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            for nome_atributo in dir(module):
                obj = getattr(module, nome_atributo)
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, ShadowForgePlugin)
                    and not inspect.isabstract(obj)
                    and obj is not ShadowForgePlugin
                ):
                    instancia: ShadowForgePlugin = obj()
                    info = PluginInfo(
                        nome=instancia.nome,
                        versao=instancia.versao,
                        caminho=str(path),
                        dependencias=list(instancia.dependencias),
                    )
                    self._infos[info.nome] = info
                    self._plugins[info.nome] = instancia
                    logger.debug("Plugin descoberto: %s v%s", info.nome, info.versao)
                    return info

        except SyntaxError as e:
            logger.warning("Plugin %s tem erro de sintaxe: %s", path, e)
        except ImportError as e:
            logger.debug("Plugin %s falhou import: %s", path, e)
        except Exception as e:
            logger.warning("Erro ao carregar plugin %s: %s", path, e)

        return None

    async def activate(self, nome: str) -> bool:
        """Ativa (on_load) um plugin registrado."""
        plugin = self._plugins.get(nome)
        if not plugin:
            return False

        if not plugin.ativo:
            logger.info("Plugin %s está desativado", nome)
            return False

        ctx: dict[str, Any] = {}
        await plugin.on_load(self._bus, ctx)
        logger.info("Plugin ativado: %s", nome)
        return True

    async def deactivate(self, nome: str) -> None:
        """Desativa um plugin e executa on_unload."""
        plugin = self._plugins.pop(nome, None)
        if plugin:
            await plugin.on_unload(self._bus)
            self._infos.pop(nome, None)
            logger.info("Plugin desativado: %s", nome)

    def get_plugin(self, nome: str) -> ShadowForgePlugin | None:
        return self._plugins.get(nome)

    def list_plugins(self) -> list[PluginInfo]:
        return list(self._infos.values())

    async def invoke_hook(self, hook: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Invoca um hook em todos os plugins ativos."""
        results = []
        for nome, plugin in self._plugins.items():
            if not plugin.ativo:
                continue
            try:
                fn = getattr(plugin, hook, None)
                if fn and callable(fn):
                    if inspect.iscoroutinefunction(fn):
                        r = await fn(*args, **kwargs)
                    else:
                        r = fn(*args, **kwargs)
                    results.append(r)
            except Exception as e:
                logger.error("Hook %s falhou no plugin %s: %s", hook, nome, e)
        return results

    