# Tutorial de Desenvolvimento de Plugins para ShadowForge Agent

Este tutorial irá guiá-lo através do processo de criação, teste e deploy de plugins para o ShadowForge Agent.

## Pré-requisitos

- Python 3.11+
- ShadowForge Agent clonado e configurado
- Conhecimento básico de Python e programação assíncrona

## Estrutura de um Plugin

Um plugin no ShadowForge Agent consiste em:

1. **Diretório do plugin** (em `plugins/`plugins/ - arquivo de inicialização)`
- (implementação principal do plugin)

## Passo 1: Gerando um Plugin Básico

O ShadowForge Agent inclui um gerador de plugins que cria a estrutura básica:

```bash
python scripts/generate_plugin.py meu_plugin --author "Seu Nome" --description "Descrição do meu plugin" --version "1.0.0"
```

Isso criará:
```
plugins/
└── meu_plugin/
    ├── __init__.py
    └── plugin.py
```

## Passo 2: Entendendo a Estrutura Gerada

### `__init__.py`
```python
"""
Pacote do plugin meu_plugin.
"""

from .plugin import MeuPlugin

# Exportar a classe do plugin para fácil importação
__all__ = ["MeuPlugin"]

# Metadados do pacote (opcional)
__title__ = "meu_plugin"
__description__ = "Descrição do meu plugin"
__version__ = "1.0.0"
__author__ = "Seu Nome"
```

### `plugin.py`
```python
"""
Descrição
Este plugin demonstra as funcionalidades básicas do sistema de plugins.
"""

from typing import Dict, Any
from core.plugins import ShadowForgePlugin
from core.event_bus import EventBus, EventoShadowForge
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MeuPlugin(ShadowForgePlugin):
    """Descrição."""

    @property
    def nome(self) -> str:
        """Nome único do plugin."""
        return "meu_plugin"

    @property
    def versao(self) -> str:
        """Versão do plugin seguindo semver (MAJOR.MINOR.PATCH)."""
        return "1.0.0"

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
            "status": "sucesso"
        }
        return resultado
```

## Passo 3: Implementando Funcionalidade

Vamos modificar o método `processar_dados` para adicionar alguma funcionalidade real:

```python
async def processar_dados(self, dados: dict) -> dict:
    """
    Processa dados de entrada e retorna resultado enriquecido.

    Args:
        dados: Dados de entrada para processamento

    Returns:
        Dados processados com informações adicionais
    """
    # Simular algum processamento
    processado = {
        "processado_por": self.nome,
        "timestamp": str(datetime.now()),
        "dados_originais": dados,
        "status": "sucesso",
        "resultado": {
            "total_itens": len(dados) if isinstance(dados, (list, dict)) else 1,
            "tipo_dados": type(dados).__name__,
            "processado_em": datetime.now().isoformat()
        }
    }
    
    logger.info(f"Plugin {self.nome} processou {len(dados) if isinstance(dados, (list, dict)) else 1} itens")
    return processado
```

## Passo 4: Adicionando Dependências

Se seu plugin depender de outros plugins, você pode especificar isso na propriedade `dependencias`:

```python
@property
def dependencias(self) -> list[str]:
    """Lista de dependências de outros plugins."""
    return ["outro_plugin"]  # Este plugin depende de outro_plugin
```

O sistema carregará automaticamente as dependências antes de carregar seu plugin.

## Passo 5: Testando seu Plugin

### Teste Manual

1. Inicie o ShadowForge Agent normalmente:
```bash
python main.py
```

2. Verifique os logs para ver se seu plugin foi carregado:
```
[INFO] Plugin ativado: meu_plugin
[INFO] Plugin 'meu_plugin' v1.0.0 carregado com sucesso!
```

### Teste com Hot-Reloader (Desenvolvimento)

Durante o desenvolvimento, use o hot-reloader para recarregar automaticamente seu plugin quando você fizer alterações:

```bash
python scripts/plugin_hot_reloader.py --interval 1
```

O hot-reloader monitorará os diretórios `plugins/` e `shadowforge_plugins/` e recarregará automaticamente qualquer plugin cujo arquivo tenha sido modificado.

## Passo 6: Publicando Eventos

Seu plugin pode publicar eventos para que outros plugins ou o núcleo do agent possam reagir:

```python
# Publicar um evento personalizado
await bus.publish(EventoShadowForge(
    tipo="meu_plugin.dados_processados",
    dados={
        "plugin": self.nome,
        "quantidade": len(dados_processados),
        "timestamp": datetime.now().isoformat()
    },
    origem=self.nome
))
```

## Passo 7: Inscrivendo-se em Eventos

Seu plugin pode se inscrever para receber eventos de outros componentes:

```python
async def on_load(self, bus: EventBus, ctx: dict[str, Any]) -> None:
    # ... código existente ...
    
    # Inscrever-se para eventos específicos
    await bus.subscribe("dados.recebidos", self.handle_dados_recebidos)
    await bus.subscribe("sistema.shutdown", self.handle_shutdown)

async def handle_dados_recebidos(self, evento: EventoShadowForge) -> None:
    """Processa dados recebidos de outros plugins."""
    logger.info(f"Recebidos dados: {evento.dados}")
    # Processar os dados...
    
async def handle_shutdown(self, evento: EventoShadowForge) -> None:
    """Limpa recursos antes do shutdown."""
    logger.info("Recebido sinal de shutdown, limpando recursos...")
    # Limpar conexões, fechar arquivos, etc.
```

## Boas Práticas

1. **Mantenha os plugins focados**: Cada plugin deve ter uma responsabilidade bem definida.
2. **Trate erros adequadamente**: Use try/except para evitar que erros no plugin crashing o agent inteiro.
3. **Logge apropriadamente**: Use o logger do plugin para mensagens informativas e de depuração.
4. **Evite operações bloqueantes**: Como o agent é assíncrono, evite operações I/O bloqueantes ou use `asyncio.to_thread()` para elas.
5. **Limite o uso de memória**: Se seu plugin armazenar estado, implemente limites ou limpeza periódica.
6. **Versionamento semântico**: Siga o padrão MAJOR.MINOR.PATCH para versões.

## Solução de Problemas

### Plugin não carrega
- Verifique se o nome da classe no `plugin.py` corresponde ao nome no `__init__.py`
- Certifique-se de que não há erros de sintaxe no código
- Verifique os logs para mensagens de erro

### Alterações não são reconhecidas pelo hot-reloader
- Certifique-se de que está editando arquivos `.py` dentro de diretórios de plugin
- O hot-reloader ignora arquivos que começam com `_` (como `__pycache__`)
- Verifique se o hot-reloader está monitorando o diretório correto

### Dependências não resolvidas
- Verifique se os plugins dependentes realmente existem
- Certifique-se de que não há dependências circulares
- Plugins com dependências não satisfeitas não serão carregados

## Próximos Passos

Depois de dominar o desenvolvimento básico de plugins, você pode:

1. Explorar plugins avançados que utilizam recursos como:
   - Agendamento de tarefas periódicas
   - Integração com APIs externas
   - Processamento de fluxos de dados em tempo real
   - Machine Learning e inferência com modelos NIM

2. Contribuir com plugins para a comunidade oficial do ShadowForge Agent

3. Criar plugins especializados para casos de uso específicos como:
   - Análise de segurança e pentesting
   - Coleta e processamento de logs
   - Integração com ferramentas de CI/CD
   - Dashboards e visualizações personalizadas

---

*Este tutorial faz parte da melhoria contínua da experiência de desenvolvedor do ShadowForge Agent. Para mais informações, consulte a documentação completa em `docs/` ou examine os plugins de exemplo em `plugins/exemplo_plugin/` e `plugins/plugin_avancado_exemplo/`.*