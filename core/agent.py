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
from typing import Any, TypedDict, Optional, List, TypedDict, List, Optional, Dict

from rich.console import Console

from core.config import ModoOperacao, ShadowForgeConfig
from core.memory import MemoriaCurtoPrazo, MemoriaLongoPrazo
from core.state import EstadoAgente, FaseOperacao
from core.event_bus import EventBus, EventoShadowForge, TipoEvento, PrioridadeEvento
from core.plugins import PluginManager
from core.action_strategies import (
    AcaoStrategy,
    ExecutarReconStrategy,
    ExecutarScanStrategy,
    ExecutarEnumStrategy,
    GerarPOCStrategy,
    AnalisarPrivEscStrategy,
    GerarRelatorioStrategy,
    IniciarReconStrategy,
    AguardarAlvoStrategy,
    AvançarFaseStrategy,
    FinalizarCampanhaStrategy,
    EticaBloqueadaStrategy,
    AcaoNaoReconhecidaStrategy,
)
from core.ooda_template import ODDATemplate
from core.subsystem_factory import (
    create_event_bus,
    create_plugin_manager,
    create_dashboard,
    create_models,
    create_vision,
    create_speech,
    create_control,
    create_hacker_tools,
    create_planning,
)

console = Console()
logger = logging.getLogger("shadowforge.core")


# TypedDict definitions for OEDA method return types
class ObservationDict(TypedDict, total=False):
    """Tipo para observações coletadas na fase OBSERVE do loop OODA.

    Attributes:
        tipo: str - Tipo da observação coletada (ex: "screenshot", "ocr",
                  "comando_voz", "processos", "analise_visual")
        dados: Any - Conteúdo da observação, cujo tipo varia conforme 'tipo':
                  - Para "screenshot": bytes da imagem capturada
                  - Para "ocr": texto extraído da imagem
                  - Para "comando_voz": string com o comando reconhecido
                  - Para "processos": lista de processos em execução
                  - Para "analise_visual": dict com descrição da cena
        timestamp: str - Timestamp ISO 8601 quando a observação foi coletada
                      (formato: YYYY-MM-DDTHH:MM:SS.mmmmmm)
    """
    tipo: str
    dados: Any
    timestamp: str


class OrientationDict(TypedDict, total=False):
    """Tipo para orientação calculada na fase ORIENT do loop OODA.

    Esta classe representa o contexto analisado após a observação, usado para
    informar a tomada de decisão na fase DECIDE.

    Attributes:
        observacoes_processadas: int - Número total de observações processadas
                                   neste ciclo OODA
        fase_atual: str - Fase atual do agente (ex: "recon", "scan", "enum",
                         "exploit", "post", "report")
        alvo: Optional[str] - Alvo atual da operação (domínio ou IP sendo testado)
        vulnerabilidades_conhecidas: int - Quantidade de vulnerabilidades já
                                        descobertas nesta campanha
        acoes_executadas: int - Número total de ações executadas até agora
        memoria_recente: List[Dict[str, Any]] - Contexto recente da memória
                                             de curto prazo (últimas 5 entradas)
        tecnicas_sugeridas: List[Dict[str, Any]] - Técnicas de pentest
                                                 sugeridas pelo sistema RAG
                                                 baseadas na fase atual e alvo
        licoes: List[str] - Lições aprendidas relevantes recuperadas da
                           memória de longo prazo para orientar a ação
    """
    observacoes_processadas: int
    fase_atual: str
    alvo: Optional[str]
    vulnerabilidades_conhecidas: int
    acoes_executadas: int
    memoria_recente: List[Dict[str, Any]]
    tecnicas_sugeridas: List[Dict[str, Any]]
    licoes: List[str]


class DecisionDict(TypedDict, total=False):
    """Tipo para decisão tomada na fase DECIDE do loop OODA.

    Esta classe representa a decisão tomada após a orientação, contendo
    a ação a ser executada e seu contexto.

    Attributes:
        acao: str - Nome da ação a ser executada (ex: "executar_recon",
                   "executar_scan", "gerar_poc", "etica_bloqueada")
        alvo: Optional[str] - Alvo da ação (domínio, IP ou None se não aplicável)
        motivo: Optional[str] - Justificativa ou explicação para a decisão tomada
        acao_original: Optional[str] - Ação original antes da aplicação dos
                                     guardrails éticos (None se não foi modificada)
        sucesso: bool - Indicador esperado de sucesso da ação (True para ações
                       normais, False para ações de bloqueio ou erro)
    """
    acao: str
    alvo: Optional[str]
    motivo: Optional[str]
    acao_original: Optional[str]
    sucesso: bool


class ActionResultDict(TypedDict, total=False):
    """Tipo para resultado da ação na fase ACT do loop OODA.

    Esta classe representa o resultado da execução de uma ação,
    indicando sucesso ou falha e qualquer informação relevante.

    Attributes:
        sucesso: bool - Indica se a ação foi executada com sucesso
        relatorio: Optional[str] - Relatório detalhado da ação (se aplicável)
                                 Ex: saída de comando, dados coletados, etc.
        erro: Optional[str] - Mensagem de erro em caso de falha (None se sucesso)
    """
    sucesso: bool
    relatorio: Optional[str]
    erro: Optional[str]


class ShadowForgeAgent(ODDATemplate):
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
        self.memoria_lp = MemoriaLongoPrazo(
            db_path=self.config.data_dir / "memory" / "long_term.db"
        )

        # Flags
        self.running = False
        self.voice_enabled = voice_enabled
        self.simulate = simulate
        self.gpu_id = gpu_id
        self._iteracao = 0
        self._shutdown_event = asyncio.Event()

        # Event Bus (comunicação pub/sub entre módulos)
        self.event_bus = EventBus()

        # Plugin Manager (extensibilidade dinâmica)
        self.plugin_manager = PluginManager(self.event_bus)

        # Subsistemas (lazy init)
        self._vision = None
        self._speech = None
        self._control = None
        self._hacker_tools = None
        self._planning = None
        self._models = None
        self._dashboard = None

        # Estratégias de ação (padrão Strategy) - serão inicializadas após subsistemas
        self._acao_estrategias: dict[str, AcaoStrategy] = {}
        self._estrategia_padrao = AcaoNaoReconhecidaStrategy()

        # Callbacks de progresso
        self._on_fase_change: list[Callable] = []
        self._on_vuln_found: list[Callable] = []
        self._on_acao_exec: list[Callable] = []

        # Estratégias de ação (padrão Strategy) - inicia as que não dependem de subsistemas
        self._acao_estrategias: dict[str, AcaoStrategy] = {
            "iniciar_recon": IniciarReconStrategy(),
            "executar_scan": ExecutarScanStrategy(),
            "executar_enum": ExecutarEnumStrategy(),
            "gerar_poc": GerarPOCStrategy(),
            "analisar_privesc": AnalisarPrivEscStrategy(),
            "avancar_fase": AvançarFaseStrategy(),
            "aguardar_alvo": AguardarAlvoStrategy(),
            "finalizar_campanha": FinalizarCampanhaStrategy(),
            "etica_bloqueada": EticaBloqueadaStrategy(),
        }
        self._estrategia_padrao = AcaoNaoReconhecidaStrategy()

        logger.info(
            "ShadowForge Agent inicializado | Modo: %s | Alvo: %s",
            mode, target or "nenhum"
        )

    def _atualizar_estrategias_com_subsistemas(self) -> None:
        """Atualiza estratégias que dependem de subsistemas após inicialização."""
        if self._hacker_tools:
            # Atualiza estratégias que dependem de hacker_tools
            self._acao_estrategias["executar_recon"] = ExecutarReconStrategy(
                hacker_tools=self._hacker_tools, simulate=self.simulate
            )
            self._acao_estrategias["gerar_relatorio"] = GerarRelatorioStrategy(
                hacker_tools=self._hacker_tools
            )

    async def inicializar_subsistemas(self) -> None:
        """Inicializa todos os subsistemas usando o padrão Factory."""
        logger.info("Inicializando subsistemas...")

        # Inicializa subsistemas via Factory
        subsystems_initialized = []

        # Event Bus (deve ser o primeiro — todos os módulos dependem dele)
        try:
            self.event_bus = create_event_bus(self)
            await self.event_bus.start()
            logger.info("[OK] Event Bus inicializado")
            subsystems_initialized.append("Event Bus")
        except Exception as e:
            logger.warning("Event Bus falhou: %s", e)

        # Plugin Manager
        try:
            self.plugin_manager = create_plugin_manager(self)
            await self.plugin_manager.load_all()
            logger.info("[OK] Plugin Manager inicializado (%d plugins)", len(self.plugin_manager.list_plugins()))
            subsystems_initialized.append("Plugin Manager")
        except Exception as e:
            logger.warning("Plugin Manager falhou: %s", e)

        # Dashboard API
        try:
            self._dashboard = create_dashboard(self)
            if self._dashboard:
                from api.dashboard import update_dashboard_state
                update_dashboard_state("agente_online", True)
                update_dashboard_state("fase_atual", self.estado.fase_atual.value)
                update_dashboard_state("alvo", self.estado.alvo_principal or "")
                logger.info("[OK] Dashboard API inicializado")
                subsystems_initialized.append("Dashboard API")
        except ImportError:
            logger.debug("Dashboard API não disponível (FastAPI não instalado)")
            self._dashboard = None

        # Models (NVIDIA NIM/Riva)
        try:
            self._models = create_models(self)
            logger.info("[OK] Models NIM/Riva inicializados")
            subsystems_initialized.append("Models")
        except ImportError as e:
            logger.warning("Módulo models não disponível: %s (funcionando em modo limitado)", e)
            self._models = None

        # Visão
        try:
            self._vision = create_vision(self)
            logger.info("[OK] Módulo visão inicializado")
            subsystems_initialized.append("Visão")
        except ImportError as e:
            logger.warning("Módulo visão não disponível: %s", e)
            self._vision = None

        # Fala
        if self.voice_enabled:
            try:
                self._speech = create_speech(self)
                await self._speech.inicializar()
                logger.info("[OK] Módulo fala inicializado")
                subsystems_initialized.append("Fala")
            except ImportError as e:
                logger.warning("Módulo fala não disponível: %s", e)
                self._speech = None

        # Controle
        try:
            self._control = create_control(self)
            logger.info("[OK] Módulo controle inicializado")
            subsystems_initialized.append("Controle")
        except ImportError as e:
            logger.warning("Módulo controle não disponível: %s", e)
            self._control = None

        # Ferramentas hacker
        try:
            self._hacker_tools = create_hacker_tools(self)
            logger.info("[OK] Módulo ferramentas hacker inicializado")
            subsystems_initialized.append("Ferramentas Hacker")
        except ImportError as e:
            logger.warning("Módulo hacker_tools não disponível: %s", e)
            self._hacker_tools = None

        # Planejamento
        try:
            self._planning = create_planning(self)
            logger.info("[OK] Módulo planejamento inicializado")
            subsystems_initialized.append("Planejamento")
        except ImportError as e:
            logger.warning("Módulo planning não disponível: %s", e)
            self._planning = None

        # Atualiza estratégias que dependem de subsistemas
        self._atualizar_estrategias_com_subsistemas()

        logger.info(
            "Subsistemas inicializados: %s",
            ", ".join(subsystems_initialized) if subsystems_initialized else "Nenhum"
        )

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
                    await self.execute_ooda_cycle()
                    self._iteracao += 1
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.exception("Erro no ciclo OODA: %s", e)
                    await asyncio.sleep(self.config.ooda.intervalo_act_ms / 1000)

        finally:
            self.running = False
            logger.info("SH4D0WF0RG3 OFFLINE | Iterações: %d", self._iteracao)

    async def execute_ooda_cycle(self) -> None:
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

    async def _observe(self) -> List[ObservationDict]:
        """Fase OBSERVE do OODA — coleta informações do ambiente."""
        observacoes: List[ObservationDict] = []

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
            except Exception as e:
                pass

        return observacoes

    async def _orient(self, observacoes: List[ObservationDict]) -> OrientationDict:
        """Fase ORIENT do OODA — analisa e contextualiza observações."""
        orientacao: OrientationDict = {
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
            except Exception as e:
                pass

        # Lições aprendidas
        try:
            licoes = await self.memoria_lp.recuperar_licoes(limite=5)
            orientacao["licoes"] = [licao.conteudo for licao in licoes]
        except Exception as e:
            orientacao["licoes"] = []

        return orientacao

    async def _decide(self, orientacao: OrientationDict) -> DecisionDict:
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

    async def _decidir_inicio(self, orientacao: OrientationDict) -> DecisionDict:
        """Decisão para fase IDLE — iniciar reconhecimento."""
        if self.estado.alvo_principal:
            self.estado.fase_atual = FaseOperacao.RECON
            return {"acao": "iniciar_recon", "alvo": self.estado.alvo_principal}
        return {"acao": "aguardar_alvo"}

    async def _decidir_recon(self, orientacao: OrientationDict) -> DecisionDict:
        """Decisão para fase RECON — scanning e enumeration."""
        if self._hacker_tools and self._hacker_tools.get("recon"):
            tecnicas = orientacao.get("tecnicas_sugeridas", [])
            return {
                "acao": "executar_recon",
                "alvo": self.estado.alvo_principal,
                "tecnicas_rag": len(tecnicas),
            }
        return {"acao": "avancar_fase", "proxima": "scan"}

    async def _decidir_scan(self, orientacao: OrientationDict) -> DecisionDict:
        """Decisão para fase SCAN — usa técnicas RAG se disponíveis."""
        tecnicas = orientacao.get("tecnicas_sugeridas", [])
        tipo_scan = "syn"
        if tecnicas:
            # Seleciona técnica mais relevante do RAG
            for t in tecnicas:
                if isinstance(t, dict) and t.get("tipo_scan"):
                    tipo_scan = t["tipo_scan"]
                    break
        return {
            "acao": "executar_scan",
            "alvo": self.estado.alvo_principal,
            "tipo_scan": tipo_scan,
            "tecnicas_rag": len(tecnicas),
        }

    async def _decidir_enum(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase ENUM — enumera serviços e vulnerabilidades."""
        tecnicas = orientacao.get("tecnicas_sugeridas", [])
        licoes = orientacao.get("licoes", [])
        return {
            "acao": "executar_enum",
            "alvo": self.estado.alvo_principal,
            "tecnicas_rag": len(tecnicas),
            "licoes": len(licoes),
        }

    async def _decidir_exploit(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase EXPLOIT — prioriza vulnerabilidades por severidade."""
        if self.estado.vulnerabilidades:
            # Ordena por severidade para explorar a mais crítica primeiro
            ordem_severidade = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
            vulns_ordenadas = sorted(
                self.estado.vulnerabilidades,
                key=lambda v: ordem_severidade.get(v.severidade.value, 5),
            )
            vuln = vulns_ordenadas[0]
            return {"acao": "gerar_poc", "vulnerabilidade": vuln.id}
        return {"acao": "avancar_fase", "proxima": "post"}

    async def _decidir_post(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase POST-EXPLOITATION — usa lições do RAG."""
        licoes = orientacao.get("licoes", [])
        return {
            "acao": "analisar_privesc",
            "alvo": self.estado.alvo_principal,
            "licoes_rag": len(licoes),
        }

    async def _decidir_report(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase REPORT."""
        return {"acao": "gerar_relatorio"}

    async def _decidir_conclusao(self, orientacao: dict) -> dict[str, Any]:
        """Decisão para fase COMPLETED."""
        self.running = False
        return {"acao": "finalizar_campanha"}

    async def _act(self, decisao: DecisionDict) -> ActionResultDict:
        """Fase ACT do OODA — executa a acao decidida."""
        acao = decisao.get("acao", "none")
        resultado: ActionResultDict = {"sucesso": False, "acao": acao}

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

        # M-06 FIX: Usar fase_anterior (se disponível) para registrar ação na fase correta.
        # registrar_acao acontece DEPOIS de avancar_fase(), então fase_atual já avançou.
        # Usamos fase_anterior para registrar a ação na fase em que foi executada.
        fase_registro = self.estado.fase_anterior.value if self.estado.fase_anterior else self.estado.fase_atual.value
        self.estado.registrar_acao(
            fase=fase_registro,
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

        # Q-03 FIX: Fecha conexão persistente com banco de memória de longo prazo
        with contextlib.suppress(Exception):
            await self.memoria_lp.close()

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
