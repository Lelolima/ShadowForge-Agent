# NVIDIA ShadowForge Agent - Arquitetura do Sistema

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPERADOR (Humano)                            │
│         Voz (Riva ASR/TTS)  │  CLI  │  Texto                   │
└──────────┬──────────────────┼───────┼───────────────────────────┘
           │                  │       │
           ▼                  ▼       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN.PY (LAUNCHER)                           │
│           Parse CLI → Detect GPU → Init → Run                   │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│              CORE/AGENT.PY (MOTOR OODA)                         │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐     │
│  │ OBSERVE │→│ ORIENT   │→│ DECIDE  │→│ ACT          │     │
│  │ Visão   │  │ Analise  │  │ Plano   │  │ Execução     │     │
│  │ Voz     │  │ RAG      │  │ Ética   │  │ Controle     │     │
│  │ Shell   │  │ Memória  │  │ Risk    │  │ Ferramentas  │     │
│  └─────────┘  └──────────┘  └─────────┘  └──────────────┘     │
│                                                                 │
│  STATE MACHINE: IDLE→RECON→SCAN→ENUM→EXPLOIT→POST→REPORT→OK  │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬──────────────────────┘
   │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────────┐
│VISION││SPEECH││CTRL  ││TOOLS ││PLAN  ││MODELS││MEMORY    │
│      ││      ││      ││      ││      ││      ││          │
│Screen││Riva  ││Mouse ││Nmap  ││Orch  ││NIM   ││Curto Pz  │
│OCR   ││ASR   ││Keybd ││OSINT ││RAG   ││Nemotr││Longo Pz  │
│Nemet ││TTS   ││Shell ││WebExp││MITRE ││Riva  ││SQLite    │
│YOLO  ││Voice ││Stealth│NetExp││ATT&CK││Embed ││ChromaDB  │
└──────┘└──────┘└──────┘└──────┘└──────┘└──────┘└──────────┘
   │         │        │        │        │        │        │
   └─────────┴────────┴────────┴────────┴────────┴────────┘
                              │
                              ▼
               ┌──────────────────────────┐
               │   NVIDIA STACK           │
               │  NIM (Inference)         │
               │  Riva (ASR/TTS)          │
               │  TensorRT (Optimization) │
               │  CUDA (GPU Compute)      │
               │  DeepStream (Video Proc) │
               │  NeMo Retriever (RAG)    │
               └──────────────────────────┘
```

## Loop OODA - Detalhamento

### OBSERVE (Observar)
O agente coleta informações do ambiente em tempo real:
- **Captura de tela**: mss captura frames a 1-30 FPS adaptativo
- **Análise visual**: Nemotron 3 Nano Omni compreende desktop
- **OCR semântico**: Tesseract + Nemotron extraem dados estruturados
- **Detecção UI**: YOLO com TensorRT identifica elementos clicáveis
- **ASR**: Riva transcreve comandos de voz em <250ms
- **Processos**: psutil lista processos em execução

### ORIENT (Orientar)
O agente contextualiza observações:
- **RAG MITRE**: Busca técnicas táticas relevantes
- **Memória**: Curto prazo (sessão) + Longo prazo (campanhas anteriores)
- **Lições aprendidas**: Consulta experiências passadas
- **Correlação**: Relaciona dados com fase atual da kill chain

### DECIDE (Decidir)
O agente decide a próxima ação:
- **State machine**: Avança fases conforme resultados
- **Guardrails éticos**: Verifica autorização ANTES de qualquer ação
- **Risk assessment**: Avalia riscos de cada ação
- **Adaptive planning**: Redireciona se caminho atual falha

### ACT (Agir)
O agente executa a ação decidida:
- **Controle**: Mouse/teclado stealth com movimentos humanos
- **Shell**: Executa ferramentas de pentest (Nmap, SQLMap, etc.)
- **Geração**: Cria PoCs, relatórios, scripts
- **Registro**: Todas as ações auditadas em SQLite

## Stack NVIDIA - Integração Profunda

| Componente | Modelo NVIDIA | Uso | Latência Alvo |
|-----------|---------------|-----|---------------|
| Planejamento | Nemotron-4-340B | Decisão estratégica | <2s |
| Raciocínio | Llama-3.1-Nemotron-70B | Análise técnica | <1s |
| Visão | Nemotron-3-Nano-Omni-VL | Compreensão visual | <500ms |
| ASR | Riva ASR | Transcrição voz | <250ms |
| TTS | Riva TTS | Síntese de fala | <150ms |
| Embeddings | NV-Embed-v1 | RAG semântico | <100ms |
| Deploy | NIM | Inferência otimizada | - |
| Aceleração | TensorRT | GPU optimization | - |
| Video | DeepStream | Processamento tela | - |

## Fluxo de Dados

```
[TELA] → mss → PIL Image → Nemotron Omni → Análise Semântica
                                            ↓
                                    [RESULTADO VISUAL]
                                            ↓
[VOZ] → Riva ASR → Texto ──────────→ [DECISÃO OODA]
                                            ↓
[CLI] → Parse ─────────────────────────────→ │
                                            ↓
                                    [VERIFICAÇÃO ÉTICA]
                                            ↓
                                    [AÇÃO AUTORIZADA]
                                            ↓
                               Mouse/Keyboard/Shell/Ferramenta
                                            ↓
                                    [RESULTADO + AUDIT]
                                            ↓
                               Memória + RAG + Estado
```

## Guardrails Éticos

Todos os módulos implementam `verificar_autorizacao()` que:
1. Checa whitelist/blacklist de hosts
2. Verifica escopo da campanha
3. Bloqueia ações destrutivas
4. Bloqueia instalação de backdoors
5. Bloqueia exfiltração de dados reais
6. Registra TODA decisão no audit trail
7. Permite override apenas em modo simulação

## Persistência

| Dado | Storage | Local |
|------|---------|-------|
| Estado da campanha | SQLite | data/state/shadowforge.db |
| Memória longo prazo | SQLite | data/memory/long_term.db |
| RAG vetores | ChromaDB | data/chromadb/ |
| Logs | Arquivo rotativo | logs/shadowforge.log |
| Configuracão | YAML + Pydantic | config/default.yaml |

## Extensibilidade - Sistema de Plugins

Novas ferramentas podem ser adicionadas:
1. Criar módulo em `hacker_tools/nova_categoria/`
2. Implementar classe com `verificar_autorizacao()`
3. Registrar no `__init__.py` do pacote
4. Adicionar entrada no config YAML
5. O motor OODA detecta automaticamente via lazy import
