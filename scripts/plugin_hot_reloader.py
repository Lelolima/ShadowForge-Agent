#!/usr/bin/env python3.11
"""
============================================================
NVIDIA ShadowForge - Plugin Hot-Reloader
Arquivo: scripts/plugin_hot_reloader.py
============================================================
Monitora alterações nos arquivos de plugin e recarrega automaticamente.
Útil para desenvolvimento de plugins.
============================================================
"""

import asyncio
import blake3
import os
import sys
import time
from pathlib import Path
from typing import Dict, Set

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("Aviso: 'rich' não instalado. Instale com: pip install rich")

from core.plugins import PluginManager
from core.event_bus import EventBus


class FileChangeHandler:
    """Monitora alterações em arquivos usando hash BLAKE3."""

    def __init__(self, watch_paths: list[Path]):
        self.watch_paths = [p.resolve() for p in watch_paths if p.exists()]
        self.file_hashes: dict[Path, str] = {}
        self._initialize_hashes()

    def _debug_log(self, message: str):
        """Log debug message if debugging is enabled."""
        # For now, always print debug info to help troubleshoot
        print(f"[DEBUG] {message}")

    def _initialize_hashes(self):
        """Inicializa o hash de todos os arquivos monitorados."""
        for path in self.walk_files():
            self.file_hashes[path] = self._get_file_hash(path)

    def walk_files(self):
        """Gerador que percorre todos os arquivos Python nos caminhos monitorados."""
        for watch_path in self.watch_paths:
            if watch_path.is_file():
                if watch_path.suffix == '.py':
                    yield watch_path
            elif watch_path.is_dir():
                for py_file in watch_path.rglob("*.py"):
                    # Ignora arquivos __pycache__ e similares
                    if "__pycache__" not in str(py_file):
                        yield py_file

    def _get_file_hash(self, file_path: Path) -> str:
        """Retorna o hash BLAKE3 do arquivo (resistente a colisões quânticas)."""
        try:
            with open(file_path, 'rb') as f:
                return blake3.blake3(f.read()).hexdigest()
        except (IOError, OSError):
            return ""

    def check_changes(self) -> set[Path]:
        """
        Verifica quais arquivos foram modificados.

        Returns:
            Conjunto de caminhos de arquivos modificados
        """
        changed_files = set()

        for file_path in self.walk_files():
            current_hash = self._get_file_hash(file_path)
            stored_hash = self.file_hashes.get(file_path)

            self._debug_log(f"Checking {file_path.name}: current={current_hash[:8] if current_hash else 'None'}, stored={stored_hash[:8] if stored_hash else 'None'}")

            if current_hash != stored_hash:
                changed_files.add(file_path)
                self.file_hashes[file_path] = current_hash
                self._log(f"[green][+] Arquivo alterado: {file_path.name}[/green]")

        return changed_files


class PluginHotReloader:
    """Recarrega plugins automaticamente quando seus arquivos são modificados."""

    def __init__(self, plugin_dirs: list[str] | None = None):
        self.event_bus = EventBus()
        self.plugin_manager = PluginManager(self.event_bus, plugin_dirs)
        self.file_handler = FileChangeHandler(
            [Path(d) for d in (plugin_dirs or self.plugin_manager.PLUGIN_DIRS)]
        )
        self.loaded_plugins: set[str] = set()
        self.console = Console() if HAS_RICH else None

    def _log(self, message: str, style: str = ""):
        """Log message with optional styling."""
        if self.console:
            self.console.print(message, style=style)
        else:
            print(message)

    def _debug_log(self, message: str):
        """Debug log message."""
        print(f"[DEBUG] {message}")  # Always print to stdout for debugging
        if self.console:
            self.console.print(f"[dim][DEBUG] {message}[/dim]")

    async def initial_load(self):
        """Carrega todos os plugins inicialmente."""
        self._log("[blue][*] Carregando plugins iniciais...[/blue]")
        await self.plugin_manager.load_all()

        # Atualiza a lista de plugins carregados
        self.loaded_plugins = {info.nome for info in self.plugin_manager.list_plugins()}

        plugin_count = len(self.loaded_plugins)
        self._log(f"[green][+] {plugin_count} plugin(s) carregado(s) inicialmente[/green]")

        if self.loaded_plugins:
            for plugin_info in self.plugin_manager.list_plugins():
                self._log(f"    • {plugin_info.nome} v{plugin_info.versao}")

    async def reload_plugin(self, plugin_name: str):
        """Recarrega um plugin específico."""
        self._log(f"[yellow][~] Recarregando plugin: {plugin_name}[/yellow]")

        try:
            # Desativa o plugin se estiver carregado
            if plugin_name in self.loaded_plugins:
                await self.plugin_manager.deactivate(plugin_name)
                self.loaded_plugins.discard(plugin_name)
                self._log(f"    [blue][-] Plugin {plugin_name} desativado[/blue]")

            # Ativa o plugin novamente
            if await self.plugin_manager.activate(plugin_name):
                self.loaded_plugins.add(plugin_name)
                plugin_info = self.plugin_manager.get_plugin(plugin_name)
                if plugin_info:
                    self._log(f"    [green][+] Plugin {plugin_name} v{plugin_info.versao} recarregado[/green]")
                else:
                    self._log(f"    [green][+] Plugin {plugin_name} recarregado[/green]")
            else:
                self._log(f"    [red][-] Falha ao ativar plugin {plugin_name}[/red]", "red")

        except Exception as e:
            self._log(f"    [red][-] Erro ao recarregar plugin {plugin_name}: {e}[/red]", "red")

    async def scan_and_reload(self):
        """Verifica alterações nos arquivos e recarrega plugins afetados."""
        self._debug_log("scan_and_reload called!")
        changed_files = self.file_handler.check_changes()

        if not changed_files:
            self._debug_log("No changed files found")
            return

        self._debug_log(f"Detected {len(changed_files)} changed file(s):")
        for f in changed_files:
            self._debug_log(f"  - {f}")

        # Mapeia arquivos alterados para plugins potenciais
        plugins_to_reload: set[str] = set()

        for changed_file in changed_files:
            # Determina se o arquivo alterado pertence a um plugin
            relative_path = None
            for watch_path in self.file_handler.watch_paths:
                try:
                    relative_path = changed_file.relative_to(watch_path)
                    self._debug_log(f"File {changed_file} is relative to {watch_path}: {relative_path}")
                    break
                except ValueError as e:
                    self._debug_log(f"File {changed_file} is NOT relative to {watch_path}: {e}")
                    continue

            if relative_path is None:
                self._debug_log(f"File {changed_file} is not relative to any watch path")
                continue

            # Extrai o nome do plugin do caminho (assumindo estrutura plugins/nome_do_plugin/...)
            path_parts = relative_path.parts
            self._debug_log(f"Path parts for {relative_path}: {path_parts}")

            if len(path_parts) >= 2 and path_parts[0] in ["plugins", "shadowforge_plugins"]:
                plugin_name = path_parts[1]
                plugins_to_reload.add(plugin_name)
                self._debug_log(f"Mapped {changed_file} to plugin: {plugin_name} (path_parts[0]={path_parts[0]}, path_parts[1]={path_parts[1]})")
            elif len(path_parts) >= 1 and path_parts[0] in ["plugins", "shadowforge_plugins"]:
                # Arquivo direto no diretório de plugins (menos comum)
                plugin_name = path_parts[0].replace(".py", "")
                plugins_to_reload.add(plugin_name)
                self._debug_log(f"Mapped {changed_file} to plugin: {plugin_name} (direct file)")
            else:
                self._debug_log(f"Could not map {changed_file} to a plugin: path_parts={path_parts}")

        # Recarrega os plugins afetados
        for plugin_name in plugins_to_reload:
            self._log(f"[yellow][~] Recarregando plugin: {plugin_name}[/yellow]")
            await self.reload_plugin(plugin_name)

    def _display_status(self):
        """Exibe o status atual do monitoramento."""
        if self.console:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.console.print(f"[dim][{timestamp}] Monitorando {len(self.file_handler.watch_paths)} diretório(s)...[/dim]")
        else:
            pass  # Versão silenciosa sem rich

    async def start_watching(self, poll_interval: float = 1.0):
        """
        Inicia o monitoramento de arquivos.

        Args:
            poll_interval: Intervalo em segundos entre verificações
        """
        self._log("[blue][*] Iniciando hot-reloader de plugins...[/blue]")
        self._log(f"[blue][*] Intervalo de verificação: {poll_interval}s[/blue]")
        self._log("[blue][*] Pressione Ctrl+C para parar[/blue]")

        # Carrega inicialmente
        await self.initial_load()

        try:
            while True:
                await self.scan_and_reload()
                await asyncio.sleep(poll_interval)
        except KeyboardInterrupt:
            self._log("\n[yellow][!] Parando hot-reloader...[/yellow]")
        except Exception as e:
            self._log(f"\n[red][-] Erro no hot-reloader: {e}[/red]", "red")
        finally:
            # Desativa todos os plugins antes de sair
            self._log("[blue][*] Desativando todos os plugins...[/blue]")
            for plugin_name in list(self.loaded_plugins):
                try:
                    await self.plugin_manager.deactivate(plugin_name)
                except Exception:
                    pass  # Ignora erros durante o desligamento
            self._log("[green][+] Hot-relôader finalizado[/green]")


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Hot-reloader para plugins do ShadowForge Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python scripts/plugin_hot_reloader.py
  python scripts/plugin_hot_reloader.py --interval 0.5
  python scripts/plugin_hot_reloader.py --dirs plugins shadowforge_plugins
        """
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Intervalo de verificação em segundos (padrão: 1.0)"
    )

    parser.add_argument(
        "--dirs",
        nargs="+",
        default=["plugins", "shadowforge_plugins"],
        help="Diretórios para monitorar (padrão: plugins shadowforge_plugins)"
    )

    parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Desativar output colorido (mesmo se rich estiver instalado)"
    )

    args = parser.parse_args()

    # Desativa rich se solicitado
    if args.no_rich:
        global HAS_RICH
        HAS_RICH = False

    # Cria e inicia o hot-reloader
    reloader = PluginHotReloader(plugin_dirs=args.dirs)

    try:
        asyncio.run(reloader.start_watching(poll_interval=args.interval))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()