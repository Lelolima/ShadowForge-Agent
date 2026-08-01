"""
Plugin Avançado de Exemplo para ShadowForge Agent
Demonstra recursos avançados como tratamento de eventos, dependências e configuração.
"""

from typing import Dict, Any, List
from core.plugins import ShadowForgePlugin
from core.event_bus import EventoShadowForge
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PluginAvancadoExemplo(ShadowForgePlugin):
    """Plugin avançado de exemplo demonstrando recursos completos do sistema de plugins."""

    @property
    def nome(self) -> str:
        """Nome único do plugin."""
        return "plugin_avancado_exemplo"

    @property
    def versao(self) -> str:
        """Versão do plugin seguindo semver (MAJOR.MINOR.PATCH)."""
        return "2.1.0"

    @property
    def dependencias(self) -> list[str]:
        """Lista de dependências de outros plugins.

        Este plugin depende do 'exemplo_plugin' para demonstrar
        como declarar e validar dependências.
        """
        return ["exemplo_plugin"]  # Dependência em outro plugin

    @property
    def ativo(self) -> bool:
        """Define se o plugin deve ser carregado automaticamente."""
        return True

    async def on_load(self, bus: EventoShadowForge, ctx: dict[str, Any]) -> None:
        """
        Chamado quando o plugin é carregado.

        Este método demonstra:
        - Registro de handlers de eventos específicos
        - Inicialização de estado interno
        - Publicação de eventos de inicialização
        - Verificação de dependências
        """
        logger.info(f"Plugin '{self.nome}' v{self.versao} carregado com sucesso!")

        # Armazenar referência ao barramento para uso posterior
        self._bus = bus
        self._context = ctx

        # Estado interno do plugin
        self._eventos_processados = 0
        self._ultimo_evento = None
        self._executando = False

        # Inscricao em eventos específicos do sistema
        await self._inscrever_em_eventos_sistema()

        # Inscricao em eventos de outros plugins (demonstra inter-plugin communication)
        await self._inscrever_em_eventos_plugins()

        # Publicar evento de inicialização
        await bus.publish(EventoShadowForge(
            tipo="plugin.avancado_exemplo.carregado",
            dados={
                "plugin": self.nome,
                "versao": self.versao,
                "dependencias": self.dependencias,
                "timestamp": datetime.now().isoformat()
            },
            origem=self.nome
        ))

        # Iniciar tarefa de background (exemplo)
        self._task_background = asyncio.create_task(self._loop_de_background())

        logger.info(f"Plugin '{self.nome}' inicializado completamente")

    async def on_unload(self, bus: EventoShadowForge) -> None:
        """
        Chamado quando o plugin é descarregado.

        Este método demonstra:
        - Cancelamento de inscrições
        - Limpeza de recursos
        - Parada segura de tarefas de background
        - Publicação de eventos de desligamento
        """
        logger.info(f"Plugin '{self.nome}' sendo descarregado...")

        # Parar tarefa de background
        self._executando = False
        if hasattr(self, '_task_background'):
            self._task_background.cancel()
            try:
                await self._task_background
            except asyncio.CancelledError:
                pass

        # Cancelar inscrições (se o seu event_bus suportar)
        # await self._desinscrever_de_eventos()

        # Publicar evento de desligamento
        await bus.publish(EventoShadowForge(
            tipo="plugin.avancado_exemplo.descarregado",
            dados={
                "plugin": self.nome,
                "eventos_processados": self._eventos_processados,
                "timestamp": datetime.now().isoformat()
            },
            origem=self.nome
        ))

        logger.info(f"Plugin '{self.nome}' descarregado com sucesso. "
                   f"Processou {self._eventos_processados} eventos.")

    async def on_event(self, evento: EventoShadowForge) -> None:
        """
        Hook genérico chamado para todos os eventos do sistema.

        Este método demonstra:
        - Filtragem eficiente de eventos
        - Processamento assíncrono de eventos
        - Atualização de estado interno
        - Tratamento de erros robusto
        """
        # Pular processamento se o plugin estiver sendo desligado
        if not self._executando:
            return

        try:
            # Atualizar estatísticas
            self._eventos_processados += 1
            self._ultimo_evento = evento

            # Filtrar eventos relevantes (melhor performance que processar todos)
            if not self._eh_evento_relevante(evento):
                return

            # Processar o evento baseado no tipo
            await self._processar_evento(evento)

        except Exception as e:
            logger.error(f"Erro ao processar evento {evento.tipo} no plugin {self.nome}: {e}",
                        exc_info=True)
            # Não propagar a exceção para não derrubar o sistema

    async def _inscrever_em_eventos_sistema(self) -> None:
        """Inscreve o plugin em eventos relevantes do sistema."""
        eventos_sistema = [
            "sistema.iniciado",
            "sistema.parando",
            "ooda.fase.iniciada",
            "ooda.fase.concluida",
            "acao.executada",
            "plugin.carregado"
        ]

        # Em uma implementação real, você faria:
        # for evento in eventos_sistema:
        #     await self._bus.subscribe(evento, self.on_event)

        logger.debug(f"Plugin {self.nome} inscrito em eventos do sistema")

    async def _inscrever_em_eventos_plugins(self) -> None:
        """Inscreve o plugin em eventos de outros plugins."""
        # Escutar eventos do plugin de exemplo (nossa dependência)
        await self._bus.subscribe(
            "exemplo_plugin.evento.processado",
            self._handle_evento_exemplo_plugin
        )

        logger.debug(f"Plugin {self.nome} inscrito em eventos de outros plugins")

    async def _handle_evento_exemplo_plugin(self, evento: EventoShadowForge) -> None:
        """Manipulador específico para eventos do exemplo_plugin."""
        logger.info(f"Plugin {self.nome} recebeu evento do exemplo_plugin: {evento.dados}")

        # Exemplo de re-processamento ou complemento de dados
        if evento.dados.get("status") == "sucesso":
            await self._bus.publish(EventoShadowForge(
                tipo="plugin.avancado_exemplo.resposta.exemplo_plugin",
                dados={
                    "resposta": "Processado com sucesso!",
                    "referencia": evento.dados,
                    "timestamp": datetime.now().isoformat()
                },
                origem=self.nome
            ))

    def _eh_evento_relevante(self, evento: EventoShadowForge) -> bool:
        """Determina se um evento deve ser processado por este plugin."""
        # Ignorar eventos próprios para evitar loops
        if evento.origem == self.nome:
            return False

        # Processar apenas ciertos tipos de evento
        tipos_relevantes = [
            "sistema.",
            "ooda.fase.",
            "acao.",
            "plugin.exemplo.",
            "plugin.avancado_exemplo."
        ]

        return any(evento.tipo.startswith(tipo) for tipo in tipos_relevantes)

    async def _processar_evento(self, evento: EventoShadowForge) -> None:
        """Processa eventos relevantes baseado no tipo."""
        if evento.tipo == "sistema.iniciado":
            await self._handle_sistema_iniciado(evento)
        elif evento.tipo == "ooda.fase.iniciada":
            await self._handle_ooda_fase_iniciada(evento)
        elif evento.tipo == "acao.executada":
            await self._handle_acao_executada(evento)
        # Adicione mais handlers conforme necessário

    async def _handle_sistema_iniciado(self, evento: EventoShadowForge) -> None:
        """Manipula o evento de inicialização do sistema."""
        logger.info("Sistema iniciado - Plugin avançado pronto para operação")

        # Você poderia inicializar recursos ou fazer verificações aqui
        await self._bus.publish(EventoShadowForge(
            tipo="plugin.avancado_exemplo.sistema.pronto",
            dados={
                "plugin": self.nome,
                "mensagem": "Pronto para processar eventos",
                "timestamp": datetime.now().isoformat()
            },
            origem=self.nome
        ))

    async def _handle_ooda_fase_iniciada(self, evento: EventoShadowForge) -> None:
        """Manipula o evento de início de fase OODA."""
        fase = evento.dados.get("fase", "desconhecida")
        logger.debug(f"Fase OODA iniciada: {fase}")

        # Exemplo de ação baseada na fase OODA
        if fase == "orientar":
            await self._realizar_analise_contextual()

    async def _handle_acao_executada(self, evento: EventoShadowForge) -> None:
        """Manipula o evento de execução de ação."""
        acao = evento.dados.get("acao", "desconhecida")
        resultado = evento.dados.get("resultado", "desconhecido")
        logger.debug(f"Ação executada: {acao} -> {resultado}")

        # Exemplo de aprendizado com ações executadas
        await self._registrar_metrica_acao(acao, resultado)

    async def _loop_de_background(self) -> None:
        """Loop de background para tarefas periódicas."""
        self._executando = True
        logger.info("Loop de background iniciado")

        while self._executando:
            try:
                # Executar tarefa periódica a cada 30 segundos
                await asyncio.sleep(30)

                if not self._executando:
                    break

                await self._executar_tarefa_periodica()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de background: {e}")
                # Continuar apesar do erro
                await asyncio.sleep(5)  # Evitar ciclo apertado em caso de erro persistente

        logger.info("Loop de background finalizado")

    async def _executar_tarefa_periodica(self) -> None:
        """Executa tarefas de manutenção periódica."""
        agora = datetime.now()
        logger.debug(f"Executando tarefa periodica às {agosto.isoformat()}")

        # Exemplo: limpar dados antigos
        if self._ultimo_evento:
            tempo_desde_ultimo_evento = agora - self._ultimo_evento.timestamp
            if tempo_desde_ultimo_evento > timedelta(hours=1):
                logger informando("Nenhum evento recebido na última hora")

        # Exemplo: reportar estatísticas
        await self._bus.publish(EventoShadowForge(
            tipo="plugin.avancado_exemplo.estatisticas",
            dados={
                "plugin": self.nome,
                "eventos_processados": self._eventos_processados,
                "taxa_por_hora": self._calcular_taxa_por_hora(),
                "timestamp": agora.isoformat()
            },
            origem=self.nome
        ))

    def _calcular_taxa_por_hora(self) -> float:
        """Calcula a taxa média de eventos processados por hora."""
        # Implementação simplificada - em produção seria mais sofisticada
        return float(self._eventos_processados)  # Placeholder

    async def _realizar_analise_contextual(self) -> None:
        """Realiza análise contextual quando a fase OODA 'orientar' inicia."""
        logger.debug("Realizando análise contextual...")

        # Aqui você poderia acessar o contexto compartilhado
        contexto_relevante = {
            k: v for k, v in self._context.items()
            if k.startswith("sensor_") or k.startswith("dados_")
        }

        if contexto_relevante:
            await self._bus.publish(EventoShadowForge(
                tipo="plugin.avancado_exemplo.analise.concluida",
                dados={
                    "conteudo": contexto_relevante,
                    "recomendacao": "Manter vigilância",
                    "confianca": 0.85
                },
                origem=self.nome
            ))

    async def _registrar_metrica_acao(self, acao: str, resultado: str) -> None:
        """Registra métricas sobre ações executadas."""
        # Em um sistema real, isso poderia atualizar métricas internas
        # ou enviar para um sistema de monitoramento
        pass

    # Métodos públicos para outros componentes utilizarem
    async def get_estatisticas(self) -> dict:
        """Retorna estatísticas atuais do plugin.

        Este método demonstra como plugins podem expor funcionalidades
        para outros componentes do sistema.
        """
        return {
            "plugin": self.nome,
            "versao": self.versao,
            "ativo": self._executando,
            "eventos_processados": self._eventos_processados,
            "ultimo_evento": self._ultimo_evento.tipo if self._ultimo_evento else None,
            "timestamp": datetime.now().isoformat()
        }

    async def processar_comando(self, comando: str, parametros: dict = None) -> dict:
        """
        Processa comandos administrativos enviados por outros componentes.

        Este método demonstra como plugins podem fornecer interfaces
        de controle e administração.
        """
        parametros = parametros or {}

        if comando == "reset_contador":
            self._eventos_processados = 0
            return {"status": "sucesso", "mensagem": "Contador zerado"}

        elif comando == "get_status":
            return await self.get_estatisticas()

        elif comando == "change_log_level":
            nivel = parametros.get("nivel", "INFO")
            numeric_level = getattr(logging, nivel.upper(), None)
            if isinstance(numeric_level, int):
                logger.setLevel(numeric_level)
                return {"status": "sucesso", "mensagem": f"Nível de log alterado para {nivel}"}
            else:
                return {"status": "erro", "mensagem": f"Nível de log inválido: {nivel}"}

        else:
            return {"status": "erro", "mensagem": f"Comando desconhecido: {comando}"}