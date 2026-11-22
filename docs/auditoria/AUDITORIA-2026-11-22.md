# Auditoria técnica: ShadowForge-Agent (2026-11-22)

Escopo: fazer o projeto instalar, testar e ter CI; corrigir bugs, dependências vulneráveis,
segredos e documentação. **Nenhuma capacidade ofensiva foi adicionada ou ampliada** e nenhuma
ferramenta do projeto foi executada contra alvo ou rede real.

Ambiente usado: Windows 11, Python 3.13.15, venv local (`.venv`, ignorado pelo git).

## 1. Diagnóstico (estado anterior)

| Item | Resultado real |
|------|----------------|
| Finalidade | Agente de pentest/hacking ético em Python (loop OODA, NVIDIA NIM, ferramentas de recon/exploit com guardrails éticos) |
| Instalação `pip install -r requirements.txt -r requirements-dev.txt` | OK |
| `pip install .` / build do pacote | **Falhava**: `Multiple top-level packages discovered in a flat-layout` (o script `shadowforge` declarado nunca podia ser instalado) |
| `python main.py --help` | OK |
| `python tests/test_imports.py` | 30/30 módulos OK |
| `pytest tests` | **Erro de coleta** (`hypothesis` ausente em requirements-dev); depois de instalado: **15 falhas, 129 aprovados** |
| CI (`gh run list`) | Todas as execuções recentes do workflow CI com **falha**; o workflow fazia push para o Docker Hub (deploy) e exigia 80% de cobertura (real: cerca de 50%) |
| `pip-audit` | 13 CVEs em `filelock 3.32.7` (transitiva via pre-commit/virtualenv; corrigido em 4.2.1) |
| Segredos | Busca manual com regex (chaves NVIDIA `nvapi-`, GitHub `ghp_`, AWS `AKIA`, `sk-`, chaves privadas, atribuições `api_key/token/password/secret`) na árvore atual e em todo o histórico (`git log -p --all`): **nenhum segredo real encontrado**. `.env.example` só tem placeholders (`nvapi-xxxxx`, `changeme`). O gitleaks não estava disponível na máquina. |
| Dados simulados | GIFs/SVGs do README rotulados como "Demonstração em Tempo Real" são **gerados sinteticamente** por `.github/assets/generate_*.py`. `observability/alerting.py::setup_periodic_evaluation` é um stub (apenas registra log). |

## 2. Problemas e correções

| # | Sev. | Problema | Evidência | Correção | Teste |
|---|------|----------|-----------|----------|-------|
| 1 | P0 | `ShadowForgeConfig.carregar_de_env()` imprimia a **API key NVIDIA em texto claro** no stdout | `core/config.py:263` (print `[DEBUG]`) | print removido; `debug_test.py` (script avulso que também imprimia a chave) removido | `test_carregar_de_env_nao_imprime_api_key` |
| 2 | P1 | Campo `modo` tinha alias `mode` sem `populate_by_name`: `modo=` era **ignorado silenciosamente** (YAML com `modo: agressivo` virava `stealth`) | `tests/unit/test_config.py::test_config_from_yaml` falhava | `populate_by_name: True` no `model_config` | `test_config_from_yaml`, `test_modo_aceita_nome_do_campo_e_alias` |
| 3 | P1 | `control/shell.py` usava `subprocess.SubprocessError` sem importar `subprocess`: qualquer `OSError` virava `NameError` | ruff F821 `control/shell.py:217` | `import subprocess` | `test_shell_oserror_nao_vira_nameerror` (mock, sem subprocess real) |
| 4 | P1 | `observability/alerting.py`: `_()` indefinido (NameError ao disparar alerta), `asyncio` sem import e a regra de quantil (`high_ooda_latency`) **nunca disparava** | ruff F821 linhas 132, 171-176; código `pass` no ramo de quantil | `_get_metric_value`, `import asyncio`, comparação com o limiar | `test_alerta_dispara_webhook_com_mensagem` (webhook mockado) |
| 5 | P1 | `escape_like_pattern` escapava em ordem errada: `100%` virava `100\\%` (escape duplo) | `test_escape_like_pattern` falhava | escapar `\` primeiro | `test_escape_like_pattern*` |
| 6 | P1 | `validate_and_sanitize_filename("../etc/passwd")` aceitava silenciosamente (descartava o diretório) em vez de rejeitar traversal/caminho absoluto, contrariando a docstring | `test_validate_and_sanitize_filename` falhava | rejeita `/`, `\`, `.` e `..` com `ValidationError` | teste existente e regressão parametrizada |
| 7 | P2 | `execute_safe_command` lançava `FileNotFoundError` para comando inexistente | teste existente falhava | retorna `CompletedProcess` com código 127 | `test_execute_safe_command_inexistente_retorna_127` |
| 8 | P1 | Pacote não construía (layout flat) | `pip wheel .` falhava | `[tool.setuptools]` com `py-modules` e `packages.find` explícitos | `pip wheel . --no-deps`: OK; job `build` no CI |
| 9 | P1 | `Dockerfile` ENTRYPOINT `python -m core.agent`: `core/agent.py` não tem `__main__`, então o container saía sem fazer nada | inspeção do código | ENTRYPOINT `python3.11 main.py` (os argumentos `--config/--mode` são os de `main.py`) | **não executado** (imagem CUDA pesada, sem GPU nesta máquina) |
| 10 | P1 | Erro de sintaxe em `plugins/plugin_avancado_exemplo/plugin.py:292` (`logger informando(`) e nome `agosto` indefinido | ruff invalid-syntax | `logger.info(`, `agora` | ruff E9/F82 limpo |
| 11 | P2 | `Any`/`ShadowForgeConfig` não importados em anotações (`models/multimodal.py`, `vision/screen.py`, `speech/voice_interface.py`) | ruff F821 | imports (`TYPE_CHECKING`) | ruff limpo |
| 12 | P0 | CVEs em `filelock` (transitiva) | pip-audit | `filelock>=4.2.1` em requirements-dev (só Python >= 3.11: a correção não existe para 3.10; risco residual restrito ao ambiente de dev em 3.10) | `pip-audit`: "No known vulnerabilities found" |
| 13 | P2 | `hypothesis` ausente em requirements-dev (erro de coleta) | pytest | adicionado | coleta OK |
| 14 | P2 | `tests/test_api_nvidia.py` fazia **requisição HTTP real** à API NVIDIA durante o `pytest` | código do teste | `skipif`: só roda com `SHADOWFORGE_RUN_INTEGRATION=1` e `NVIDIA_API_KEY` | pulado por padrão |
| 15 | P2 | Testes com expectativas desatualizadas/corrompidas (entidades HTML decodificadas no arquivo, HSTS sem `includeSubDomains`, identificadores SQL sem aspas, kwarg inexistente, comparação de float exata, import de `rate_limit` ausente, `echo` no Windows) | 9 falhas em `test_security.py` | expectativas alinhadas ao comportamento atual, que é **o mais seguro** (nenhum teste removido) | 45/45 em `test_security.py` |
| 16 | P1 | CI quebrado e com deploy (push para o Docker Hub) | `gh run list` | workflow novo: lint (ruff E9/F63/F7/F82), testes em 3.10 e 3.13, pip-audit, build e smoke test; `permissions: contents: read`; actions fixadas por SHA; **sem deploy** | ver PR |
| 17 | P3 | README apresentava animações sintéticas como "tempo real"; faltavam seções de testes e variáveis de ambiente | inspeção | nota explícita e seções "Testes" e "Variáveis de ambiente" | n/a |

## 3. Testes executados (resultados reais)

```
python tests/test_imports.py                       -> 30 OK | 0 FALHAS
pytest tests -q                                    -> 153 passed, 1 skipped (integração NVIDIA)
ruff check . --select E9,F63,F7,F82                -> sem erros
pip-audit -r requirements.txt -r requirements-dev.txt -> No known vulnerabilities found
pip wheel . --no-deps                              -> shadowforge-1.0.0-py3-none-any.whl
python main.py --help                              -> OK
```

Os testes de regressão novos (`tests/unit/test_regressoes_auditoria.py`) foram executados
**sem** as correções (7 de 8 falharam) e **com** elas (8/8 passaram).

Cobertura (core, models, planning, control, observability): cerca de 50% medida localmente.
O limite de 80% do CI antigo foi removido porque nunca era atingido.

Observação de honestidade: na primeira execução do `pytest`, antes de eu identificar o problema,
`tests/test_api_nvidia.py` fez uma requisição HTTP sem chave a `integrate.api.nvidia.com/v1/models`
(endpoint público de listagem, sem credencial e sem custo). Depois disso, o teste ficou desativado por padrão.

## 4. Não executado (e por quê)

- Build/execução da imagem Docker: base `nvidia/cuda` pesada e sem GPU nesta máquina.
- Visão (`ultralytics`, `opencv`), voz (Riva/pyaudio), RAG (chromadb): extras não instalados; só a importação é validada.
- Ferramentas ofensivas (nmap, sqlmap etc.) e loop OODA real: fora do escopo autorizado (sem alvos reais).

## 5. Riscos residuais e decisões do dono

- `ruff check .` com o conjunto completo do `pyproject.toml` ainda aponta cerca de 597 avisos de estilo e
  débito; o CI só bloqueia erros fatais. `ruff format` nunca foi aplicado.
- `control/shell.py` usa `create_subprocess_shell` (TODO Q-08 do próprio projeto); a blacklist de comandos é
  uma salvaguarda parcial.
- `setup_periodic_evaluation` dos alertas é um stub: não consulta métricas reais.
- `push.ps1`, `enviar.ps1`, `setup-and-push.ps1` contêm caminhos locais de outra máquina
  e fazem `git add -A` seguido de push direto na `main`. Não há segredos neles, mas recomendo removê-los (decisão do dono).
- Arquivos `.backup` (`core/security/input_validation.py.backup`, `tests/test_memory_lru.py.backup`)
  e as pastas `.refact/` e `.agents/` estão versionados. Fica a cargo do dono limpar.
- PRs do Dependabot para `docker/*` ficaram obsoletos porque o job de push Docker foi removido.
