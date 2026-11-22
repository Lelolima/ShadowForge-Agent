<p align="center">
  <img src="docs/assets/banner.svg" width="100%" alt="ShadowForge Agent: agente de pentest autorizado com escopo obrigatório, confirmação, dry-run e trilha de auditoria">
</p>

<p align="center">
  <a href="https://github.com/Lelolima/ShadowForge-Agent/actions/workflows/ci.yml"><img src="https://github.com/Lelolima/ShadowForge-Agent/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.10%20|%203.13-blue" alt="Python 3.10 e 3.13">
  <img src="https://img.shields.io/badge/licen%C3%A7a-MIT-green" alt="Licença MIT">
</p>

# ShadowForge Agent

Agente em Python para **testes de intrusão autorizados**. Ele conduz uma campanha por
um loop OODA (Observe → Orient → Decide → Act) seguindo a kill chain (recon, scan,
enumeração, exploração, pós-exploração, relatório). Cada ação passa por guardrails
éticos antes de tocar um alvo. Também traz ferramentas defensivas para **triagem de
scans já existentes**, **revisão de cabeçalhos HTTP**, **revisão de configuração** e
**geração de relatórios**.

> [!IMPORTANT]
> **Uso responsável e autorização.** Use este software **somente** contra sistemas para os
> quais você tem **autorização expressa e por escrito** do responsável, dentro do escopo e
> da janela combinados. Testar sistemas de terceiros sem permissão é crime em muitas
> jurisdições, incluindo o Brasil (Lei 12.737/2012, art. 154-A do Código Penal). Os autores
> não se responsabilizam pelo mau uso.
> O projeto foi feito para dificultar o uso fora do autorizado:
> - o escopo é obrigatório fora do dry-run;
> - ações intrusivas pedem confirmação;
> - tudo fica registrado numa trilha de auditoria verificável.
>
> Não desative essas proteções.

## Sumário

- [Arquitetura](#arquitetura)
- [Instalação](#instalação)
- [Uso](#uso)
- [Salvaguardas](#salvaguardas)
- [Exemplos de casos reais](#exemplos-de-casos-reais)
- [Testes e CI](#testes-e-ci)
- [Configuração e variáveis de ambiente](#configuração-e-variáveis-de-ambiente)
- [Limitações reais](#limitações-reais)
- [Estrutura do projeto](#estrutura-do-projeto)

## Arquitetura

<p align="center">
  <img src="docs/assets/arquitetura.svg" width="100%" alt="Diagrama: CLI e config/escopo alimentam o agente OODA; cada ação passa pelos guardrails antes das ferramentas; resultados viram relatórios e todos os eventos vão para a trilha de auditoria">
</p>

<details>
<summary><b>Componentes em detalhe</b> (clique para expandir)</summary>

| Componente | Arquivo | Papel |
|---|---|---|
| CLI | `main.py` | Argumentos, banner, confirmação interativa, `--check-config` |
| Configuração | `core/config.py`, `config/default.yaml` | Pydantic; seções `agente`, `etica`, `ooda`, `nvidia` |
| Escopo | `core/scope.py` | Regra única de autorização: IP, CIDR, hostname, `*.dominio`; blacklist por sobreposição de redes |
| Agente | `core/agent.py` | Loop OODA, decisões por fase, guardrails, confirmação, auditoria e relatório |
| Estado e memória | `core/state.py`, `core/memory.py` | Campanha, ações e vulnerabilidades (SQLite) |
| Auditoria | `core/audit.py` | JSON Lines encadeado por SHA-256, com segredos mascarados |
| Recon | `hacker_tools/recon/scanner.py` | Nmap (python-nmap ou binário), DNS, fingerprint web, parser de XML |
| Triagem | `hacker_tools/recon/triagem.py` | Classifica exposições de scans **já gravados** |
| Revisão web | `hacker_tools/recon/web_review.py` | Cabeçalhos de segurança, banners, flags de cookie |
| Revisão de config | `core/revisao_config.py` | Guardrails desligados, escopo amplo, segredos em texto claro |
| Relatórios | `hacker_tools/reporting/` | Markdown, JSON e HTML; PDF se `reportlab` estiver instalado |
| Modelos (opcional) | `models/` | Cliente NVIDIA NIM; sem chave, opera em modo local sem chamadas |

</details>

## Instalação

Requisitos: Python 3.10 ou superior. Para recon real, o binário `nmap` no `PATH`.

```bash
git clone https://github.com/Lelolima/ShadowForge-Agent.git
cd ShadowForge-Agent
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# desenvolvimento (testes, lint, tipos):
pip install -r requirements-dev.txt -c constraints-py313.txt   # versões exatas validadas em 3.13
cp .env.example .env               # opcional; nunca commite o .env
```

Extras opcionais (pesados, fora dos testes e do CI): `requirements-vision.txt`,
`requirements-speech.txt`, `requirements-rag.txt`, `requirements-hacker.txt`.

## Uso

<p align="center">
  <img src="docs/assets/fluxo-uso.svg" width="100%" alt="Fluxo de uso: 1 revisar config, 2 ensaiar em dry-run, 3 definir escopo, 4 executar confirmando, 5 entregar relatório e auditoria">
</p>

```bash
# 1. Revisar a configuração (exit 1 se houver achado crítico/alto)
python main.py --check-config

# 2. Ensaiar sem tocar o alvo: fases sem implementação real aparecem como [SIMULADO]
python main.py --dry-run --target 10.0.0.5 --no-gpu

# 3 e 4. Execução real: escopo obrigatório e confirmação antes de cada ação intrusiva
python main.py --target 10.0.0.5 --scope 10.0.0.0/24
python main.py --target app.lab.local --scope-file escopo.txt --yes   # não interativo
```

<details>
<summary><b>Todas as opções da linha de comando</b></summary>

| Opção | Descrição |
|---|---|
| `--target ALVO` | Alvo inicial (IP, CIDR ou hostname) |
| `--scope ALVO` | Entrada de escopo autorizado (repetível). Obrigatório fora do dry-run |
| `--scope-file ARQ` | Arquivo com um alvo autorizado por linha (`#` comenta) |
| `--dry-run` / `--simulate` | Nada é executado contra o alvo; o relatório sai marcado como DRY-RUN |
| `--yes` | Confirma ações intrusivas automaticamente (o alvo ainda precisa estar no escopo) |
| `--check-config` | Só revisa o YAML de `--config` e sai |
| `--mode` | `stealth` (padrão), `agressivo`, `recon_only`, `debug` |
| `--config ARQ` | YAML de configuração (padrão `config/default.yaml`) |
| `--max-iteracoes N` | Limite de ciclos OODA |
| `--vision` | Habilita captura de tela; com API key, as imagens são enviadas à NVIDIA |
| `--voice`, `--always-listen` | Interface de voz (requer Riva e os extras de fala) |
| `--no-gpu`, `--gpu N` | Seleção de GPU (informativa) |
| `--campaign ID` | Identificador da campanha |
| `--log-level`, `--ascii` | Nível de log; saída sem Rich |

</details>

Saídas: relatórios em `data/reports/`, trilha em `data/audit/<campanha>.jsonl`, logs em `logs/`.
Todos esses diretórios são ignorados pelo git.

## Salvaguardas

| Proteção | Comportamento |
|---|---|
| Escopo obrigatório | Fora do dry-run, alvo sem escopo ou fora dele é **bloqueado** (`core/scope.py`) |
| Blacklist | `0.0.0.0/8`, loopback, link-local/metadata de nuvem, multicast e broadcast sempre bloqueados |
| Confirmação | Ações que tocam o alvo pedem `[s/N]`; sem terminal e sem `--yes`, a ação é **negada** (fail-closed) |
| Encerramento | Três bloqueios seguidos encerram a campanha, em vez de repetir em loop |
| Dry-run | `--dry-run` não toca o alvo; dados ilustrativos são sempre rotulados `[SIMULADO]` |
| Auditoria | Cada decisão, confirmação e ação vai para JSONL com hash encadeado; `core.audit.verificar_trilha()` detecta adulteração |
| Políticas | Ações destrutivas, backdoor/persistência e exfiltração real são recusadas (`verificar_etica`) |
| Privacidade | Visão (captura de tela) é **opt-in** (`--vision`); segredos nunca são impressos nem gravados na trilha |
| SSRF | O fingerprint web não acessa metadata de nuvem; loopback só quando está explicitamente no escopo |

<details>
<summary><b>Exemplo de linha da trilha de auditoria</b></summary>

```json
{"ts": "2026-11-22T14:25:34+00:00", "campanha": "SF-20261122-112524", "operador": "analista",
 "evento": "acao_bloqueada", "acao": "executar_recon", "alvo": "10.0.0.5",
 "motivo": "operador não confirmou a ação intrusiva", "simulado": false, "hash": "0745dd38..."}
```

</details>

## Exemplos de casos reais

Os exemplos são completos e executáveis, e rodam no CI (`tests/examples/test_exemplos.py`).
Usam só dados sintéticos versionados ou um laboratório que o próprio exemplo cria em `127.0.0.1`.

| # | Cenário | Comando |
|---|---|---|
| 01 | [Triagem de XML do Nmap já existente](examples/01_triagem_nmap/) | `python examples/01_triagem_nmap/triagem.py` |
| 02 | [Relatório de pentest a partir de achados](examples/02_relatorio_achados/) | `python examples/02_relatorio_achados/gerar_relatorio.py` |
| 03 | [Revisão de configuração insegura](examples/03_revisao_config/) | `python examples/03_revisao_config/revisar.py` |
| 04 | [Reconhecimento web de laboratório local](examples/04_lab_web_local/) | `python examples/04_lab_web_local/lab_web.py --yes` |

<details>
<summary><b>Saída real do exemplo 01</b></summary>

```
Hosts ativos no XML: 4 | analisados (no escopo): 3
Ignorados por estarem FORA do escopo: 10.10.20.7
SEVERIDADE ALVO               ACHADO
HIGH       10.10.10.12:3306   Banco de dados/cache acessível pela rede
HIGH       10.10.10.12:6379   Banco de dados/cache acessível pela rede
HIGH       10.10.10.20:23     Telnet exposto (credenciais em texto claro)
MEDIUM     10.10.10.20:21     FTP exposto (sem criptografia)
MEDIUM     10.10.10.20:445    SMB exposto
MEDIUM     10.10.10.5:22      OpenSSH desatualizado (OpenSSH 7.4)
MEDIUM     10.10.10.5:80      Apache httpd desatualizado (Apache httpd 2.4.41)
LOW        10.10.10.5:80      Serviço HTTP sem TLS
Resumo: {"critical": 0, "high": 3, "medium": 4, "low": 1, "info": 0}
```

</details>

## Testes e CI

```bash
pip install -r requirements.txt -r requirements-dev.txt
python tests/test_imports.py     # importa todos os módulos
pytest tests -q --cov            # unitários, fluxo do agente e exemplos (sem rede externa)
ruff check .                     # lint (conjunto completo do pyproject.toml)
mypy core/scope.py core/audit.py core/config.py core/agent.py --follow-imports=silent
```

- `tests/test_api_nvidia.py` faz chamadas reais à NVIDIA e fica **desativado** por padrão. Para rodá-lo, defina `SHADOWFORGE_RUN_INTEGRATION=1` e `NVIDIA_API_KEY`.
- O CI (`.github/workflows/ci.yml`) roda:
  - ruff;
  - mypy nos módulos centrais;
  - testes em Python 3.10 (faixas do requirements) e 3.13 (versões exatas de `constraints-py313.txt`), com piso de cobertura;
  - `pip-audit`;
  - build do pacote com smoke test da CLI.
- Permissões: `contents: read`. Actions fixadas por SHA. **Sem deploy.**

## Configuração e variáveis de ambiente

O comportamento vem de `config/default.yaml`. Em `agente.etica.whitelist_hosts` fica o
escopo do contrato, e `--scope` acrescenta entradas na linha de comando. As variáveis
ficam em `.env` (veja `.env.example`, só com placeholders):

| Variável | Uso |
|---|---|
| `NVIDIA_API_KEY` | Chave da API NVIDIA NIM; sem ela, nenhuma chamada é feita. Chamadas reais podem gerar custo |
| `SHADOWFORGE__NVIDIA__API_KEY`, `SHADOWFORGE_MODE` | Lidas por `ShadowForgeConfig.carregar_de_env()` quando o YAML não existe |
| `RIVA_SERVER` | Servidor Riva (só com interface de voz) |
| `SHODAN_API_KEY`, `CENSYS_API_ID`, `CENSYS_API_SECRET` | OSINT opcional |
| `*_WEBHOOK_URL` | Webhooks de alertas (`observability/alerting.py`) |

## Limitações reais

- No loop autônomo, **só o reconhecimento** (`executar_recon`: nmap, DNS e fingerprint web) executa de verdade. As fases de scan, enumeração, PoC e privesc devolvem **dados ilustrativos**, sempre rotulados `[SIMULADO]` e `simulado: true` na trilha.
- O recon real depende do `nmap` instalado. Sem ele, a lista de hosts vem vazia e a falha fica registrada no log.
- O planejamento com LLM (NIM) só funciona com `NVIDIA_API_KEY`. RAG sem `chromadb` usa um modo em memória reduzido.
- Visão, voz e RAG exigem extras pesados (OpenCV, Ultralytics, Riva, ChromaDB) e não são testados no CI.
- O dashboard (`api/dashboard.py`) exige FastAPI, que não está no `requirements.txt`; sem ele, o agente apenas não o inicia.
- A imagem Docker (base CUDA) **não é construída nem testada no CI**.
- A cobertura de testes está em torno de 58%. Os módulos de exploração e pós-exploração têm pouca cobertura e não são acionados pelo loop autônomo.

## Estrutura do projeto

```
core/            agente, config, escopo, auditoria, estado, memória, segurança, resiliência
hacker_tools/    recon (scanner, triagem, revisão web), reporting, exploit, post_exploitation
models/          cliente NVIDIA NIM e prompts      planning/   orquestração e RAG
control/ vision/ speech/   controle de shell/teclado, visão e voz (opcionais)
examples/        cenários reais executáveis         tests/      unitários, fluxo e exemplos
config/          default.yaml                       docs/       arquitetura, auditorias, assets
```

> [!NOTE]
> Sobre as imagens: os SVGs em `docs/assets/` são animados com CSS interno e seguem o tema
> claro/escuro do sistema e a preferência de movimento reduzido. Imagens embutidas por `<img>`
> não recebem clique nem hover no GitHub, por isso os detalhes interativos usam `<details>`.

## Licença

[MIT](LICENSE). Veja também [SECURITY.md](SECURITY.md), [PRIVACY.md](PRIVACY.md) e [CONTRIBUTING.md](CONTRIBUTING.md).
