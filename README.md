<!-- ShadowForge-Agent README - Hacker Edition -->
<p align="center">
<img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/hacker-header.svg" width="100%" alt="SH4D0WF0RG3 - Autonomous Ethical Hacking AI" />
</p>

<!-- Animated dashboard -->
<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/shadowforge-dashboard.gif" width="100%" alt="SH4D0WF0RG3 Dashboard" />
</p>

---

## <span style="color:#0f0">&#62;</span> Visão Geral

```
[root@shadowforge]# ./agent --init
[*] NVIDIA ShadowForge Agent v1.1.0
[*] Powered by NVIDIA NIM (Llama 3.3 70B)
[*] Ethical Guardrails: ENGAGED (Strict Mode)
[*] 43 security fixes applied from code review
[OK] Ready for authorized penetration testing
```

O **ShadowForge Agent** é um agente autônomo de hacking ético que combina a stack NVIDIA (**NIM**, **Riva**, **TensorRT**) com um motor de decisão completo baseado no **loop OODA** (Observe-Orient-Decide-Act), executando testes de penetração autorizados de ponta a ponta — desde reconhecimento até geração de relatórios.

<p align="center">
<img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/hacker-terminal.svg" width="100%" alt="ShadowForge Terminal Simulation" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/NVIDIA-NIM-76B900?style=for-the-badge&logo=nvidia&logoColor=white&color=black&labelColor=black&border=1;border-color:0f0" alt="NVIDIA NIM" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&color=black&labelColor=black" alt="Python" />
  <img src="https://img.shields.io/badge/SH4D0WF0RG3-v1.1.0-0f0?style=for-the-badge&color=black&labelColor=black" alt="Version" />
</p>

---

## <span style="color:#0f0">&#62;</span> Demonstração em Tempo Real: Reconhecimento (RECON)

<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/tool-recon.svg" width="100%" alt="Simulated Reconnaissance" />
</p>

Executa `nmap`, `shodan` e OSINT passivo de forma autônoma, com enriquecimento de dados via IA:

```bash
$ python main.py --mode stealth --target 10.0.0.0/24
[✓] NVIDIA NIM Connected (Llama-3.3-70B)
[✓] Ethical Guardrails: ENGAGED
[RECON] Passive OSINT gathering...
[SCAN] 192.168.1.10:80 OPEN (Apache/2.4.52)
[SCAN] 192.168.1.10:443 OPEN (TLSv1.3)
[AI] Analyzing attack surface... 3 vectors found
```

---

## <span style="color:#fbbf24">&#62;</span> Demonstração em Tempo Real: Exploração (EXPLOIT)

<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/tool-exploit.svg" width="100%" alt="Simulated Exploitation" />
</p>

O agente identifica vetores de ataque, testa POCs e gera relatórios — sempre com guardrails éticos bloqueando ações destrutivas:

```
[AI] Potential SQL Injection at /api/v1/users?id=
[AI] LFI vulnerability in /download?file=
[GUARD] Blocked: DROP TABLE users; DELETE FROM sessions;
[SAFE] Escalating to human authorization
[REPORT] Generating PDF report with CVSS scores...
```

---

## <span style="color:#0f0">&#62;</span> Arquitetura

<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/architecture.svg" width="90%" alt="Architecture" />
</p>

```
                              +------------------+
                              |   NVIDIA NIM     |
                              |  Llama 3.3 70B   |
                              |  Vision Models    |
                              +--------+---------+
                                       |
+--------+     +--------+     +--------v---------+     +----------+
| Vision |---->|  OODA  |---->|    Planning      |---->| Hacker   |
| Screen |     |  Loop  |     |  RAG (MITRE/OWASP)|    | Tools    |
| OCR    |     | Engine |     |  Orchestrator    |     | Nmap     |
| Detect |     |        |     |                  |     | SQLMap   |
+--------+     +---+----+     +------------------+     | Metasploit|
                   |                                    +----------+
+--------+     +---v----+     +------------------+
| Speech |<--->|  Core  |---->|    Control       |
| Riva   |     | Agent  |     |  Mouse/Keyboard  |
| ASR/TTS|     | State  |     |  Shell/Stealth   |
+--------+     +--------+     +------------------+
```

---

## <span style="color:#0f0">&#62;</span> Loop OODA + Kill Chain

<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/ooda-loop.svg" width="48%" alt="OODA Loop" />
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/kill-chain.svg" width="48%" alt="Kill Chain" />
</p>

---

## <span style="color:#60a5fa">&#62;</span> Correções de Segurança Implementadas

Após revisão completa de código, **43 correções** foram aplicadas:

| Prioridade | Correções | Status |
|------------|-----------|--------|
| **P0 (Crítica)** | Command Injection, API Key leak, CORS aberto | 3/3 Resolvidas |
| **P1 (Alta)** | Vazamento SQLite, Deadlock, NIM não-inicializado | 9/9 Resolvidas |
| **P2 (Média)** | SSL bypass, hash MD5, tipagem fraca, Range IP | 14/14 Resolvidas |
| **P3 (Baixa)** | Docstrings, testes, typos, random não-crypto | 10/10 Resolvidas |
| **Total** | **36** fixes de segurança + **7** de qualidade | **43/43** |

---

## <span style="color:#0f0">&#62;</span> Recursos Principais

- **IA NVIDIA NIM**: Llama 3.3 70B para planejamento tático e geração de relatórios
- **Loop OODA Autônomo**: Ciclo completo Observe → Orient → Decide → Act
- **Sistema de Visão**: Screen capture, OCR, YOLOv8 para análise visual
- **Interface de Voz**: NVIDIA Riva ASR/TTS para operação hands-free
- **Guardrails Éticos**: Bloqueio de ações não autorizadas, destrutivas ou ilegais
- **Kill Chain Completa**: RECON → SCAN → ENUM → EXPLOIT → POST → REPORT
- **Testes Unitários**: Testes críticos para OODA, estado, memória e ética

---

## <span style="color:#0f0">&#62;</span> Instalação

```bash
# Clone
$ git clone https://github.com/Lelolima/ShadowForge-Agent.git
$ cd ShadowForge-Agent

# Ambiente virtual
$ python -m venv .venv
$ source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Dependências
$ pip install -r requirements.txt

# Configure sua NVIDIA API Key
$ cp .env.example .env
# Edite .env e adicione sua chave
```

---

## <span style="color:#0f0">&#62;</span> Uso

```bash
# MODO SIMULAÇÃO (seguro - sem ataques reais)
$ python main.py --mode stealth --target 192.168.1.0/24 --simulate

# Reconhecimento apenas
$ python main.py --mode recon_only --target example.com

# Com interface de voz
$ python main.py --voice --always-listen --target 10.0.0.1
```

| Modo | Descrição |
|------|-----------|
| `stealth` | Low-and-slow, anti-forensics (default) |
| `agressivo` | Fast scanning, full exploitation |
| `recon_only` | Reconhecimento apenas, no exploitation |
| `debug` | Verbose output, todas ações logadas |

---

## <span style="color:#0f0">&#62;</span> Ethical Guardrails

> **WARNING**: Ferramenta para testes de segurança autorizados APENAS.

ShadowForge inclui múltiplas camadas de salvaguardas éticas, agora reforçadas após 43 correções:

- **Verificação de Autorização**: Requer confirmação antes de testar
- **Blacklist/Whitelist**: Restrições de alvo configuráveis
- **Prevenção de Ações Destrutivas**: Não pode deletar, destruir ou wipe
- **Prevenção de Backdoors**: Não pode instalar persistência maliciosa
- **Modo Simulação**: Executa todas as fases sem ataques reais
- **Audit Trail Completo**: Cada ação é logada com timestamp

---

## <span style="color:#0f0">&#62;</span> Estrutura do Projeto

```
shadowforge/
├── main.py                    # Entry point
├── core/                      # Engine do agente
│   ├── agent.py               # OODA Loop + kill chain
│   ├── config.py              # Configuração Pydantic v2
│   ├── state.py               # State machine de campanha
│   ├── memory.py              # Memória curto/longo prazo
│   └── state.py
├── models/                    # Integração NVIDIA AI
│   ├── nim_client.py          # Cliente NIM API
│   ├── multimodal.py          # Modelo visão-linguagem
│   ├── embeddings.py          # Embeddings vetoriais
│   └── riva_client.py         # Riva ASR/TTS
├── vision/                    # Percepção visual
├── control/                   # Interação humanoide
├── hacker_tools/              # Ferramentas de segurança
└── tests/                     # Suite de testes
```

---

## <span style="color:#0f0">&#62;</span> Licença

Este projeto está licenciado sob a **MIT License** com um **Requisito de Uso Ético** — veja o arquivo [LICENSE](LICENSE) para detalhes.

> **Ethics first, hack second.**

---

<p align="center">
  <sub>Wellington de Lima Catarina</sub><br>
  <a href="https://linkedin.com/in/wellington-de-lima-catarina">LinkedIn</a> · <a href="mailto:lelolima806@gmail.com">Email</a>
</p>
