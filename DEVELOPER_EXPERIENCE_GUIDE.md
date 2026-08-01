# Melhorias na Experiência do Desenvolvedor

Este documento descreve as ferramentas e práticas implementadas para melhorar a experiência de desenvolvimento no ShadowForge Agent.

## Ferramentas de Desenvolvimento

### 1. Gerador de Plugins (`scripts/generate_plugin.py`)

Esta ferramenta cria rapidamente a estrutura básica para novos plugins, incluindo:
- Diretório do plugin com nome apropriado
- Arquivo `__init__.py` com metadados básicos
- Arquivo `plugin.py` com implementação básica seguindo a interface `ShadowForgePlugin`

**Uso:**
```bash
python scripts/generate_plugin.py nome_do_plugin --author "Seu Nome" --description "Descrição do plugin" --version "1.0.0"
```

### 2. Hot-Reloader de Plugins (`scripts/plugin_hot_reloader.py`)

Esta ferramenta monitora alterações nos arquivos de plugin e recarrega automaticamente os plugins modificados, eliminando a necessidade de reiniciar toda a aplicação durante o desenvolvimento.

**Funcionalidades:**
- Monitoramento em tempo real de alterações em arquivos Python nos diretórios de plugins
- Recarregamento automático de plugins quando seus arquivos são modificados
- Logging detalhado para depuração
- Suporte a múltiplos diretórios de plugins
- Integração com o sistema existente de plugins do ShadowForge Agent

**Uso:**
```bash
# Monitora os diretórios padrão (plugins, shadowforge_plugins)
python scripts/plugin_hot_reloader.py

# Especifica intervalo de verificação personalizado
python scripts/plugin_hot_reloader.py --interval 0.5

# Monitora diretórios específicos
python scripts/plugin_hot_reloader.py --dirs meus_plugins plugins_externos

# Desativa output colorido (útil em alguns terminais)
python scripts/plugin_hot_reloader.py --no-rich
```

### 3. Scripts de Desenvolvimento (`scripts/dev.py`)

Script unificado para tarefas comuns de desenvolvimento:
- `lint`: Executa verificações de qualidade de código
- `test`: Roda a suíte de testes
- `format`: Formata o código usando black
- `typecheck`: Verifica tipos usando mypy
- `clean`: Remove arquivos temporários e caches
- `dev`: Inicia o servidor de desenvolvimento
- `all`: Executa todas as tarefas de verificação

**Exemplos:**
```bash
python scripts/dev.py lint
python scripts/dev.py test
python scripts/dev.py format
python scripts/dev.py dev
```

### 4. Configuração de TypeScript (`tsconfig.json`)

Configuração TypeScript para projetos que possam incluir componentes frontend ou scripts em TypeScript.

### 5. Requisitos de Desenvolvimento (`requirements-dev.txt`)

Lista de dependências necessárias para desenvolvimento, incluindo:
- Ferramentas de formatação (black)
- Linters (flake8)
- Verificação de tipos (mypy)
- Framework de testes (pytest)
- Ferramentas de documentação (mkdocs)
- Ferramentas de build e empacotamento

## Boas Práticas para Desenvolvimento de Plugins

### Estrutura Recomendada
```
meu_plugin/
├── __init__.py          # Metadados e exportação da classe
├── plugin.py            # Implementação principal
├── README.md            # Documentação do plugin
├── requirements.txt     # Dependências específicas (opcional)
└── resources/           # Recursos estáticos (opcional)
```

### Implementação da Interface
Todos os plugins devem herdar de `ShadowForgePlugin` e implementar:
- `nome`: Propriedade que retorna o nome único do plugin
- `versao`: Propriedade que retorna a versão seguindo semver
- `dependencias`: Lista opcional de plugins obrigatórios
- `ativo`: Propriedade booleana que determina se o carrega automaticamente
- `on_load`: Método assíncrito chamado quando o plugin é carregado
- `on_unload`: Método assíncrito chamado quando o plugin é descarregado
- `on_event`: Método assíncrito opcional para manipular eventos do sistema

### Exemplo Completo de Plugin
```python
"""Exemplo de plugin de coletor de threat intelligence."""

from typing import Dict, Any
from core.plugins import ShadowForgePlugin
from core.event_bus import EventBus, EventoShadowForge
import logging
import aiohttp

logger = logging.getLogger(__name__)

class ThreatIntelPlugin(ShadowForgePlugin):
    """Plugin para coletar indicadores de comprometimento de fontes abertas."""
    
    @property
    def nome(self) -> str:
        return "threat_intel"

    @property
    def versao(self) -> str:
        return "1.0.0"

    @property
    def dependencias(self) -> list[str]:
        return []  # Nenhuma dependência obrigatória

    @property
    def ativo(self) -> bool:
        return True

    async def on_load(self, bus: EventBus, ctx: dict[str, Any]) -> None:
        """Inicializa o plugin quando carregado."""
        logger.info(f"Plugin '{self.nome}' v{self.versao} carregado")
        
        # Inscrito para eventos de solicitação de TI
        await bus.subscribe("ti.solicitar", self.handle_ti_request)
        
        # Publica evento de inicialização
        await bus.publish(EventoShadowForge(
            tipo="plugin.inicializado",
            dados={"plugin": self.nome, "versao": self.versao},
            origem=self.nome
        ))

    async def on_unload(self, bus: EventBus) -> None:
        """Limpa recursos quando o plugin é descarregado."""
        logger.info(f"Plugin '{self.nome}' descarregado")
        await bus.unsubscribe("ti.solicitar", self.handle_ti_request)

    async def on_event(self, evento: EventoShadowForge) -> None:
        """Processa eventos do sistema."""
        if evento.tipo.startswith("sistema."):
            logger.debug(f"Plugin '{self.nome}' recebeu evento de sistema: {evento.tipo}")

    async def handle_ti_request(self, evento: EventoShadowForge) -> None:
        """Manipula solicitações de threat intelligence."""
        try:
            indicadores = await self.fetch_threat_intel()
            await bus.publish(EventoShadowForge(
                tipo="ti.resultado",
                dados={"indicadores": indicadores, "fonte": self.nome},
                origem=self.nome
            ))
        except Exception as e:
            logger.error(f"Erro ao buscar threat intelligence: {e}")
            await bus.publish(EventoShadowForge(
                tipo="ti.erro",
                dados={"erro": str(e), "fonte": self.nome},
                origem=self.nome
            ))

    async def fetch_threat_intel(self) -> list[dict]:
        """Busca threat intelligence de fontes externas."""
        # Implementação específica aqui
        return []
```

## Workflow Recomendado para Desenvolvimento

1. **Crie o plugin**: Use o gerador para criar a estrutura básica
2. **Implemente a funcionalidade**: Adicione sua lógica específica no arquivo plugin.py
3. **Teste isoladamente**: Teste os métodos do plugin antes de integrar
4. **Use o hot-reloader**: Execute o hot-reloader para ver mudanças em tempo real
5. **Execute os testes**: Garanta que seu plugin não quebre funcionalidades existentes
6. **Verifique a qualidade**: Use lint e type checking para manter padrões de código
7. **Documente**: Adicione README e comentários explicativos
8. **Empacote**: Prepare para distribuição se necessário

## Solução de Problemas Comuns

### Plugin não está sendo carregado
- Verifique se o nome do plugin está correto e não há conflitos
- Confirme que a classe herda de `ShadowForgePlugin`
- Verifique se o método `nome` retorna exatamente o mesmo nome do diretório
- Olhe nos logs por mensagens de erro de importação

### Alterações não estão sendo detectadas pelo hot-reloader
- Certifique-se de que está editando arquivos .py nos diretórios monitorados
- Verifique se o editor não está salvando em um local temporário ou diferente
- Tente aumentar o intervalo de verificação com `--interval`
- Consulte os logs de debug para ver se as mudanças estão sendo detectadas

### Erros de importação no plugin
- Certifique-se de que todas as dependências estão instaladas
- Verifique se os caminhos de importação estão corretos relacionados à raiz do projeto
- Confirme que não há erros de sintaxe no arquivo

## Próximos Passos Sugeridos

1. **Documentação Automatizada**: Integrar geraçãodocumentação automática de plugins usando docstrings
2. **Testes Automáticos de Plugins**: Criar framework de teste específico para plugins
3. **Marketplace de Plugins**: Sistema para descoberta e instalação de plugins comunitários
4. **Versionamento de Plugins**: Sistema mais robusto para gerenciar dependências entre plugins
5. **Ambiente de Sandbox**: Execução de plugins em ambiente restrito para maior segurança

Estas ferramentas estabelecem uma base sólida para desenvolvimento contínuo e colaborativo no ecossistema ShadowForge Agent.