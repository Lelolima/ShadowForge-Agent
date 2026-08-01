#!/usr/bin/env python3.11
"""
============================================================
NVIDIA ShadowForge - Plugin Generator
Arquivo: scripts/generate_plugin.py
============================================================
Script para gerar estrutura básica de plugins para ShadowForge Agent.
============================================================
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

def create_plugin_structure(plugin_name: str, author: str = "Seu Nome",
                          description: str = "Plugin para ShadowForge Agent",
                          version: str = "1.0.0"):
    """
    Cria a estrutura básica para um novo plugin.

    Args:
        plugin_name: Nome do plugin (snake_case)
        author: Nome do autor
        description: Descrição do plugin
        version: Versão inicial do plugin
    """
    # Converte para snake_case se necessário
    plugin_name = plugin_name.lower().replace("-", "_").replace(" ", "_")

    # Define caminhos
    plugin_dir = Path("plugins") / plugin_name
    init_file = plugin_dir / "__init__.py"
    plugin_file = plugin_dir / "plugin.py"

    # Cria diretório
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Cria __init__.py
    init_content = f'''"""
Pacote do plugin {plugin_name}.
"""

from .plugin import {plugin_name.title().replace("_", "")}

# Exportar a classe do plugin para fácil importação
__all__ = ["{plugin_name.title().replace("_", "")}"]

# Metadados do pacote (opcional)
__title__ = "{plugin_name}"
__description__ = "{description}"
__version__ = "{version}"
__author__ = "{author}"
'''

    # Cria plugin.py
    plugin_class_name = "".join(word.capitalize() for word in plugin_name.split("_"))
    plugin_content = f'''"""
{description}
Este plugin demonstra as funcionalidades básicas do sistema de plugins.
"""

from typing import Dict, Any
from core.plugins import ShadowForgePlugin
from core.event_bus import EventoShadowForge
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class {plugin_class_name}(ShadowForgePlugin):
    """{description}."""

    @property
    def nome(self) -> str:
        """Nome único do plugin."""
        return "{plugin_name}"

    @property
    def versao(self) -> str:
        """Versão do plugin seguindo semver (MAJOR.MINOR.PATCH)."""
        return "{version}"

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
        logger.info(f"Plugin '{{self.nome}}' v{{self.versao}} carregado com sucesso!")

        # Exemplo: inscrever-se para eventos específicos
        # await bus.subscribe("tipo_de_evento", self.handle_custom_event)

        # Exemplo: publicar um evento de inicialização
        await bus.publish(EventoShadowForge(
            tipo="plugin.carregado",
            dados={{"plugin": self.nome, "versao": self.versao}},
            origem=self.nome
        ))

    async def on_unload(self, bus: EventBus) -> None:
        """
        Chamado quando o plugin é descarregado.

        Args:
            bus: Barramento de eventos
        """
        logger.info(f"Plugin '{{self.nome}}' descarregado.")

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
            logger.debug(f"Plugin '{{self.nome}}' recebeu evento de sistema: {{evento.tipo}}")

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
        resultado = {{
            "processado_por": self.nome,
            "timestamp": str(datetime.now()),
            "dados_originais": dados,
            "status": "sucesso"
        }}
        return resultado
'''

    # Escreve os arquivos
    with open(init_file, "w", encoding="utf-8") as f:
        f.write(init_content)

    with open(plugin_file, "w", encoding="utf-8") as f:
        f.write(plugin_content)

    print(f"[+] Plugin '{plugin_name}' created successfully!")
    print(f"    Location: {plugin_dir.absolute()}")
    print(f"    Files created:")
    print(f"      - {init_file}")
    print(f"      - {plugin_file}")
    print()
    print("Next steps:")
    print(f"  1. Edit {plugin_file} to implement your plugin's functionality")
    print(f"  2. Update metadata in {init_file} if needed")
    print(f"  3. Add dependencies to plugin.py if you need other plugins")
    print(f"  4. Test the agent with: python main.py")

def main():
    parser = argparse.ArgumentParser(
        description="Gerador de plugins para ShadowForge Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python scripts/generate_plugin.py meu_novo_plugin
  python scripts/generate_plugin.py scanner_de_portas --author "João Silva" --version "0.1.0"
  python scripts/generate_plugin.py analisador_de_vulns -d "Plugin para análise de vulnerabilidades"
        """
    )

    parser.add_argument(
        "name",
        help="Nome do plugin (será convertido para snake_case)"
    )

    parser.add_argument(
        "--author",
        default="Seu Nome",
        help="Nome do autor do plugin (padrão: 'Seu Nome')"
    )

    parser.add_argument(
        "--description",
        default="Plugin para ShadowForge Agent",
        help="Descrição do plugin"
    )

    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Versão inicial do plugin (padrão: '1.0.0')"
    )

    args = parser.parse_args()

    try:
        create_plugin_structure(
            plugin_name=args.name,
            author=args.author,
            description=args.description,
            version=args.version
        )
    except Exception as e:
        print(f"[!] Erro ao criar plugin: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()