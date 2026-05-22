#!/usr/bin/env python3.11
"""
============================================================
 NVIDIA ShadowForge - Teste de Importacao de Todos os Modulos
 Arquivo: tests/test_imports.py
============================================================
 Verifica que todos os modulos Python do projeto importam
 sem erros, validando sintaxe e dependencias.
============================================================
"""

import importlib
import sys
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


MODULES = [
    "core.config",
    "core.state",
    "core.memory",
    "models.nim_client",
    "models.prompts",
    "models.riva_client",
    "vision.screen",
    "vision.ocr",
    "vision.detector",
    "vision.understanding",
    "control.mouse",
    "control.keyboard",
    "control.shell",
    "control.stealth",
    "hacker_tools.recon.osint",
    "hacker_tools.recon.scanner",
    "hacker_tools.exploit.network_attacks",
    "hacker_tools.exploit.web_attacks",
    "hacker_tools.post_exploitation.pivot",
    "hacker_tools.reporting.report_generator",
    "planning.orchestrator",
    "planning.rag",
    "speech.asr",
    "speech.tts",
    "speech.audio_utils",
    "speech.voice_interface",
    "examples.pentest_lab",
    "examples.bug_bounty_simulation",
    "examples.doom_control",
    "examples.voice_campaign",
]


def test_all_imports() -> None:
    ok_count = 0
    fail_count = 0
    failures = []

    for mod_name in MODULES:
        try:
            importlib.import_module(mod_name)
            ok_count += 1
            print(f"  [OK] {mod_name}")
        except Exception as e:
            fail_count += 1
            err_msg = str(e)[:80]
            failures.append(f"{mod_name}: {err_msg}")
            print(f"  [FALHA] {mod_name} - {err_msg}")

    assert fail_count == 0, f"{fail_count} módulos falharam: {failures}"


def main():
    print("\n" + "=" * 60)
    print("  NVIDIA ShadowForge - Teste de Importacao")
    print("=" * 60 + "\n")

    # Priming imports that need optional deps
    # Some modules have heavy deps - import core first
    print("Testando modulos:\n")

    try:
        test_all_imports()
        ok, fail, failures = len(MODULES), 0, []
    except AssertionError as exc:
        ok = len(MODULES)
        fail = 1
        failures = [str(exc)]

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Resultado: {ok} OK | {fail} FALHAS | {ok + fail} total")
    print(f"{'=' * 60}\n")

    if failures:
        print("Falhas detalhadas:")
        for f in failures:
            print(f"  - {f}")
        print()

    # Count lines
    total_lines = 0
    total_files = 0
    for py_file in ROOT_DIR.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            lines = len(py_file.read_text(encoding="utf-8").splitlines())
            total_lines += lines
            total_files += 1
        except Exception:
            pass

    print(f"  Arquivos Python: {total_files}")
    print(f"  Linhas Python: {total_lines}")
    print()

    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
