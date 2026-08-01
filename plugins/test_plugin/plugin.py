"""
Plugin de teste para validar o hot-reloader
Este plugin demonstra as funcionalidades básicas do sistema de plugins.
"""

from typing import Dict, Any
from core.plugins import ShadowForgePlugin
from core.event_bus import EventBus, EventoShadowForge
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TestPlugin(ShadowForgePlugin):
    """Plugin de teste para validar o hot-reloader."""

    @property
    def nome(self) -> str:
        """Nome único do plugin."""
        return "test_plugin"

    @property
    def versao(self) -> str:
        """Versão do plugin seguindo semver (MAJOR.MINOR.PATCH)."""
        return "0.1.0"

    @property
    def dependencias(self) -> list[str]:
        """Lista de dependências de outros plugins."""
        return []  # Nenhuma dependência neste exemplo

    @property
    def ativo(self) -> bool:
        """Define se o plugin deve ser carregado automaticamente."""
        return True

    async def on_load(self, bus: EventBus, ctx: dict[str, Any]) -> None:
        """
        Chamado quando o plugin é carregado.

        Args:
            bus: Barramento de eventos para publicar/inscrever-se
            ctx: Contexto compartilhado entre plugins
        """
        logger.info(f"Plugin '{self.nome}' v{self.versao} carregado com sucesso!")

        # Exemplo: inscrever-se para eventos específicos
        # await bus.subscribe("tipo_de_evento", self.handle_custom_event)

        # Exemplo: publicar um evento de inicialização
        await bus.publish(EventoShadowForge(
            tipo="plugin.carregado",
            dados={"plugin": self.nome, "versao": self.versao},
            origem=self.nome
        ))

    async def on_unload(self, bus: EventBus) -> None:
        """
        Chamado quando o plugin é descarregado.

        Args:
            bus: Barramento de eventos
        """
        logger.info(f"Plugin '{self.nome}' descarregado.")

        # Exemplo: limpar recursos ou cancelar inscrições
        # await bus.unsubscribe("tipo_de_evento", self.handle_custom_event)

    async def on_event(self, evento: EventoShadowForge) -> None:
        """
        Hook genérico chamado para todos os eventos do sistema.

        Args:
            evento: O evento que ocorreu
        """
        # Filtrar eventos específicos se necessário
        if evento.tipo.startswith("sistema."):
            logger.debug(f"Plugin '{self.nome}' recebeu evento de sistema: {evento.tipo}")

        # Processar o evento conforme necessário
        # if evento.tipo == "evento.especifico":
        #     await self.processar_evento_especifico(evento)

    # Métodos auxiliares específicos do seu plugin
    async def processar_dados(self, dados: dict) -> dict:
        """
        Exemplo de método de processamento específico do plugin.

        Args:
            dados: Dados de entrada para processamento

        Returns:
            Dados processados
        """
        # Implementar lógica de processamento aqui
        resultado = {
            "processado_por": self.nome,
            "timestamp": str(datetime.now()),
            "dados_originais": dados,
            "status": "sucesso",
            "hot_reload_test": "MANUAL TRIGGER - HOT RELOAD DETECTION TEST - " + str(datetime.now()),
            "contador": getattr(self, '_contador', 0) + 1,
            "teste_marcador": "MANUAL_TEST_ACTIVE"
        }
        self._contador = resultado.get('contador', 0)
        return resultado
