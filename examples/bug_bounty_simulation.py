"""
============================================================
 NVIDIA ShadowForge Agent - Exemplo: Bug Bounty Simulation
 Arquivo: examples/bug_bounty_simulation.py
 Descricao: Demo de workflow de bug bounty com deteccao
 visual, PoC generation e report automatico.
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
from rich.table import Table  # noqa: E402
from rich.tree import Tree  # noqa: E402

console = Console(force_terminal=True)


async def demo_bug_bounty() -> None:
    """Demo de workflow de bug bounty."""

    console.print(Panel.fit(
        "[bold cyan]SH4D0WF0RG3 // Bug Bounty Simulation[/bold cyan]\n"
        "[dim]Workflow automatico | PoC Generation | Report[/dim]",
        border_style="cyan"
    ))

    console.print("\n[bold yellow]=== BUG BOUNTY WORKFLOW ===[/bold yellow]")
    console.print("[dim]Plataforma: HackerOne | Programa: TestCorp VRP[/dim]")
    console.print("[dim]Scope: *.testcorp.com | Exclusoes: /api/internal/*[/dim]\n")

    # Arvore de scope
    tree = Tree("[bold cyan]testcorp.com[/bold cyan]")
    app = tree.add("[green]app.testcorp.com[/green]")
    app.add("[yellow]|-- /login[/yellow]")
    app.add("[yellow]|-- /dashboard[/yellow]")
    app.add("[yellow]|-- /api/v1/users[/yellow]")
    app.add("[yellow]\\-- /api/v1/orders[/yellow]")
    api = tree.add("[green]api.testcorp.com[/green]")
    api.add("[yellow]|-- /graphql[/yellow]")
    api.add("[yellow]\\-- /rest/v2[/yellow]")
    docs = tree.add("[green]docs.testcorp.com[/green]")
    docs.add("[yellow]\\-- /api-docs[/yellow]")

    console.print(tree)
    await asyncio.sleep(1)

    # Descobertas
    console.print("\n[bold green]--- DESCOBERTAS ---[/bold green]")

    bugs = [
        {
            "id": "BB-001",
            "tipo": "IDOR",
            "severidade": "HIGH",
            "local": "/api/v1/users/{id}",
            "descricao": "Acesso nao autorizado a dados de outros usuarios via manipulacao de ID",
            "poc": "GET /api/v1/users/1337 HTTP/1.1\\nAuthorization: Bearer <token_user_1>\\n-> Retorna dados de user_1337",
            "bounty": "$500-1500",
        },
        {
            "id": "BB-002",
            "tipo": "GraphQL Injection",
            "severidade": "CRITICAL",
            "local": "/graphql",
            "descricao": "Introspection query habilitada + mutation nao autorizada",
            "poc": '{"query": "{ __schema { types { name } } }"}\\n-> Full schema exposed',
            "bounty": "$2000-5000",
        },
        {
            "id": "BB-003",
            "tipo": "XSS Stored",
            "severidade": "HIGH",
            "local": "/dashboard/settings",
            "descricao": "XSS armazenado no campo de nome de usuario via Unicode bypass",
            "poc": '<svg/onload=alert(document.domain)>\\n-> Executa no dashboard de admin',
            "bounty": "$500-1500",
        },
    ]

    for bug in bugs:
        sev_color = {"CRITICAL": "bold red", "HIGH": "red", "MEDIUM": "yellow", "LOW": "blue"}

        console.print(f"\n[bold {sev_color.get(bug['severidade'], 'white')}]"
            f" [{bug['severidade']}] {bug['id']}: {bug['tipo']}[/bold {sev_color.get(bug['severidade'], 'white')}]")
        console.print(f"  [cyan]Local:[/cyan] {bug['local']}")
        console.print(f"  [cyan]Desc:[/cyan] {bug['descricao']}")
        console.print(f"  [cyan]PoC:[/cyan] {bug['poc']}")
        console.print(f"  [green]Bounty:[/green] {bug['bounty']}")

        await asyncio.sleep(0.8)

    # Relatorio final
    console.print("\n[bold green]--- RELATORIO BUG BOUNTY ---[/bold green]")

    report_table = Table(title="Resumo de Submissoes", show_header=True, header_style="bold cyan")
    report_table.add_column("ID", style="cyan")
    report_table.add_column("Tipo", style="green")
    report_table.add_column("Severidade")
    report_table.add_column("Bounty Est.")
    report_table.add_column("Status")

    report_table.add_row("BB-001", "IDOR", "[red]HIGH[/red]", "$500-1500", "[green]SUBMITTED[/green]")
    report_table.add_row("BB-002", "GraphQL Inj.", "[bold red]CRITICAL[/bold red]", "$2000-5000", "[green]SUBMITTED[/green]")
    report_table.add_row("BB-003", "XSS Stored", "[red]HIGH[/red]", "$500-1500", "[yellow]TRIAGE[/yellow]")

    console.print(report_table)

    console.print("\n[bold green] Bounty estimado total: $3,000 - $8,000[/bold green]")
    console.print("[cyan] Regras eticas: todas as vulnerabilidades reportadas ANTES de qualquer exploracao. [/cyan]")
    console.print("[cyan] Nenhum dado exfiltrado. Scope respeitado. >> [/cyan]\n")


if __name__ == "__main__":
    asyncio.run(demo_bug_bounty())
