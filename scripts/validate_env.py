#!/usr/bin/env python3.11
"""
============================================================
 NVIDIA ShadowForge - Script de Validacao do Ambiente
 Arquivo: scripts/validate_env.py
============================================================
 Verifica todas as dependencias, configuracoes e APIs
 antes de executar o agente principal.
============================================================
"""

import os
import subprocess
import sys
from pathlib import Path

# UTF-8 no Windows
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

try:
    from rich.console import Console
    from rich.panel import Panel  # noqa: F401
    from rich.table import Table
    console = Console(force_terminal=True)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def check_python_version() -> tuple[bool, str]:
    version = sys.version_info
    ok = version >= (3, 10)
    msg = f"{version.major}.{version.minor}.{version.micro}"
    return ok, msg


def check_package(pkg_name: str) -> tuple[bool, str]:
    try:
        __import__(pkg_name)
        return True, "OK"
    except ImportError:
        return False, "AUSENTE"


def check_nvidia_api() -> tuple[bool, str]:
    key = os.environ.get("NVIDIA_API_KEY", "")
    if not key:
        return False, "Nao configurada"
    if key.startswith("nvapi-xxxxx") or key == "your-nvidia-api-key":
        return False, "Key placeholder"
    return True, f"Configurada ({key[:10]}...)"


def check_gpu() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip().split("\n")[0]
        return False, "nvidia-smi falhou"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "Nao detectada"


def check_yaml_config() -> tuple[bool, str]:
    config_path = ROOT_DIR / "config" / "default.yaml"
    if not config_path.exists():
        return False, "Arquivo nao encontrado"
    try:
        import yaml
        with open(config_path, encoding="utf-8") as f:
            yaml.safe_load(f)
        return True, "OK"
    except Exception as e:
        return False, str(e)[:60]


def check_dotenv() -> tuple[bool, str]:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return False, ".env nao encontrado"
    return True, "OK"


def main():
    print("\n" + "=" * 60)
    print("  NVIDIA ShadowForge - Validacao de Ambiente")
    print("=" * 60 + "\n")

    checks = [
        ("Python >= 3.10", lambda: check_python_version()),
        ("PyYAML", lambda: check_package("yaml")),
        ("aiohttp", lambda: check_package("aiohttp")),
        ("pydantic", lambda: check_package("pydantic")),
        ("rich", lambda: check_package("rich")),
        ("Pillow", lambda: check_package("PIL")),
        ("python-dotenv", lambda: check_package("dotenv")),
        ("GPU NVIDIA", lambda: check_gpu()),
        ("API Key NVIDIA", lambda: check_nvidia_api()),
        ("Config YAML", lambda: check_yaml_config()),
        (".env", lambda: check_dotenv()),
    ]

    all_ok = True
    if HAS_RICH:
        table = Table(title="Verificacao de Ambiente", show_header=True, header_style="bold cyan")
        table.add_column("Componente", style="cyan", width=25)
        table.add_column("Status", width=10)
        table.add_column("Detalhe", style="dim")

        for name, check_fn in checks:
            ok, detail = check_fn()
            status = "[green]OK[/green]" if ok else "[red]FALHA[/red]"
            if not ok:
                all_ok = False
            table.add_row(name, status, detail)

        console.print(table)
    else:
        for name, check_fn in checks:
            ok, detail = check_fn()
            status = "OK" if ok else "FALHA"
            if not ok:
                all_ok = False
            print(f"  {name:25s} {status:10s} {detail}")

    # Resumo
    print()
    if all_ok:
        if HAS_RICH:
            console.print("[bold green]>> Ambiente OK! Pronto para executar.[/bold green]")
        else:
            print(">> Ambiente OK! Pronto para executar.")
    else:
        if HAS_RICH:
            console.print("[bold yellow]>> Algumas verificacoes falharam.[/bold yellow]")
            console.print("[yellow]Instale dependencias: pip install -r requirements.txt[/yellow]")
        else:
            print(">> Algumas verificacoes falharam.")
            print("Instale dependencias: pip install -r requirements.txt")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
