#!/usr/bin/env python3.11
"""
============================================================
 NVIDIA ShadowForge - Health Check Completo
 Arquivo: scripts/health_check.py
============================================================
 Executa validacao visual completa de todos os subsistemas
 com output colorido em tempo real.
============================================================
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402
from rich.text import Text  # noqa: E402

console = Console(force_terminal=True)


async def check_subsystems():
    results = {}

    # 1. Config YAML
    console.print("\n[bold cyan][1/7] Verificando configuracao YAML...[/bold cyan]")
    try:
        import yaml
        config_path = ROOT_DIR / "config" / "default.yaml"
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        modo = config.get("agente", {}).get("modo", "N/A")
        console.print(f"  [green]OK[/green] - Modo: {modo}")
        results["config_yaml"] = True
    except Exception as e:
        console.print(f"  [red]FALHA[/red] - {str(e)[:60]}")
        results["config_yaml"] = False

    # 2. .env
    console.print("[bold cyan][2/7] Verificando .env...[/bold cyan]")
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        key = os.environ.get("NVIDIA_API_KEY", "")
        if key and not key.startswith("nvapi-xxxxx"):
            # Do not expose any part of the API key in output for security
            console.print("  [green]OK[/green] - API Key: [[CONFIGURADA]]")
            results["env_file"] = True
        else:
            console.print("  [yellow]AVISO[/yellow] - API Key nao configurada ou placeholder")
            results["env_file"] = False
    else:
        console.print("  [red]FALHA[/red] - .env nao encontrado")
        results["env_file"] = False

    # 3. NIM Client
    console.print("[bold cyan][3/7] Verificando NIM Client...[/bold cyan]")
    try:
        from core.config import ConfigNVIDIA
        from models.nim_client import NIMClient

        nvidia_config = ConfigNVIDIA(api_key=os.environ.get("NVIDIA_API_KEY", ""))
        nim = NIMClient(config=nvidia_config)

        if nim.disponivel():
            saude = await nim.verificar_saude()
            if saude:
                console.print("  [green]OK[/green] - NIM online, API key valida")
            else:
                console.print("  [yellow]AVISO[/yellow] - NIM API key configurada mas endpoints retornam erro")
            results["nim_client"] = True
        else:
            console.print("  [yellow]SIMULACAO[/yellow] - NIM operando em modo simulacao")
            results["nim_client"] = False

        await nim.fechar()
    except Exception as e:
        console.print(f"  [red]FALHA[/red] - {str(e)[:60]}")
        results["nim_client"] = False

    # 4. Modelos Pydantic
    console.print("[bold cyan][4/7] Verificando modelos Pydantic...[/bold cyan]")
    try:
        from core.config import ShadowForgeConfig
        cfg = ShadowForgeConfig.carregar_de_yaml(str(ROOT_DIR / "config" / "default.yaml"))
        console.print(f"  [green]OK[/green] - Config: {cfg.nome} v{cfg.versao} [{cfg.codinome}]")
        console.print(f"  [green]OK[/green] - Modo: {cfg.modo.value} | Etica: autorizacao={cfg.etica.exigir_autorizacao}")
        results["pydantic"] = True
    except Exception as e:
        console.print(f"  [red]FALHA[/red] - {str(e)[:60]}")
        results["pydantic"] = False

    # 5. Modulos
    console.print("[bold cyan][5/7] Verificando importacao de modulos...[/bold cyan]")
    modules_ok = 0
    modules_fail = 0
    module_list = [
        "core.config", "core.state", "core.memory",
        "models.nim_client", "models.prompts",
        "vision.screen", "vision.ocr", "vision.detector",
        "control.mouse", "control.keyboard", "control.shell",
        "planning.orchestrator", "planning.rag",
        "speech.asr", "speech.tts",
    ]
    for mod in module_list:
        try:
            __import__(mod)
            modules_ok += 1
        except Exception:
            modules_fail += 1

    if modules_fail == 0:
        console.print(f"  [green]OK[/green] - {modules_ok}/{len(module_list)} modulos importam corretamente")
        results["modules"] = True
    else:
        console.print(f"  [yellow]AVISO[/yellow] - {modules_ok}/{len(module_list)} OK, {modules_fail} falharam")
        results["modules"] = modules_ok > len(module_list) // 2

    # 6. GPU
    console.print("[bold cyan][6/7] Verificando GPU NVIDIA...[/bold cyan]")
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            gpu_info = result.stdout.strip().split("\n")[0]
            console.print(f"  [green]OK[/green] - {gpu_info}")
            results["gpu"] = True
        else:
            console.print("  [yellow]N/A[/yellow] - nvidia-smi nao disponivel (modo CPU)")
            results["gpu"] = False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        console.print("  [yellow]N/A[/yellow] - GPU NVIDIA nao detectada (modo CPU)")
        results["gpu"] = False

    # 7. Diretorios
    console.print("[bold cyan][7/7] Verificando estrutura de diretorios...[/bold cyan]")
    required_dirs = ["core", "models", "vision", "control", "planning", "speech",
                     "hacker_tools", "config", "examples", "data", "logs", "tests", "scripts"]
    dirs_ok = 0
    for d in required_dirs:
        if (ROOT_DIR / d).exists():
            dirs_ok += 1
    console.print(f"  [green]OK[/green] - {dirs_ok}/{len(required_dirs)} diretorios presentes")
    results["dirs"] = dirs_ok == len(required_dirs)

    return results


async def run():
    # Banner
    banner = Text()
    banner.append("SH4D0WF0RG3", style="bold cyan")
    banner.append(" v1.0.0 | Health Check", style="cyan")
    console.print(Panel(banner, border_style="cyan", padding=(1, 2)))

    start = datetime.now()

    results = await check_subsystems()

    elapsed = (datetime.now() - start).total_seconds()

    # Tabela resumo
    table = Table(title="Resumo do Health Check", show_header=True, header_style="bold cyan")
    table.add_column("Subsistema", style="cyan", width=20)
    table.add_column("Status", width=15)

    labels = {
        "config_yaml": "Config YAML",
        "env_file": ".env / API Key",
        "nim_client": "NIM Client",
        "pydantic": "Pydantic Models",
        "modules": "Modulos Python",
        "gpu": "GPU NVIDIA",
        "dirs": "Diretorios",
    }

    for key, label in labels.items():
        ok = results.get(key, False)
        if ok:
            table.add_row(label, "[green]OK[/green]")
        else:
            table.add_row(label, "[yellow]SIMULACAO/N/A[/yellow]" if key in ("nim_client", "gpu") else "[red]FALHA[/red]")

    console.print()
    console.print(table)

    # Resultado final
    total_ok = sum(1 for v in results.values() if v)
    total = len(results)

    console.print(f"\n[bold]Verificacao completa em {elapsed:.1f}s[/bold]")
    console.print(f"[bold]{total_ok}/{total} subsistemas operacionais[/bold]\n")

    if total_ok >= total - 2:  # GPU e NIM sao opcionais
        console.print("[bold green]>> SH4D0WF0RG3 PRONTO PARA OPERAR[/bold green]")
        console.print("[dim]Modos disponiveis: stealth, agressivo, recon_only, debug[/dim]")
        console.print("[dim]Execute: python main.py --mode stealth --simulate[/dim]\n")
    else:
        console.print("[bold yellow]>> Alguns subsistemas precisam de atencao[/bold yellow]\n")


if __name__ == "__main__":
    asyncio.run(run())
