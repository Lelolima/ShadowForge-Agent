#!/usr/bin/env python3.11
"""
============================================================
 NVIDIA ShadowForge Agent - Ponto de Entrada Principal
 Arquivo: main.py
 Versão: 1.0.0 | Codinome: SH4D0WF0RG3
============================================================
 Agente autônomo de hacking ético com visão computacional,
 interface por voz e stack NVIDIA completa.

 USO:
   python main.py --mode stealth --config config/default.yaml
   python main.py --mode recon_only --target 192.168.1.0/24
   python main.py --voice --always-listen

 AVISO LEGAL:
   Este software é destinado EXCLUSIVAMENTE para testes
   de segurança autorizados, pesquisa e educação.
   Uso não autorizado é ILEGAL e antiético.
============================================================
"""

import argparse
import asyncio
import contextlib
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

# Forcar UTF-8 no Windows
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Carrega .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

console = Console(force_terminal=True)

# Banner ASCII cyberpunk
BANNER = r"""
[cyan]
  ╔═══════════════════════════════════════════════════════════════╗
  ║                                                               ║
  ║   ███████╗██╗  ██╗ █████╗ ██████╗  ██████╗ ██╗    ██╗        ║
  ║   ██╔════╝██║  ██║██╔══██╗██╔══██╗██╔═══██╗██║    ██║        ║
  ║   ███████╗███████║███████║██║  ██║██║   ██║██║ █╗ ██║        ║
  ║   ╚════██║██╔══██║██╔══██║██║  ██║██║   ██║██║███╗██║        ║
  ║   ███████║██║  ██║██║  ██║██████╔╝╚██████╔╝╚███╔███╔╝        ║
  ║   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝         ║
  ║                                                               ║
  ║   ███████╗███████╗ ██████╗ █████╗ ██████╗ ███████╗            ║
  ║   ██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝            ║
  ║   ███████╗█████╗  ██║     ███████║██████╔╝█████╗              ║
  ║   ╚════██║██╔══╝  ██║     ██╔══██║██╔══██╗██╔══╝              ║
  ║   ███████║██║     ╚██████╗██║  ██║██║  ██║███████╗            ║
  ║   ╚══════╝╚═╝      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝            ║
  ║                                                               ║
  ║   [ SH4D0WF0RG3 v1.0.0 | 1337 Mode ]                         ║
  ║   Autonomous Ethical Hacking AI | NVIDIA Powered              ║
  ║                                                               ║
  ╚═══════════════════════════════════════════════════════════════╝
[/cyan]
"""

CREDITS = """
[yellow]
  ⚠️  AVISO LEGAL ⚠️
  Este software é para pentest AUTORIZADO apenas.
  Uso não autorizado é CRIME. Ethics first, hack second.
  Sempre obtenha permissão escrita antes de testar.
[/yellow]
"""


class ShadowForgeLauncher:
    """Launcher principal do agente ShadowForge."""

    def __init__(self) -> None:
        self.args: argparse.Namespace | None = None
        self.agent: object | None = None
        self._shutdown_event: asyncio.Event = asyncio.Event()

    def parse_args(self) -> argparse.Namespace:
        """Parseia argumentos da linha de comando."""
        parser = argparse.ArgumentParser(
            prog="shadowforge",
            description="NVIDIA ShadowForge Agent - Autonomous Ethical Hacking AI",
            epilog=">> Ethics first, hack second. <<",
        )

        parser.add_argument(
            "--mode",
            choices=["stealth", "agressivo", "recon_only", "debug"],
            default="stealth",
            help="Modo de operação do agente (default: stealth)",
        )
        parser.add_argument(
            "--config",
            type=str,
            default="config/default.yaml",
            help="Caminho do arquivo de configuração YAML",
        )
        parser.add_argument(
            "--target",
            type=str,
            default=None,
            help="Alvo inicial (IP, range, domínio)",
        )
        parser.add_argument(
            "--voice",
            action="store_true",
            help="Habilita interface por voz",
        )
        parser.add_argument(
            "--always-listen",
            action="store_true",
            help="Modo always-listening (sem push-to-talk)",
        )
        parser.add_argument(
            "--simulate",
            action="store_true",
            help="Modo simulação - não executa ataques reais",
        )
        parser.add_argument(
            "--gpu",
            type=int,
            default=0,
            help="ID da GPU NVIDIA (default: 0)",
        )
        parser.add_argument(
            "--no-gpu",
            action="store_true",
            help="Força modo CPU",
        )
        parser.add_argument(
            "--campaign",
            type=str,
            default=None,
            help="Nome da campanha para retomar",
        )
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Nível de logging",
        )
        parser.add_argument(
            "--ascii",
            action="store_true",
            help="Output ASCII puro (sem Rich)",
        )

        return parser.parse_args()

    def display_banner(self) -> None:
        """Exibe banner cyberpunk."""
        if not self.args.ascii:
            console.print(BANNER)
            console.print(CREDITS)

            # Tabela de status
            table = Table(title="Status do Sistema", show_header=True, header_style="bold cyan")
            table.add_column("Componente", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Modo", style="yellow")

            table.add_row("Agente", "INICIALIZANDO", self.args.mode.upper())
            table.add_row("GPU", "Detectando...", "AUTO")
            table.add_row("Voz", "ATIVA" if self.args.voice else "DESATIVADA", "")
            table.add_row("Alvo", self.args.target or "NENHUM", "")

            console.print(table)
        else:
            print("SH4D0WF0RG3 v1.0.0 | Autonomous Ethical Hacking AI")
            print("=" * 50)

    def detect_gpu(self) -> dict:
        """Detecta GPU NVIDIA disponível."""
        gpu_info = {"disponivel": False, "nome": "N/A", "vram": "N/A"}

        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines:
                    parts = lines[0].split(",")
                    gpu_info["disponivel"] = True
                    gpu_info["nome"] = parts[0].strip()
                    gpu_info["vram"] = parts[1].strip() if len(parts) > 1 else "N/A"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return gpu_info

    def setup_logging(self) -> logging.Logger:
        """Configura logging estilo hacker."""
        log_dir = ROOT_DIR / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"shadowforge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        formatter = logging.Formatter(
            fmt="%(asctime)s │ %(levelname)-8s │ %(name)-20s │ %(message)s",
            datefmt="%H:%M:%S"
        )

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        logger = logging.getLogger("shadowforge")
        logger.setLevel(getattr(logging, self.args.log_level))
        logger.addHandler(file_handler)

        return logger

    async def run(self) -> None:
        """Loop principal assíncrono."""
        self.args = self.parse_args()
        self.display_banner()

        logger = self.setup_logging()
        logger.info("SH4D0WF0RG3 Agent iniciando - Modo: %s", self.args.mode)

        # Detecta GPU
        gpu = self.detect_gpu()
        if gpu["disponivel"]:
            console.print(f"\n[bold green]  GPU Detectada: {gpu['nome']} ({gpu['vram']})[/bold green]")
            logger.info("GPU: %s (%s)", gpu["nome"], gpu["vram"])
        elif not self.args.no_gpu:
            console.print("\n[yellow]  GPU NVIDIA não detectada - Modo CPU ativado[/yellow]")
            logger.warning("GPU não detectada, usando CPU")

        # Verifica autorização
        console.print("\n[bold red]  ⚠️  VERIFICAÇÃO DE AUTORIZAÇÃO[/bold red]")
        console.print("[dim]  Este agente SÓ opera em alvos autorizados.[/dim]")
        console.print("[dim]  Certifique-se de ter permissão escrita.[/dim]\n")

        # Carrega configuração
        config_path = ROOT_DIR / self.args.config
        if not config_path.exists():
            console.print(f"[red]  Config não encontrado: {config_path}[/red]")
            sys.exit(1)

        # Inicializa componentes
        console.print("\n[cyan]  [*] Inicializando subsistemas...[/cyan]")

        try:
            # Importa e inicializa o agente
            from core.agent import ShadowForgeAgent

            self.agent = ShadowForgeAgent(
                config_path=str(config_path),
                mode=self.args.mode,
                target=self.args.target,
                voice_enabled=self.args.voice,
                simulate=self.args.simulate,
                gpu_id=self.args.gpu if not self.args.no_gpu else -1,
                campaign=self.args.campaign,
            )

            console.print("[green]  [+] Core agent.............. OK[/green]")
            console.print("[green]  [+] Módulo visão............ OK[/green]")
            console.print("[green]  [+] Módulo controle......... OK[/green]")
            console.print("[green]  [+] Módulo planejamento..... OK[/green]")

            if self.args.voice:
                console.print("[green]  [+] Módulo voz.............. OK[/green]")
            else:
                console.print("[dim]  [ ] Módulo voz.............. DESATIVADO[/dim]")

            console.print(f"\n[bold green]  SH4D0WF0RG3 ONLINE | Modo: {self.args.mode.upper()}[/bold green]\n")

            # Registra handlers de shutdown
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                with contextlib.suppress(NotImplementedError):
                    loop.add_signal_handler(sig, self._handle_shutdown, sig) # Windows

            # Executa ciclo principal do agente
            await self.agent.run()

        except ImportError as e:
            console.print(f"[red]  [-] Erro de importação: {e}[/red]")
            console.print("[yellow]  Execute setup.sh primeiro.[/yellow]")
            sys.exit(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]  [!] Shutdown solicitado pelo usuário[/yellow]")
        except Exception as e:
            console.print(f"[red]  [-] Erro fatal: {e}[/red]")
            logger.exception("Erro fatal no launcher")
            raise
        finally:
            if self.agent:
                await self.agent.shutdown()
            console.print("[cyan]  SH4D0WF0RG3 OFFLINE | Sessão encerrada[/cyan]")

    def _handle_shutdown(self, sig: signal.Signals) -> None:
        """Handler graceful de shutdown."""
        console.print(f"\n[yellow]  [!] Sinal {sig.name} recebido - Encerrando...[/yellow]")
        self._shutdown_event.set()


def main() -> None:
    """Ponto de entrada."""
    launcher = ShadowForgeLauncher()
    try:
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        print("\nSH4D0WF0RG3 OFFLINE")


if __name__ == "__main__":
    main()
