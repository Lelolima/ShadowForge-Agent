# NVIDIA ShadowForge Agent

Autonomous Ethical Hacking AI - Powered by NVIDIA

<p align="center">
  <a href="https://github.com/Lelolima/ShadowForge-Agent">
    <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/shadowforge-dashboard.gif" width="100%" alt="SH4D0WF0RG3 Dashboard - Real-time Agent Monitoring" />
  </a>
</p>

## Visão Geral

O ShadowForge Agent é um agente de hacking ético autônomo baseado em inteligência artificial que combina o poder da stack NVIDIA (NIM, Riva, TensorRT) com um motor de decisão completo do loop OODA para realizar testes de penetração autorizados - desde reconhecimento até a geração de relatórios.

## Arquitetura

```
                              +------------------+
                              |   NVIDIA NIM      |
                              |  Llama 3.3 70B |
                              |  Vision Models   |
                              +--------+---------+
                                       |
+--------+     +--------+     +--------v---------+     +----------+
| Vision |---->|  OODA  |---->|    Planning      |---->| Hacker    |
| Screen |     |  Loop   |     |  RAG (MITRE/OWASP)|    | Tools    |
| OCR    |     | Engine  |     |  Orchestrator    |     | Nmap     |
| Detect |     |        |     |                  |     | SQLMap   |
+--------+     +---+----+     +------------------+     | Metasploit|
                   |                                    +----------+
+--------+     +---v----+     +------------------+
| Speech |<--->|  Core  |---->|    Control       |
| Riva   |     | Agent   |     |  Mouse/Keyboard    |
| ASR/TTS|     | State  |     |  Shell/Stealth  |
+--------+     +--------+     +------------------+
```

## Recursos Principais

- **Análise Baseada em IA**: Integração com NVIDIA NIM com Llama 3.3 70B para planejamento, raciocínio e geração de relatórios
- **Loop OODA Autônomo**: Ciclo Observe -> Orient -> Decide -> Act com máquina de estados da kill chain
- **Sistema de Visão**: Captura de tela, OCR, detecção de objetos YOLOv8 para análise visual
- **Interface de Voz**: NVIDIA Riva ASR/TTS para operação sem mãos
- **Guardrails Éticos**: Salvaguardas integradas que previnem ações não autorizadas, destrutivas ou ilegais
- **Kill Chain Completa**: RECON -> SCAN -> ENUM -> EXPLOIT -> POST -> REPORT

## Correções Implementadas

### Correções de Segurança (P0)
- ✅ C-01: Command Injection via `argumentos_extra` no Nmap
- ✅ C-02: Shodan API Key exposta na URL de requisição
- ✅ C-03: CORS totalmente aberto no Dashboard API

### Correções de Alta Severidade (P1)
- ✅ H-01: Conexões SQLite não fechadas
- ✅ H-02: Erros silenciosamente engolidos
- ✅ H-03: Sessão aiosqlite criada a cada operação
- ✅ H-04: `Proc.env.update(env)` no shell pode vazar variáveis de ambiente
- ✅ H-05: `_safe_quote()` no Windows não escapa `"` corretamente
- ✅ H-06: `recuperar_licoes()` ignora campos faltando
- ✅ H-07: `ScreenCapture.capturar()` retorna `None` para frames sem mudança
- ✅ H-08: `plugin.py` — deadlock em ordenação de dependências
- ✅ H-09: `NemotronVision` nunca inicializa `_nim_client`

### Correções de Média Severidade (P2)
- ✅ M-01: `MemoriaCurtoPrazo._evict()` tem complexidade O(n²)
- ✅ M-02: Hash MD5 usado para cache de embeddings
- ✅ M-03: Embedding fallback produz vetor de dimensão incorreta
- ✅ M-04: `OCRExtractor._parsear_nmap_output` sempre cria um único host
- ✅ M-05: SSL verification desabilitado em todos os requests
- ✅ M-06: Discordância entre `FaseOperacao` no `state.py` e ao agent
- ✅ M-07: `PluginManager._load_plugin` registra módulo no `sys.modules` global
- ✅ M-08: `StealthShell.executar_stream` ignora timeout entre linhas
- ✅ M-09: `HTTP` flow fingerprint aceita qualquer URL
- ✅ M-10: `RivaClient.conectar()` é síncrono bloqueante
- ✅ M-11: `_resposta_simulada` usa f-string mal formatada
- ✅ M-12: Variável `re` sombreia builtin
- ✅ M-13: Listagem de ranges privados incompleta
- ✅ M-14: `control/stealth_enhanced.py` — Código inalcançável

### Correções de Baixa Severidade (P3)
- ✅ L-01: Tipagem fraca (Any para config)
- ✅ L-02: Erro de digitação: "Licões" vs "Lições"
- ✅ L-03: Import temporário dentro de loops
- ✅ L-04: `_safe_quote()` não é usada em `shell.executar()`
- ✅ L-05: `logger_mod` em `vision/screen.py` — naming inconsistente
- ✅ L-06: `SecretManager._gerar_mac_aleatorio` usa `random` não criptográfico
- ✅ L-07: Docstrings em português com termos em inglês misturados
- ✅ L-08: Tipo de retorno específico em report_generator
- ✅ L-09: Testes unitários para OODA, state, memory, ethics
- ✅ L-10: `post_exploitation/pivot.py` retorna `{"erro": False}` em falha

## Novos Testes

Foram implementados testes unitários abrangentes para os componentes críticos:

```python
# tests/test_core.py
class TestEstadoAgente:
    def test_criacao_basica(self) -> None:
        # Testa criação básica do estado do agente

    def test_registrar_vulnerabilidade(self) -> None:
        # Testa registro de vulnerabilidades

    def test_registrar_acao(self) -> None:
        # Testa registro de ações

    def test_avancar_fase(self) -> None:
        # Testa avanço de fases

    def test_adicionar_alvo(self) -> None:
        # Testa adição de alvos

    def test_resumo(self) -> None:
        # Testa resumo do estado

    def test_persistencia_db(self) -> None:
        # Testa persistência em banco de dados

class TestMemoriaCurtoPrazo:
    def test_adicionar_e_buscar(self) -> None:
        # Testa adição e busca em memória de curto prazo

    def test_buscar_por_tags(self) -> None:
        # Testa busca por tags

    def test_evict(self) -> None:
        # Testa remoção de entradas antigas

    def test_contexto_recente(self) -> None:
        # Testa contexto recente

class TestGuardrailsEticos:
    def test_verificar_etica_acao_segura(self) -> None:
        # Testa verificação de ações seguras

    def test_verificar_etica_acao_destrutiva(self) -> None:
        # Testa ações destrutivas bloqueadas

    def test_verificar_etica_backdoor(self) -> None:
        # Testa prevenção de backdoors

    def test_verificar_etica_blacklist(self) -> None:
        # Testa blacklist de hosts

    def test_verificar_etica_modo_desenvolvimento(self) -> None:
        # Testa modo desenvolvimento

    def test_verificar_etica_whitelist(self) -> None:
        # Testa whitelist de hosts

class TestOODAKillChain:
    def test_fluxo_fases(self) -> None:
        # Testa o fluxo completo das fases OODA

    def test_fase_emoji(self) -> None:
        # Testa emojis das fases

    def test_severidade_cvss_range(self) -> None:
        # Testa ranges de severidade CVSS
```

## Status Final

Todas as correções identificadas na revisão de código foram implementadas com sucesso. O ShadowForge-Agent agora está em conformidade com as melhores práticas de segurança, performance e qualidade de código.

## Documentação Adicional

Para mais informações detalhadas, consulte:
- `docs/RELATORIO_COMPLETO.md` - Documentação técnica completa
- `CORRECOES_CONCLUIDAS.md` - Relatório detalhado de correções
- `RELATORIO_FINAL.md` - Relatório executivo resumido

## Licença

Este projeto está licenciado sob a licença MIT com um **Requisito de Uso Ético** - veja o arquivo [LICENSE](LICENSE) para detalhes.