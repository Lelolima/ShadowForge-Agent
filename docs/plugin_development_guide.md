# Desenvolvimento de Plugins para ShadowForge Agent

Este documento fornece um guia completo para o desenvolvimento de plugins para o ShadowForge Agent, incluindo conceitos básicos, arquitetura, melhores práticas e exemplos práticos.

## Visão Geral do Sistema de Plugins

O sistema de plugins do ShadowForge Agent foi projetado para ser extensível, seguro e fácil de usar. Ele permite que desenvolvedores estendam as funcionalidades do agente sem modificar o código base.

### Principais Características

- **Carregamento Dinâmico**: Plugins são carregados automaticamente do diretório `plugins/` na inicialização
- **Interface Padronizada**: Todos os plugins herdam da classe base `ShadowForgePlugin`
- **Hooks de Eventos**: Plugins podem se inscrever para eventos específicos do sistema
- **Gerenciamento de Dependências**: Suporte para declaração e validação de dependências entre plugins
- **Hot Reload**: Suporte para recarregamento de plugins durante a execução (em desenvolvimento)
- **Sandboxing Básico**: Isolamento de importações para evitar conflitos
- **Validação de Segurança**: Opcional verificação de hash para plugins confiáveis

## Arquitetura do Sistema de Plugins

![Arquitetura do Sistema de Plugins](.github/assets/plugin-architecture.svg)

### Componentes Principais

1. **Plugin Manager** (`core.plugins.PluginManager`)
   - Responsável por descobrir, carregar e gerenciar o ciclo de vida dos plugins
   - Valida dependências e resolve conflitos
   - Fornece interface para carregar/descarregar plugins em tempo de execução

2. **ShadowForgePlugin Base Class** (`core.plugins.ShadowForgePlugin`)
   - Classe abstrata que define a interface que todos os plugins devem implementar
   - Fornece métodos de ciclo de vida (`on_load`, `on_unload`, `on_event`)

3. **Event Bus** (`core.event_bus.EventBus`)
   - Sistema de publicação/assinatura para comunicação entre componentes
   - Plugins podem se inscrever para eventos específicos ou receber todos os eventos

4. **Plugin Registry**
   - Registro interno de todos os plugins carregados
   - Mantém estado e metadados de cada plugin

## Estrutura de Diretórios para Plugins

Plugins devem ser colocados no diretório:
```
shadowforge-agent/
├── plugins/
│   ├── meu_plugin/
│   │   ├── __init__.py
│   │   └── plugin.py
│   └── outro_plugin.py
└── shadowforge_plugins/  # Diretório alternativo
    └── exemplo_plugin.py
```

## Criando Seu Primeiro Plugin

### Passo 1: Estrutura Básica

Crie um novo diretório para seu plugin dentro de `plugins/` ou `shadowforge_plugins/`:

```bash
mkdir -p plugins/meu_primeiro_plugin
touch plugins/meu_primeiro_plugin/__init__.py
touch plugins/meu_primeiro_plugin/plugin.py
```

### Passo 2: Implementando a Classe do Plugin

Edite `plugins/meu_primeiro_plugin/plugin.py`:

```python
"""
Exemplo de Plugin para ShadowForge Agent
Este plugin demonstra as funcionalidades básicas do sistema de plugins.
"""

from typing import Dict, Any
from core.plugins import ShadowForgePlugin
from core.event_bus import EventoShadowForge
import logging

logger = logging.getLogger(__name__)


class MeuPrimeiroPlugin(ShadowForgePlugin):
    """Primeiro plugin de exemplo para ShadowForge Agent."""
    
    @property
    def nome(self) -> str:
        """Nome único do plugin."""
        return "meu_primeiro_plugin"
    
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
            "status": "sucesso"
        }
        return resultado
```

### Passo 3: __init__.py do Pacote

Edite `plugins/meu_primeiro_plugin/__init__.py`:

```python
"""
Pacote do plugin meu_primeiro_plugin.
"""

from .plugin import MeuPrimeiroPlugin

# Exportar a classe do plugin para fácil importação
__all__ = ["MeuPrimeiroPlugin"]

# Metadados do pacote (opcional)
__title__ = "meu_primeiro_plugin"
__description__ = "Primeiro plugin de exemplo para ShadowForge Agent"
__version__ = "1.0.0"
__author__ = "Seu Nome"
```

### Passo 4: Teste e Validação

Para testar seu plugin, simplesmente inicie o ShadowForge Agent:

```bash
python main.py
```

O plugin será carregado automaticamente e você verá as mensagens de log indicando seu carregamento.

## Hooks Disponibilidade de Hooks e Eventos

### Hooks do Ciclo de Vida

1. **`on_load(bus, ctx)`**
   - Chamado quando o plugin é carregado
   - Ideal para inicialização de recursos, inscrição em eventos
   - Recebe o barramento de eventos e contexto compartilhado

2. **`on_unload(bus)`**
   - Chamado quando o plugin é descarregado
   - Ideal para limpeza de recursos, cancelamento de inscrições
   - Recebe o barramento de eventos

3. **`on_event(evento)`**
   - Chamado para CADA evento do sistema (use com cuidado)
   - Alternativa mais específica: inscreva-se para tipos específicos de eventos usando `bus.subscribe()`

### Eventos Comuns do Sistema

O sistema publica diversos eventos que seus plugins podem escutar:

- `sistema.iniciado` - Quando o sistema inicia
- `sistema.parando` - Quando o sistema está se preparando para parar
- `sistema.parado` - Quando o sistema para completamente
- `ooda.fase.iniciada` - Quando uma fase do ciclo OODA começa
- `ooda.fase.concluida` - Quando uma fase do ciclo OODA termina
- `acao.executada` - Quando uma ação é executada
- `plugin.carregado` - Quando um plugin é carregado
- `plugin.descarregado` - Quando um plugin é descarregado

### Publicando Eventos

Seu plugin pode publicar eventos para comunicar com outros componentes:

```python
from core.event_bus import EventoShadowForge

# Dentro de qualquer método do seu plugin
await bus.publish(EventoShadowForge(
    tipo="meu_plugin.evento.personalizado",
    dados={
        "chave": "valor",
        "resultado": "sucesso"
    },
    origem=self.nome
))
```

## Melhores Práticas

### 1. Segurança

- **Valide todas as entradas**: Nunca confie em dados externos sem validação
- **Use o princípio do menor privilégio**: Solicite apenas as permissões necessárias
- **Trate exceções adequadamente**: Evite que exceções não tratadas derrubem o sistema
- **Considere o sandboxing**: Se seu plugin executar código externo, isole-o adequadamente

### 2. Performance

- **Operações assíncronas**: Use `async/await` para operações de I/O
- **Cache quando apropriado**: Evite reprocessamento desnecessário
- **Limite escuta de eventos**: Se usar `on_event()`, filtre cuidadosamente para evitar sobrecarga
- **Libere recursos**: Sempre limpe recursos em `on_unload()`

### 3. Manutenibilidade

- **Documente seu código**: Use docstrings e comentários claros
- **Follow PEP 8**: Mantenha consistência com o estilo de código do projeto
- **Versionamento semântico**: Use MAJOR.MINOR.PATCH para versionamento
- **Teste unitário**: Crie testes para a lógica do seu plugin
- **Logs significativos**: Use níveis de log apropriados (DEBUG, INFO, WARNING, ERROR)

### 4. Compatibilidade

- **Declare dependências claramente**: Liste todas as dependências de outros plugins
- **Mantenha compatibilidade retroativa**: Evite quebrar mudanças em versões menores
- **Teste com diferentes versões**: Certifique-se de que seu plugin funciona com as versões suportadas do agente

## Estrutura Avançada de Plugins

Para plugins mais complexos, considere esta estrutura:

```
meu_plugin_avancado/
├── __init__.py
├── plugin.py              # Classe principal do plugin
├── config.py              # Configurações do plugin
├── handlers/              # Manipuladores de eventos específicos
│   ├── __init__.py
│   └── evento_handler.py
├── services/              # Serviços de negócio
│   ├── __init__.py
│   └── processador.py
├── utils/                 # Funções utilitárias
│   ├── __init__.py
│   └── helpers.py
└── resources/             # Recursos estáticos (se necessário)
    ├── templates/
    └── static/
```

## Exemplo de Plugin Completo com Dependências

Vamos criar um exemplo mais avançado que demonstra dependências e comunicação entre plugins:

```python
"""
Plugin de Exemplo Avançado com Dependências
"""

from typing import Dict, Any, List
from core.plugins import ShadowForgePlugin
from core.event_bus import EventoShadowForge
import logging
import aiohttp

logger = logging.getLogger(__name__)


class PluginAvancadoExemplo(ShadowForgePlugin):
    """Plugin avançado que demonstra dependências e integração externa."""
    
    @property
    def nome(self) -> str:
        return "plugin_avancado_exemplo"
    
    @property
    def versao(self) -> str:
        return "1.0.0"
    
    @property
    def dependencias(self) -> list[str]:
        # Este plugin depende do plugin de logger personalizado (hipotético)
        return ["logger_personalizado"]
    
    @property
    def ativo(self) -> bool:
        return True
    
    def __init__(self):
        super().__init__()
        self.http_session: aiohttp.ClientSession | None = None
        self.logger_plugin = None  # Será preenchido se o plugin de logger estiver disponível
    
    async def on_load(self, bus: EventBus, ctx: dict[str, Any]) -> None:
        """Inicialização assíncrona do plugin."""
        logger.info(f"Carregando {self.nome} v{self.versao}")
        
        # Criar sessão HTTP reutilizável
        self.http_session = aiohttp.ClientSession()
        
        # Verificar se dependências estão disponíveis no contexto
        if "logger_personalizado" in ctx:
            self.logger_plugin = ctx["logger_personalizado"]
            logger.info("Plugin de logger personalizado encontrado e vinculado")
        else:
            logger.warning("Plugin de logger personalizado não encontrado - continuando sem ele")
        
        # Inscrever-se para eventos específicos
        await bus.subscribe("dados.recebidos", self.processar_dados_recebidos)
        await bus.subscribe("sistema.shutdown", self.limpar_recursos)
        
        # Publicar evento de inicialização
        await bus.publish(EventoShadowForge(
            tipo="plugin.avancado.carregado",
            dados={
                "plugin": self.nome,
                "versao": self.versao,
                "recursos": ["http_session", "logger_integracao"] if self.logger_plugin else ["http_session"]
            },
            origem=self.nome
        ))
    
    async def on_unload(self, bus: EventBus) -> None:
        """Limpeza cuidadosa de recursos."""
        logger.info(f"Descarregando {self.nome}")
        
        # Cancelar inscrições
        await bus.unsubscribe("dados.recebidos", self.processar_dados_recebidos)
        await bus.unsubscribe("sistema.shutdown", self.limpar_recursos)
        
        # Fechar sessão HTTP
        if self.http_session:
            await self.http_session.close()
        
        # Publicar evento de descarregamento
        await bus.publish(EventoShadowForge(
            tipo="plugin.avancado.descarregado",
            dados={"plugin": self.nome},
            origem=self.nome
        ))
    
    async def on_event(self, evento: EventoShadowForge) -> None:
        """Processamento seletivo de eventos."""
        # Filtrar apenas eventos que nos interessam
        if evento.tipo in ["dados.recebidos", "sistema.shutdown"]:
            await self.on_event(evento)
    
    async def processar_dados_recebidos(self, evento: EventoShadowForge) -> None:
        """
        Processa dados recebidos de outros componentes.
        
        Args:
            evento: Contendo os dados a serem processados
        """
        try:
            dados = evento.dados.get("payload", {})
            logger.info(f"Processando dados recebidos: {dados}")
            
            # Exemplo de processamento: enriquecer dados com timestamp
            dados_enriquecidos = await self._enriquecer_dados(dados)
            
            # Publicar resultado para outros plugins consumirem
            await bus.publish(EventoShadowForge(
                tipo="dados.processados",
                dados={
                    "original": dados,
                    "processado": dados_enriquecidos,
                    "processado_por": self.nome
                },
                origem=self.nome
            ))
            
        except Exception as e:
            logger.error(f"Erro ao processar dados: {e}")
            # Notificar sobre o erro
            await bus.publish(EventoShadowForge(
                tipo="erro.processamento",
                dados={
                    "plugin": self.nome,
                    "erro": str(e),
                    "dados_originais": evento.dados
                },
                origem=self.nome
            ))
    
    async def _enriquecer_dados(self, dados: dict) -> dict:
        """
        Enriquece dados usando recursos externos (exemplo: API externa).
        
        Args:
            dados: Dados originais
            
        Returns:
            Dados enriquecidos
        """
        # Simular chamada a API externa
        if self.http_session:
            try:
                # Exemplo: chamar serviço de geolocalização baseado em IP
                ip = dados.get("endereco_ip")
                if ip:
                    # async with self.http_session.get(f"https://ipapi.co/{ip}/json/") as resp:
                    #     geo_data = await resp.json()
                    #     dados["geolocalizacao"] = geo_data
                    pass  # Implementação real ia aqui
            except Exception as e:
                logger.warning(f"Falha ao enriquecer dados com API externa: {e}")
        
        # Adicionar metadata de processamento
        dados["processado_em"] = str(datetime.now())
        dados["processado_por_plugin"] = self.nome
        
        return dados
    
    async def limpar_recursos(self, evento: EventoShadowForge) -> None:
        """
        Manipulador específico para evento de shutdown.
        
        Args:
            evento: Evento de shutdown do sistema
        """
        logger.info("Recebido sinal de shutdown, limpando recursos...")
        # A limpeza real acontece em on_unload, mas podemos fazer preparação aqui
```

## Publicando e Compartilhando Plugins

Se você deseja compartilhar seu plugin com outros usuários do ShadowForge Agent:

1. **Documente completamente seu plugin (README, exemplos de uso)
2. **Inclua um arquivo `plugin.yml` ou `plugin.json` com metadados**
3. **Forneça exemplos de uso e casos de teste**
4. **Considere criar uma versão empacotada para distribuição**

### Arquivo de Metadados do Plugin (Opcional)

Crie `plugin.yaml` no diretório do seu plugin:

```yaml
name: meu_primeiro_plugin
version: 1.0.0
description: Primeiro plugin de exemplo para ShadowForge Agent
author: Seu Nome
email: seu.email@exemplo.com
homepage: https://github.com/seusuario/meu_primeiro_plugin
dependencies: []  # Lista de dependências de outros plugins
tags:
  - exemplo
  - tutorial
  - demostração
maintainers:
  - name: Seu Nome
    email: seu.email@exemplo.com
licenses:
  - MIT
```

## Desenvolvimento e Testes

### Ambiente de Desenvolvimento

1. **Clone o repositório**: `git clone https://github.com/Lelolima/ShadowForge-Agent.git`
2. **Instale dependências**: `pip install -r requirements.txt`
3. **Instale dependências de desenvolvimento**: `pip install -r requirements-dev.txt`
4. **Execute os testes**: `pytest tests/`

### Testando Seu Plugin

Crie testes unitários para seu plugin:

```python
# tests/plugins/test_meu_primeiro_plugin.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from plugins.meu_primeiro_plugin.plugin import MeuPrimeiroPlugin
from core.event_bus import EventoShadowForge

@pytest.fixture
def plugin():
    return MeuPrimeiroPlugin()

@pytest.fixture
def mock_bus():
    bus = MagicMock()
    bus.publish = AsyncMock()
    bus.subscribe = AsyncMock()
    return bus

@pytest.fixture
def mock_context():
    return {}

@pytest.mark.asyncio
async def test_plugin_load(plugin, mock_bus, mock_context):
    """Testa o carregamento do plugin."""
    await plugin.on_load(mock_bus, mock_context)
    assert plugin.nome == "meu_primeiro_plugin"
    assert plugin.versao == "1.0.0"
    mock_bus.publish.assert_called()

@pytest.mark.asyncio
async def test_plugin_event_handling(plugin, mock_bus):
    """Testa o manipulação de eventos pelo plugin."""
    evento = EventoShadowForge(
        tipo="teste.evento",
        dados={"chave": "valor"},
        origem="teste"
    )
    
    # Não deve lançar exceção
    await plugin.on_event(evento)
    
    # Se o plugin tiver lógica específica, asserte aqui
```

### Desenvolvimento Iterativo

Durante o desenvolvimento, você pode recarregar plugins sem reiniciar todo o sistema:

```python
# No console Python ou em um script de desenvolvimento
from core.plugins import PluginManager

manager = PluginManager()
# Recarregar um plugin específico
await manager.reload_plugin("meu_primeiro_plugin")
# Ou recarregar todos os plugins
await manager.reload_all_plugins()
```

## Solução de Problemas Comuns

### Plugin não está sendo carregado

1. **Verifique o diretório**: Certifique-se de que o plugin está em `plugins/` ou `shadowforge_plugins/`
2. **Verifique o __init__.py**: Cada pacote de plugin precisa de um `__init__.py`
3. **Verifique a classe**: Sua classe deve herdar de `ShadowForgePlugin`
4. **Verifique os métodos abstratos**: Você deve implementar `nome` e `versao`
5. **Check logs**: Procure por mensagens de erro no log durante a inicialização

### Erros de importação

1. **Dependências faltantes**: Verifique se todas as dependências de Python estão instaladas
2. **Caminhos de importação incorretos**: Use importações relativas dentro do pacote do plugin
3. **Conflitos de namespace**: Evite nomes que conflitam com módulos padrão do Python

### Problemas de performance

1. **Operações síncronas em métodos assíncronos**: Converta I/O para assíncrono
2. **Escuta excessiva de eventos**: Use filtros específicos em vez de `on_event()` genérico
3. **Vazamentos de memória**: Sempre limpe conexões, sessões e recursos em `on_unload()`

### Conflitos com outros plugins

1. **Dependências conflitantes**: Verifique se as versões de dependências são compatíveis
2. **Nomes de eventos conflitantes**: Use namespacing em seus tipos de evento (ex: `meu_plugin.tipo`)
3. **Recursos compartilhados**: Coordine o acesso a recursos externos com outros plugins

## Recursos Adicionais

### APIs Disponíveis

Seu plugin tem acesso a diversos componentes do sistema através do contexto e do barramento de eventos:

- **`event_bus`**: Para publicar e inscrever-se em eventos
- **`context`**: Dicionário compartilhado para troca de dados entre plugins
- **`logging`**: Sistema de logger configurado para o seu plugin
- **`config`**: Acesso à configuração do sistema (se exposta pelo PluginManager)

### Extendendo o Sistema

Se você precisar estender o próprio sistema de plugins:

1. **Subclasse PluginManager**: Para personalizar lógica de carregamento
2. **Adicione novos tipos de hooks**: Estendendo a interface de plugin
3. **Implemente novos mecanismos de descoberta**: Para diferentes fontes de plugins
4. **Adicione recursos de segurança avançados**: Como assinatura de código ou sandboxing aprimorado

## Conclusão

O sistema de plugins do ShadowForge Agent oferece uma plataforma poderosa e flexível para extensão de funcionalidades. Seguindo as diretrizes deste tutorial, você pode criar plugins robustos, seguros e maintaináveis que se integrem perfeitamente ao ecossistema do agente.

Lembre-se de:
- Começar simples e adicionar complexidade gradualmente
- Testar rigorosamente em diferentes cenários
- Documentar seu plugin para que outros usuários possam entendê-lo e usá-lo
- Seguire as melhores práticas de segurança e performance

Boa codificação! 🚀

---

*Última atualização: August 2026*
*Versão do documento: 1.0.0*
*Compatível com ShadowForge Agent v2.0.0+*