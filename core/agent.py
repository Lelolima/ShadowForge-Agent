"""
============================================================
 NVIDIA ShadowForge Agent - Motor Agentic Principal
 Arquivo: core/agent.py
============================================================
 Loop OODA (Observe-Orient-Decide-Act) completo com
 state machine de campanhas, self-correction, integração
 com visão, fala, controle, ferramentas e planejamento.
============================================================
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from rich.console import Console

from core.config import ModoOperacao, ShadowForgeConfig
from core.memory import MemoriaCurtoPrazo, MemoriLongoPrazo
from core.state import EstadoAgente, FaseOperacao

console = Console()
logger = logging.getLogger("shadowforge.core")


class ShadowForgeAgent:
    """Motor agentic principal do ShadowForge.

    Implementa loop OODA contínuo com state machine para
    campanhas de pentest autorizado. Coordena todos os
    subsistemas: visão, fala, controle, ferramentas e planejamento.

    Attributes:
        config: Configuração do agente
        estado: Estado atual da campanha
        memoria_cp: Memória de curto prazo
        memoria_lp: Memória de longo prazo
        running: Flag de execução
    """

    def __init__(
        self,
        config_path: str = "config/default.yaml",
        mode: str = "stealth",
        target: str | None = None,
        voice_enabled: bool = False,
        simulate: bool = False,
        gpu_id: int = 0,
        campaign: str | None = None,
    ) -> None:
        # Configuração
        try:
            self.config = ShadowForgeConfig.carregar_de_yaml(config_path)
        except FileNotFoundError:
            logger.warning("Config YAML não encontrado, usando padrão + env")
            self.config = ShadowForgeConfig.carregar_de_env()

        self.config.modo = ModoOperacao(mode)
        if target:
            self.config.alvo_inicial = target

        # Estado e memória
        db_path = self.config.data_dir / "state" / "shadowforge.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.estado = EstadoAgente(db_path=str(db_path))
        self.estado.alvo_principal = target
        if campaign:
            self.estado.campanha_id = campaign

        self.memoria_cp = MemoriaCurtoPrazo(capacidade=500)
        self.memoria_lp = MemoriLongoPrazo(
            db_path=self.config.data_dir / "memory" / "long_term.db"
        )

        # Flags
        self.running = False
        self.voice_enabled = voice_enabled
        self.simulate = simulate
        self.gpu_id = gpu_id
        self._iteracao = 0
        self._shutdown_event = asyncio.Event()

        # Subsistemas (lazy init)
        self._vision = None
        self._speech = None
        self._control = None
        self._hacker_tools = None
        self._planning = None
        self._models = None

        # Callbacks de progresso
        self._on_fase_change: list[Callable] = []
        self._on_vuln_found: list[Callable] = []
        self._on_acao_exec: list[Callable] = []

        logger.info(
            "ShadowForge Agent inicializado | Modo: %s | Alvo: %s",
            mode, target or "nenhum"
        )

    async def inicializar_subsistemas(self) -> None:
        """Inicializa todos os subsistemas de forma assíncrona."""
        logger.info("Inicializando subsistemas...")

        # Models (NVIDIA NIM/Riva)
        try:
            from models.multimodal import NemotronVision
            from models.nim_client import NIMClient
            from models.prompts import PromptManager

            self._models = {
                "nim": NIMClient(config=self.config.nvidia),
                "vision": NemotronVision(config=self.config.nvidia),
                "prompts": PromptManager(),
            }
            logger.info("[OK] Models NIM/Riva inicializados")
        except ImportError as e:
            logger.warning("Módulo models não disponível: %s (funcionando em modo limitado)", e)
            self._models = None

        # Visão
        try:
            from vision.ocr import OCRExtractor
            from vision.screen import ScreenCapture
            from vision.understanding import ScreenUnderstanding

            self._vision = {
                "capture": ScreenCapture(config=self.config),
                "understanding": ScreenUnderstanding(config=self.config),
                "ocr": OCRExtractor(config=self.config),
            }
            logger.info("[OK] Módulo visão inicializado")
        except ImportError as e:
            logger.warning("Módulo visão não disponível: %s", e)
            self._vision = None

        # Fala
        if self.voice_enabled:
            try:
                from speech.voice_interface import VoiceInterface
                self._speech = VoiceInterface(config=self.config)
                await self._speech.inicializar()
                logger.info("[OK] Módulo fala inicializado")
            except ImportError as e:
                logger.warning("Módulo fala não disponível: %s", e)
                self._speech = None

        # Controle
        try:
            from control.keyboard import StealthKeyboard
            from control.mouse import StealthMouse
            from control.shell import StealthShell

            self._control = {
                "mouse": StealthMouse(),
                "keyboard": StealthKeyboard(),
                "shell": StealthShell(config=self.config),
            }
            logger.info("[OK] Módulo controle inicializado")
        except ImportError as e:
            logger.warning("Módulo controle não disponível: %s", e)
            self._control = None

        # Ferramentas hacker
        try:
            from hacker_tools.exploit.web_attacks import WebExploiter
            from hacker_tools.recon.scanner import ReconScanner
            from hacker_tools.reporting.report_generator import ReportGenerator

            self._hacker_tools = {
                "recon": ReconScanner(config=self.config),
                "web_exploit": WebExploiter(config=self.config),
                "report": ReportGenerator(),
            }
            logger.info("[OK] Módulo ferramentas hacker inicializado")
        except ImportError as e:
            logger.warning("Módulo hacker_tools não disponível: %s", e)
            self._hacker_tools = None

        # Planejamento
        try:
            from planning.orchestrator import CampaignOrchestrator
            from planning.rag import MITRERAG

            self._planning = {
                "orchestrator": CampaignOrchestrator(config=self.config),
                "rag": MITRERAG(config=self.config),
            }
            logger.info("[OK] Módulo planejamento inicializado")
        except ImportError as e:
            logger.warning("Módulo planning não disponível: %s", e)
            self._planning = None

    async def run(self) -> None:
        """Loop principal do agente — OODA contínuo."""
        self.running = True
        await self.inicializar_subsistemas()

        logger.info("SH4D0WF0RG3 ONLINE | Loop OODA iniciando...")
        console.print("\n[bold green]SH4D0WF0RG3 ONLINE | Loop OODA iniciando...[/bold green]")
        console.print(f"[dim]Alvo: {self.estado.alvo_principal or 'Nenhum'} | Modo: {self.config.modo.value} | Simulacao: {self.simulate}[/dim]")
        console.print(f"[dim]Max iteracoes: {self.config.ooda.max_iteracoes} | Timeout: {self.config.ooda.timeout_campanha_min}min[/dim]\n")

        try:
            while self.running and not self._shutdown_event.is_set():
                if self._iteracao >= self.config.ooda.max_iteracoes:
                    logger.warning("Limite de iterações atingido: %d", self._iteracao)
                    break

                # Verifica timeout da campanha
                duracao_min = (datetime.now() - self.estado.inicio).total_seconds() / 60
                if duracao_min >= self.config.ooda.timeout_campanha_min:
                    logger.warning("Timeout da campanha atingido: %.1f min", duracao_min)
                    break

                try:
                    await self._ooda_cycle()
                    self._iteracao += 1
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.exception("Erro no ciclo OODA: %s", e)
                    await asyncio.sleep(self.config.ooda.intervalo_act_ms / 1000)

        finally:
            self.running = False
            logger.info("SH4D0WF0RG3 OFFLINE | Iterações: %d", self._iteracao)

    async def _ooda_cycle(self) -> None:
        """Executa um ciclo completo do loop OODA."""
        console.print(f"\n[bold cyan]>> Ciclo OODA #{self._iteracao + 1}[/bold cyan]")

        # === OBSERVE ===
        observacoes = await self._observe()
        console.print(f"  [cyan][OBSERVE][/cyan] {len(observacoes)} observacoes coletadas")
        await asyncio.sleep(self.config.ooda.intervalo_observe_ms / 1000)

        # === ORIENT ===
        orientacao = await self._orient(observacoes)
        fase_str = orientacao.get("fase_atual", "N/A")
        tecnicas = orientacao.get("tecnicas_sugeridas", [])
        console.print(f"  [yellow][ORIENT][/yellow] Fase: {fase_str} | Tecnicas RAG: {len(tecnicas)}")
        await asyncio.sleep(self.config.ooda.intervalo_orient_ms / 1000)

        # === DECIDE ===
        decisao = await self._decide(orientacao)
        acao = decisao.get("acao", "none")
        if acao == "etica_bloqueada":
            console.print(f"  [bold red][DECIDE][/bold red] BLOQUEADA: {decisao.get('acao_original', '?')} - {decisao.get('motivo', '')}")
        else:
            console.print(f"  [green][DECIDE][/green] Acao: {acao}")
        await asyncio.sleep(self.config.ooda.intervalo_decide_ms / 1000)

        # === ACT ===
        resultado = await self._act(decisao)
        sucesso = resultado.get("sucesso", False)
        status_icon = "[green]OK[/green]" if sucesso else "[red]FALHA[/red]"
        console.print(f"  [bold green][ACT][/bold green] Resultado: {status_icon} | {acao}")

        # Registra na memória
        self.memoria_cp.adicionar(
            tipo="ooda_cycle",
            conteudo=f"Obs:{len(observacoes)} | Fase:{self.estado.fase_atual.value} | Ação:{decisao.get('acao', 'none')}",
            importancia=0.7 if resultado.get("sucesso") else 0.3,
        )

    async def _observe(self) -> list[dict[str, Any]]:
        """Fase OBSERVE do OODA — coleta informações do ambiente."""
        observacoes = []

        # Captura de tela (visão)
        if self._vision and self._vision.get("capture"):
            try:
                screenshot = await self._vision["capture"].capturar()
                if screenshot:
                    observacoes.append({
                        "tipo": "screenshot",
                        "dados": screenshot,
                        "timestamp": datetime.now().isoformat(),
                    })

                    # Análise visual
                    if self._vision.get("understanding"):
                        analise = await self._vision["understanding"].analisar(screenshot)
                        if analise:
                            observacoes.append({
                                "tipo": "analise_visual",
                                "dados": analise,
                            })

                    # OCR
                    if self._vision.get("ocr"):
                        texto = await self._vision["ocr"].extrair(screenshot)
                        if texto:
                            observacoes.append({
                                "tipo": "ocr",
                                "dados": texto,
                            })
            except Exception as e:
                logger.debug("Erro na captura visual: %s", e)

        # Comando de voz (se habilitado)
        if self._speech:
            try:
                comando_voz = await self._speech.ouvir_comando()
                if comando_voz:
                    observacoes.append({
                        "tipo": "comando_voz",
                        "dados": comando_voz,
                    })
            except Exception as e:
                logger.debug("Erro no ASR: %s", e)

        # Estado do shell/processos
        if self._control and self._control.get("shell"):
            try:
                processos = await self._control["shell"].listar_processos()
                observacoes.append({
                    "tipo": "processos",
                    "dados": processos,
                })
            except Exception:
                pass

        return observacoes

    async def _orient(self, observacoes: list[dict]) -> dict[str, Any]:
        """Fase ORIENT do OODA — analisa e contextualiza observações."""
        orientacao = {
            "observacoes_processadas": len(observacoes),
            "fase_atual": self.estado.fase_atual.value,
            "alvo": self.estado.alvo_principal,
            "vulnerabilidades_conhecidas": len(self.estado.vulnerabilidades),
            "acoes_executadas": len(self.estado.acoes),
            "memoria_recente": self.memoria_cp.contexto_recente(5),
        }

        # RAG para técnicas relevantes
        if self._planning and self._planning.get("rag"):
            try:
                contexto_tatico = await self._planning["rag"].buscar_tecnicas(
                    fase=self.estado.fase_atual.value,
                    alvo=self.estado.alvo_principal or "",
                )
                orientacao["tecnicas_sugeridas"] = contexto_tatico
            except Exception:
                pass

        # Lices aprendidas
        try:
            licoes = await self.memoria_lp.recuperar_licoes(limite=5)
            orientacao["licoes"] = [licao.conteudo for licao in licoes]
        except Exception:
            orientacao["licoes"] = []

        return orientacao

    async def _decide(self, orientacao: dict[str, Any]) -> dict[str, Any]:
        """Fase DECIDE do OODA — escolhe a próxima ação."""
        fase = self.estado.fase_atual

        # Mapeamento de ações por fase
        acoes_por_fase = {
            FaseOperacao.IDLE: self._decidir_inicio,
            FaseOperacao.RECON: self._decidir_recon,
            FaseOperacao.SCAN: self._decidir_scan,
            FaseOperacao.ENUM: self._decidir_enum,
            FaseOperacao.EXPLOIT: self._decidir_exploit,
            FaseOperacao.POST: self._decidir_post,
            FaseOperacao.REPORT: self._decidir_report,
            FaseOperacao.COMPLETED: self._decidir_conclusao,
        }

        decisao_fn = acoes_por_fase.get(fase, self._decidir_inicio)
        decisao = await decisao_fn(orientacao)

        # Guardrail ético
        acao_nome = decisao.get("acao", "")
        alvo = decisao.get("alvo", self.estado.alvo_principal or "")
        permitido, motivo = self.config.verificar_etica(acao_nome, alvo)

        if not permitido:
            logger.warning("AÇÃO BLOQUEADA: %s | Motivo: %s", acao_nome, motivo)
            decisao = {
                "acao": "etica_bloqueada",
                "motivo": motivo,
                "acao_original": acao_nome,
            }

        return decisao

    async def _decidir_inicio(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase IDLE — iniciar reconhecimento."""
        if self.estado.alvo_principal:
            self.estado.fase_atual = FaseOperacao.RECON
            return {"acao": "iniciar_recon", "alvo": self.estado.alvo_principal}
        return {"acao": "aguardar_alvo"}

    async def _decidir_recon(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase RECON — scanning e enumeration."""
        if self._hacker_tools and self._hacker_tools.get("recon"):
            return {"acao": "executar_recon", "alvo": self.estado.alvo_principal}
        return {"acao": "avancar_fase", "proxima": "scan"}

    async def _decidir_scan(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase SCAN."""
        return {"acao": "executar_scan", "alvo": self.estado.alvo_principal}

    async def _decidir_enum(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase ENUM."""
        return {"acao": "executar_enum", "alvo": self.estado.alvo_principal}

    async def _decidir_exploit(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase EXPLOIT."""
        if self.estado.vulnerabilidades:
            vuln = self.estado.vulnerabilidades[0]
            return {"acao": "gerar_poc", "vulnerabilidade": vuln.id}
        return {"acao": "avancar_fase", "proxima": "post"}

    async def _decidir_post(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase POST-EXPLOITATION."""
        return {"acao": "analisar_privesc", "alvo": self.estado.alvo_principal}

    async def _decidir_report(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase REPORT."""
        return {"acao": "gerar_relatorio"}

    async def _decidir_conclusao(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase COMPLETED."""
        self.running = False
        return {"acao": "finalizar_campanha"}

    async def _act(self, decisao: dict[str, Any]) -> dict[str, Any]:
        """Fase ACT do OODA — executa a acao decidida."""
        acao = decisao.get("acao", "none")
        resultado = {"sucesso": False, "acao": acao}

        if acao == "etica_bloqueada":
            logger.warning("Acao bloqueada por guardrails eticos: %s", decisao.get("motivo"))
            self.estado.registrar_acao(
                fase=self.estado.fase_atual.value,
                tipo="etica_bloqueada",
                descricao=f"Acao {decisao.get('acao_original')} bloqueada",
                resultado=decisao.get("motivo", ""),
                autorizada=False,
                motivo_etico=decisao.get("motivo", ""),
            )
            return {"sucesso": False, "motivo": "etica_bloqueada"}

        if acao == "iniciar_recon":
            console.print(f"    [dim]Iniciando reconhecimento em {self.estado.alvo_principal}[/dim]")
            self.estado.avancar_fase()
            resultado = {"sucesso": True}

        elif acao == "executar_recon":
            console.print("    [dim]Executando reconhecimento ativo...[/dim]")
            if self._hacker_tools and self._hacker_tools.get("recon"):
                try:
                    recon_result = await self._hacker_tools["recon"].executar_full_recon(
                        alvo=self.estado.alvo_principal,
                        simulate=self.simulate,
                    )
                    resultado = {"sucesso": True, "dados": recon_result}
                except Exception as e:
                    logger.error("Erro no recon: %s", e)
                    resultado = {"sucesso": False, "erro": str(e)}
            else:
                resultado = {"sucesso": True, "dados": {"status": "simulado"}}
            self.estado.avancar_fase()

        elif acao == "executar_scan":
            console.print("    [dim]Executando port scan (simulado)...[/dim]")
            await asyncio.sleep(0.5)
            resultado = {"sucesso": True, "portas": [22, 80, 443, 3306, 8080]}
            self.estado.avancar_fase()

        elif acao == "executar_enum":
            console.print("    [dim]Enumerando servicos (simulado)...[/dim]")
            await asyncio.sleep(0.3)
            resultado = {"sucesso": True, "servicos": ["SSH", "HTTP", "MySQL"]}
            self.estado.avancar_fase()

        elif acao == "gerar_poc":
            console.print("    [dim]Gerando PoC para vulnerabilidade...[/dim]")
            await asyncio.sleep(0.3)
            vuln_id = decisao.get("vulnerabilidade", "unknown")
            resultado = {"sucesso": True, "poc": f"PoC para {vuln_id}"}
            self.estado.avancar_fase()

        elif acao == "analisar_privesc":
            console.print("    [dim]Analisando privilege escalation...[/dim]")
            await asyncio.sleep(0.3)
            resultado = {"sucesso": True, "vetores": ["SUID binary", "kernel exploit"]}
            self.estado.avancar_fase()

        elif acao == "gerar_relatorio":
            console.print("    [dim]Gerando relatorio final...[/dim]")
            if self._hacker_tools and self._hacker_tools.get("report"):
                try:
                    report = await self._hacker_tools["report"].gerar(
                        estado=self.estado,
                    )
                    resultado = {"sucesso": True, "relatorio": report}
                except Exception as e:
                    logger.error("Erro no relatorio: %s", e)
                    resultado = {"sucesso": True, "relatorio": "Relatorio simulado"}
            else:
                resultado = {"sucesso": True, "relatorio": "Relatorio simulado"}
            self.estado.avancar_fase()

        elif acao == "avancar_fase":
            console.print("    [dim]Avancando para proxima fase...[/dim]")
            self.estado.avancar_fase()
            resultado = {"sucesso": True}

        elif acao == "aguardar_alvo":
            console.print("    [dim]Aguardando definicao de alvo...[/dim]")
            resultado = {"sucesso": True}
            # Sem alvo, para o loop apos 3 iteracoes
            if self._iteracao > 3:
                self.running = False

        elif acao == "finalizar_campanha":
            console.print("    [bold green]Campanha finalizada![/bold green]")
            resultado = {"sucesso": True}
            self.running = False

        else:
            console.print(f"    [yellow]Acao nao reconhecida: {acao} - avancando fase[/yellow]")
            self.estado.avancar_fase()
            resultado = {"sucesso": True}

        # Fase COMPLETED — parar o loop
        if self.estado.fase_atual == FaseOperacao.COMPLETED:
            console.print("\n[bold green]=== CAMPANHA CONCLUIDA ===[/bold green]")
            console.print("[cyan]Fases completadas: IDLE -> RECON -> SCAN -> ENUM -> EXPLOIT -> POST -> REPORT[/cyan]")
            console.print(f"[cyan]Iteracoes OODA: {self._iteracao + 1}[/cyan]")
            console.print("[cyan]Ethics first, hack second. >>[/cyan]\n")
            self.running = False

        # Registra acao no audit trail
        self.estado.registrar_acao(
            fase=self.estado.fase_atual.value,
            tipo=acao,
            descricao=f"Executou {acao}",
            alvo=decisao.get("alvo", ""),
            sucesso=resultado.get("sucesso", False),
            autorizada=True,
        )

        return resultado

    async def shutdown(self) -> None:
        """Desligamento gracioso do agente."""
        logger.info("Desligando SH4D0WF0RG3...")
        self.running = False
        self._shutdown_event.set()

        # Salva memória de longo prazo
        try:
            for entrada in self.memoria_cp.buscar_recentes(50):
                if entrada.importancia >= 0.7:
                    await self.memoria_lp.armazenar(entrada)
        except Exception as e:
            logger.error("Erro ao salvar memória: %s", e)

        # Fecha NIM client (evita "Unclosed client session")
        if self._models and self._models.get("nim"):
            with contextlib.suppress(Exception):
                await self._models["nim"].fechar()

        # Fecha subsistemas
        if self._speech:
            with contextlib.suppress(Exception):
                await self._speech.finalizar()

        logger.info("SH4D0WF0RG3 OFFLINE | Memória persistida")

    def registrar_callback_fase(self, callback: Callable) -> None:
        """Registra callback para mudanças de fase."""
        self._on_fase_change.append(callback)

    def registrar_callback_vuln(self, callback: Callable) -> None:
        """Registra callback para vulnerabilidades encontradas."""
        self._on_vuln_found.append(callback)
