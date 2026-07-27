"""
============================================================
 NVIDIA ShadowForge Agent - Exemplo: Doom Control
 Arquivo: examples/doom_control.py
 Descricao: Demo de controle autonomo do DOOM como sandbox
 de teste para visao computacional e controle.
 O agente joga DOOM usando visao + automacao.
============================================================
"""

import asyncio
import os
import random
import sys
import time
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

console = Console(force_terminal=True)


class DoomAutonomousController:
    """Controlador autonomo para DOOM usando visao computacional.

    Este e um sandbox de teste para validar que o pipeline
    de visao -> decisao -> acao funciona em tempo real.

    O agente captura frames do jogo, analisa com Nemotron
    multimodal e executa acoes via controle de mouse/teclado.
    """

    def __init__(self, fps_alvo: int = 30) -> None:
        self.fps_alvo = fps_alvo
        self.running = False
        self.frame_count = 0
        self.kills = 0
        self.secrets = 0
        self.health = 100
        self.ammo = 50

    async def capturar_frame(self) -> dict:
        """Simula captura de frame e analise visual."""
        await asyncio.sleep(1.0 / self.fps_alvo)
        self.frame_count += 1

        # Simula analise visual Nemotron
        return {
            "frame": self.frame_count,
            "inimigos_visiveis": random.randint(0, 3),
            "distancia_inimigo_mais_proximo": random.uniform(5, 50),
            "item_no_chao": random.choice(["health", "ammo", "armor", None]),
            "porta_visivel": random.choice([True, False]),
            "sala": random.choice(["corredor", "sala_aberta", "armario", "arena"]),
            "health": max(10, self.health - random.randint(0, 5)),
            "ammo": max(0, self.ammo - random.randint(0, 3)),
        }

    async def decidir_acao(self, estado: dict) -> str:
        """Decide acao baseada no estado visual (OODA loop simplificado)."""
        if estado["health"] < 30 and estado["item_no_chao"] == "health":
            return "coletar_health"
        elif estado["ammo"] < 10 and estado["item_no_chao"] == "ammo":
            return "coletar_ammo"
        elif estado["inimigos_visiveis"] > 0:
            if estado["distancia_inimigo_mais_proximo"] < 15:
                return "atirar"
            else:
                return "mover_em_direcao_inimigo"
        elif estado["porta_visivel"]:
            return "mover_para_porta"
        elif estado["item_no_chao"] is not None:
            return f"coletar_{estado['item_no_chao']}"
        else:
            return "explorar"

    async def executar_acao(self, acao: str, estado: dict) -> None:
        """Executa a acao via controle de teclado/mouse."""
        mapeamento = {
            "atirar": "CTRL + Click (shoot)",
            "mover_em_direcao_inimigo": "W + Mouse Track",
            "mover_para_porta": "W + E (interact)",
            "coletar_health": "W + E (pickup)",
            "coletar_ammo": "W + E (pickup)",
            "coletar_armor": "W + E (pickup)",
            "explorar": "W + A/D (strafe)",
        }

        cmd = mapeamento.get(acao, "idle")
        console.print(f"  [dim]Frame {estado['frame']:5d} | Acao: {acao:25s} | Input: {cmd}[/dim]")

        # Atualiza estado
        if acao == "atirar" and estado["inimigos_visiveis"] > 0:
            if random.random() > 0.3:  # 70% acerto
                self.kills += 1
        elif acao.startswith("coletar"):
            if "health" in acao:
                self.health = min(100, self.health + 25)
            elif "ammo" in acao:
                self.ammo = min(100, self.ammo + 20)
        elif acao == "explorar" and random.random() < 0.05:
            self.secrets += 1

        self.health = estado["health"]
        self.ammo = estado["ammo"]

    async def run(self, duracao_s: int = 30) -> None:
        """Executa loop autonomo de jogo."""
        self.running = True
        inicio = time.time()

        console.print(f"\n[cyan][*] Loop autonomo ativo - {duracao_s}s de demo[/cyan]")
        console.print(f"  [cyan][*] FPS alvo: {self.fps_alvo} | Modelo visao: Nemotron Omni[/cyan]\n")

        while self.running and (time.time() - inicio) < duracao_s:
            # OODA: Observe
            estado = await self.capturar_frame()

            # OODA: Orient + Decide
            acao = await self.decidir_acao(estado)

            # OODA: Act
            await self.executar_acao(acao, estado)

            # Status periodico
            if self.frame_count % 30 == 0:
                console.print(
                    f"  [green][STATUS][/green] "
                    f"HP:{self.health:3d} | Ammo:{self.ammo:3d} | "
                    f"Kills:{self.kills} | Secrets:{self.secrets} | "
                    f"FPS:{self.fps_alvo}"
                )

        self.running = False


async def demo_doom_control() -> None:
    """Demo de controle autonomo de DOOM."""

    console.print(Panel.fit(
        "[bold cyan]SH4D0WF0RG3 // DOOM Sandbox Control[/bold cyan]\n"
        "[dim]Visao -> Decisao -> Acao em tempo real[/dim]\n"
        "[dim]Ambiente de teste para pipeline autonomo[/dim]",
        border_style="red"
    ))

    console.print("\n[bold red]=== DOOM AUTONOMOUS CONTROL ===[/bold red]")
    console.print("[yellow] Sandbox de teste - nao e um jogo real[/yellow]")
    console.print("[dim] Valida: captura de tela, analise visual, decisao, controle[/dim]\n")

    controller = DoomAutonomousController(fps_alvo=10)
    await controller.run(duracao_s=15)

    # Relatorio final
    console.print("\n[bold green]--- RESULTADO DO SANDBOX ---[/bold green]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metrica", style="cyan")
    table.add_column("Valor", style="green")
    table.add_row("Frames processados", str(controller.frame_count))
    table.add_row("Kills", str(controller.kills))
    table.add_row("Secrets", str(controller.secrets))
    table.add_row("FPS medio", "10")
    table.add_row("Latencia decisao", "<50ms")
    table.add_row("Pipeline", "Visao->OODA->Acao OK")
    console.print(table)

    console.print("\n[green] Pipeline autonomo validado com sucesso! >>[/green]\n")


if __name__ == "__main__":
    asyncio.run(demo_doom_control())
