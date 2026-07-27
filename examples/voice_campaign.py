"""
============================================================
 NVIDIA ShadowForge Agent - Exemplo: Voice Campaign
 Arquivo: examples/voice_campaign.py
 Descricao: Demo de interface por voz para comandos de pentest
 usando NVIDIA Riva ASR/TTS.
============================================================
"""

import asyncio
import os
import sys
from pathlib import Path

# Forcar UTF-8 no Windows
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402

console = Console(force_terminal=True)


async def demo_voice_campaign() -> None:
    """Demo de campanha controlada por voz."""

    console.print(Panel.fit(
        "[bold cyan]SH4D0WF0RG3 // Voice Campaign Demo[/bold cyan]\n"
        "[dim]Interface voz full-duplex | Riva ASR/TTS[/dim]",
        border_style="cyan"
    ))

    console.print("\n[bold magenta]=== INTERFACE DE VOZ ===[/bold magenta]")
    console.print("[dim]Wake word: 'shadow'[/dim]")
    console.print("[dim]Comandos disponiveis: recon, scan, exploit, report, status, abort[/dim]\n")

    comandos = [
        ("OPERADOR", "Shadow, reconhece o alvo 192.168.1.0/24"),
        ("SH4D0WF0RG3", "Reconhecimento iniciado no range 192.168.1.0/24. "
         "Executando scan Nmap SYN com service detection. "
         "5 hosts ativos detectados, 23 portas abertas."),
        ("OPERADOR", "Shadow, enumera os servicos web"),
        ("SH4D0WF0RG3", "Enumeration web concluida. "
         "Detectado Apache 2.4.54 com WordPress 6.2. "
         "2 formularios de login e 1 API endpoint identificados."),
        ("OPERADOR", "Shadow, analisa possiveis SQLi no formulario de login"),
        ("SH4D0WF0RG3", "Analise de SQL injection em andamento. "
         "Parametro 'log' vulneravel a authentication bypass. "
         "PoC gerado. Severidade: CRITICA. CVSS 9.8."),
        ("OPERADOR", "Shadow, gera relatorio"),
        ("SH4D0WF0RG3", "Relatorio gerado com 5 vulnerabilidades. "
         "1 critica, 1 alta, 2 medias, 1 baixa. "
         "Score geral: 8.2 de 10. "
         "Arquivo salvo em data/campaigns/last_report.pdf"),
    ]

    for speaker, texto in comandos:
        if speaker == "OPERADOR":
            console.print(f"\n[bold green]MIC OPERADOR:[/bold green] {texto}")
            console.print("[dim]  [Riva ASR] Transcricao em 180ms | Confianca: 0.97[/dim]")
        else:
            console.print(f"\n[bold cyan]BOT SH4D0WF0RG3:[/bold cyan] {texto}")
            console.print("[dim]  [Riva TTS] Sintese em 95ms | Voz: cyber-masculino-pt[/dim]")
        await asyncio.sleep(1.2)

    console.print("\n[bold green]=== DEMO DE VOZ CONCLUIDA ===[/bold green]")
    console.print("[cyan]Latencia ASR: <250ms | TTS: <150ms | Full-duplex ativo[/cyan]\n")


if __name__ == "__main__":
    asyncio.run(demo_voice_campaign())
