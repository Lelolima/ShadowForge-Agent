# Contribuindo para o ShadowForge

Primeiramente, obrigado por considerar contribuir para o ShadowForge! É por causa de pessoas como você que esta ferramenta fica melhor para toda a comunidade de segurança.

## Código de Conduta

Este projeto e todas as pessoas que participam dele são regidos pelo nosso
[Código de Conduta](CODE_OF_CONDUCT.md). Ao participar, você é esperado para
cumprir este código. Por favor, relate comportamentos inaceitáveis para security@shadowforge.dev.

## Requisitos Legais e Éticos

**Este projeto é para testes de segurança autorizados APENAS.** Antes de contribuir:

- Nunca contribua com código que facilite acesso não autorizado a sistemas
- Nunca inclua chaves de API reais, senhas ou credenciais nas contribuições
- Certifique-se de que suas contribuições respeitem as leis de privacidade e proteção de dados (LGPD, GDPR)
- Todas as capacidades ofensivas devem incluir salvaguardas éticas adequadas
- Contribuições que removam ou enfraqueçam as salvaguardas éticas serão rejeitadas
- Você deve ter o direito legal de enviar o código (sem vazamentos de código proprietário)

## Como Posso Contribuir?

### Relatando Bugs

1. Verifique se o bug já foi relatado em [Issues](../../issues)
2. Se não, crie uma nova issue usando o [modelo de relatório de bug](.github/ISSUE_TEMPLATE/bug_report.md)
3. Inclua:
   - Título e descrição claros
   - Passos para reproduzir
   - Comportamento esperado vs atual
   - Seu ambiente (SO, versão do Python, GPU)
   - Logs relevantes (redija quaisquer chaves de API ou dados sensíveis)

### Sugerindo Melhorias

1. Abra uma issue usando o [modelo de solicitação de recurso](.github/ISSUE_TEMPLATE/feature_request.md)
2. Descreva o recurso, seu caso de uso e por que beneficiaria a maioria dos usuários
3. Inclua quaisquer considerações de segurança (ele adiciona superfície de ataque? são necessárias novas salvaguardas?)

### Pull Requests

1. Faça um fork do repositório
2. Crie uma branch de recurso (`git checkout -b feature/recurso-incrivel`)
3. Faça suas alterações com commits claros e atômicos
4. Adicione testes que cubram a nova funcionalidade
5. Certifique-se de que todos os testes passem (`python -m pytest tests/ -v`)
6. Execute a verificação de linting (`ruff check . && ruff format .`)
7. Execute a verificação de tipos (`mypy core/ models/ planning/`)
8. Execute o scan de segurança (`bandit -r core/ models/ planning/ -ll --skip B101,B311`)
9. Envie para seu fork e abra um Pull Request

#### Modelo de Descrição do PR

```markdown
## Descrição
Breve descrição das alterações

## Tipo de Alteração
- [ ] Correção de bug (alteração não disruptiva que corrige um problema)
- [ ] Novo recurso (alteração não disruptiva que adiciona funcionalidade)
- [ ] Alteração disruptiva (correção ou recurso que causaria mudança na funcionalidade existente)
- [ ] Melhoria de segurança

## Considerações Éticas
- [ ] Esta alteração NÃO enfraquece as salvaguardas éticas
- [ ] Esta alteração NÃO habilita acesso não autorizado
- [ ] Novas capacidades de ataque incluem salvaguardas apropriadas

## Testes
- [ ] Testes adicionados/atualizados
- [ ] Todos os testes existentes passam
- [ ] Testado em modo de simulação

## Checklist
- [ ] O código segue as diretrizes de estilo do projeto (ruff, mypy)
- [ ] Revisão automática do código concluída
- [ ] Comentários adicionados para lógica complexa
- [ ] Documentação atualizada se necessário
```

## Convenções de Mensagem de Commit

Seguimos a especificação [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<escopo>): <descrição>

[corpo opcional]

[rodapé(s) opcional]
```

### Tipos

| Tipo | Descrição |
|------|-----------|
| `feat` | Novo recurso |
| `fix` | Correção de bug |
| `security` | Correção de vulnerabilidade de segurança |
| `docs` | Apenas documentação |
| `style` | Estilo de código (formatação, ponto e vírgula) |
| `refactor` | Refatoração de código sem alteração de funcionalidade |
| `perf` | Melhoria de desempenho |
| `test` | Adição ou atualização de testes |
| `build` | Sistema de construção ou dependências |
| `ci` | Alterações na configuração de CI |
| `chore` | Tarefas de manutenção |

### Exemplos

```
feat(visão): adicionar detecção de elemento UI YOLOv8
fix(nim): lidar com limite de taxa com backoff exponencial
security(ética): prevenir a evasão da verificação de autorização
docs(readme): adicionar instruções de configuração RAG
test(core): adicionar testes de máquina de estado do loop OODA
```

### Alterações Disruptivas

Indique alterações disruptivas com `!` após o tipo ou com um `BREAKING CHANGE:` no rodapé:

```
feat(api)!: alterar a interface do cliente NIM para assíncrona apenas

BREAKING CHANGE: NIMClient.query() agora requer await
```

## Configuração de Desenvolvimento

```bash
# Clone seu fork
git clone https://github.com/SEU_USUARIO/NVIDIA-ShadowForge-Agent.git
cd NVIDIA-ShadowForge-Agent

# Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Instale ganchos pré-commit
pre-commit install

# Copie e configure o ambiente
cp .env.example .env
# Edite .env com sua chave de API NVIDIA

# Verifique o ambiente
python scripts/health_check.py
python scripts/validate_env.py

# Execute os testes
python -m pytest tests/ -v
```

## Padrões de Codificação

### Python

- **Python 3.10+**: Use dicas de tipo moderno (`X | Y` em vez de `Union`)
- **Async-first**: Todas as operações de I/O devem ser assíncronas
- **Dicas de tipo**: Todas as funções públicas devem ter anotações de tipo
- **Docstrings**: Docstrings no estilo Google para todas as APIs públicas
- **Linguagem**: Código em inglês; comentários/documentação podem estar em português
- **Comprimento da linha**: 100 caracteres máximo (implementado pelo ruff)
- **Importações**: Use `from __future__ import annotations` em todos os módulos

### Exemplo de Docstring

```python
from __future__ import annotations

async def scan_target(host: str, ports: str = "1-1000") -> ScanResult:
    """Realiza um escaneamento de porta no alvo especificado.

    Args:
        host: Endereço IP ou hostname do alvo.
        ports: Intervalo de portas para escanear (padrão: 1-1000).

    Returns:
        Objeto ScanResult com os serviços descobertos.

    Raises:
        AuthorizationError: Se o alvo não estiver na whitelist.
        ConnectionError: Se o alvo for inacessível.
    """
```

### Requisitos de Segurança para Código

1. **Nunca codifique credenciais embutidas** -- use variáveis de ambiente
2. **Nunca registre dados sensíveis** -- chaves de API, senhas, tokens devem ser redigidos
3. **Sempre adicione salvaguardas éticas** a novas capacidades de ataque
4. **Use consultas parametrizadas** -- nunca concatene strings para SQL ou comandos shell
5. **Valide todas as entradas** -- use modelos Pydantic para configuração
6. **Trate erros com elegância** -- nunca exponha pilhas de chamada para usuários não autenticados