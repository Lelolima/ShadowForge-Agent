<p align="center">
<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/NVIDIA-NIM-76B900?style=for-the-badge&logo=nvidia&logoColor=white">
<img src="https://img.shields.io/badge/LGPD-Compliant-green?style=for-the-badge">
<img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge">
<img src="https://img.shields.io/badge/Status-Beta-orange?style=for-the-badge">
</p>

<h1 align="center">NVIDIA ShadowForge Agent</h1>

<p align="center">
<code>SH4D0WF0RG3 v1.0.0</code><br>
<sub>Autonomous Ethical Hacking AI - Powered by NVIDIA</sub><br>
<sup><em>Ethics first, hack second.</em></sup>

<p align="center">
<a href="https://linkedin.com/in/wellington-de-lima-catarina">
<img src="https://img.shields.io/badge/LinkedIn-Wellington%20de%20Lima%20Catarina-0A66C2?style=flat-square&logo=linkedin"></a>
<a href="mailto:lelolima806@gmail.com">
<img src="https://img.shields.io/badge/Email-lelolima806%40gmail.com-D14836?style=flat-square&logo=gmail&logoColor=white"></a>
</p>
</p>

<p align="center">
  <a href="https://github.com/Lelolima/ShadowForge-Agent">
    <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/shadowforge-dashboard.gif" width="100%" alt="SH4D0WF0RG3 Dashboard - Real-time Agent Monitoring" />
  </a>
</p>

---

## Overview

ShadowForge is an autonomous ethical hacking agent that combines the **NVIDIA AI stack** (NIM, Riva, TensorRT) with a full **OODA Loop** decision engine to perform authorized penetration tests — from reconnaissance to reporting.

**Key capabilities:**
- **AI-Powered Analysis**: NVIDIA NIM integration with Llama 3.3 70B for planning, reasoning, and report generation
- **Autonomous OODA Loop**: Observe -> Orient -> Decide -> Act cycle with kill chain state machine
- **Vision System**: Screen capture, OCR, YOLOv8 object detection for visual analysis
- **Voice Interface**: NVIDIA Riva ASR/TTS for hands-free operation
- **Ethical Guardrails**: Built-in safeguards preventing unauthorized, destructive, or illegal actions
- **Full Kill Chain**: RECON -> SCAN -> ENUM -> EXPLOIT -> POST -> REPORT

## Architecture

```
                              +------------------+
                              |   NVIDIA NIM     |
                              |  Llama 3.3 70B   |
                              |  Vision Models   |
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

## Step-by-Step Workflow

The following animated demos walk through the entire ShadowForge workflow — from installation to final report.

### Step 1 — Installation

```bash
git clone https://github.com/Lelolima/ShadowForge-Agent.git
cd ShadowForge-Agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/install-shadowforge.gif" width="100%" alt="Step 1: Install ShadowForge" />
</p>

---

### Step 2 — Configuration

```bash
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
python scripts/validate_env.py
python scripts/health_check.py
```

<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/configure-shadowforge.gif" width="100%" alt="Step 2: Configure ShadowForge" />
</p>

---

### Step 3 — Reconnaissance (RECON)

```bash
python main.py --mode recon_only --target 192.168.1.0/24
```

<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/recon-shadowforge.gif" width="100%" alt="Step 3: Reconnaissance" />
</p>

---

### Step 4 — Scanning & Enumeration

```bash
python main.py --mode stealth --target 192.168.1.0/24 --simulate
```

<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/scan-shadowforge.gif" width="100%" alt="Step 4: Scanning and Enumeration" />
</p>

---

### Step 5 — Exploitation & Post-Exploitation

```bash
python main.py --mode agressivo --target 192.168.1.10
# Simulation mode (safe)
python main.py --mode stealth --target 192.168.1.0/24 --simulate
```

<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/exploit-shadowforge.gif" width="100%" alt="Step 5: Exploitation and Post-Exploitation" />
</p>

---

### Step 6 — Report Generation

```bash
# Auto-generated after campaign completes
ls ./reports/
```

<p align="center">
  <img src="https://raw.githubusercontent.com/Lelolima/ShadowForge-Agent/main/.github/assets/report-shadowforge.gif" width="100%" alt="Step 6: Report Generation" />
</p>

---

## Quick Start

### Prerequisites

- Python 3.10+
- NVIDIA API Key (get one at [build.nvidia.com](https://build.nvidia.com/))
- (Optional) NVIDIA GPU with CUDA for local inference

### Installation

```bash
# Clone the repository
git clone https://github.com/Lelolima/ShadowForge-Agent.git
cd ShadowForge-Agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install core dependencies
pip install -r requirements.txt

# Install optional capabilities
pip install -r requirements-vision.txt    # Screen capture, OCR, detection
pip install -r requirements-speech.txt    # Voice interface
pip install -r requirements-rag.txt       # MITRE/OWASP knowledge base
pip install -r requirements-hacker.txt    # Nmap, Shodan, etc.

# Configure environment
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

### Usage

```bash
# Run with simulation mode (safe - no real attacks)
python main.py --mode stealth --target 192.168.1.0/24 --simulate

# Run with specific mode
python main.py --mode recon_only --target example.com

# Run with voice interface
python main.py --voice --always-listen --target 10.0.0.1

# Health check
python scripts/health_check.py

# Validate environment
python scripts/validate_env.py
```

### Modes

| Mode | Description |
|------|-------------|
| `stealth` | Low-and-slow, anti-forensics enabled (default) |
| `agressivo` | Fast scanning, full exploitation |
| `recon_only` | Reconnaissance only, no exploitation |
| `debug` | Verbose output, all actions logged |

---

## Kill Chain Phases

```
IDLE -> RECON -> SCAN -> ENUM -> EXPLOIT -> POST -> REPORT -> COMPLETED
  |       |        |       |        |        |        |
  v       v        v       v        v        v        v
 Wait  Nmap/OSINT  Port   Service  PoC     Privesc  PDF/HTML
       Shodan     Scan   Enum     Gen     Pivot    Report
```

---

## Ethical Safeguards

> **WARNING**: This tool is for AUTHORIZED security testing ONLY.

ShadowForge includes multiple ethical guardrails:

- **Authorization Verification**: Requires confirmation before testing
- **Blacklist/Whitelist**: Configurable target restrictions
- **Destructive Action Prevention**: Cannot delete, destroy, or wipe data
- **Backdoor Prevention**: Cannot install persistent backdoors
- **Exfiltration Prevention**: Cannot exfiltrate real data
- **Simulation Mode**: Run all phases without executing real attacks
- **Full Audit Trail**: Every action is logged with timestamp

---

## Audit Trail Example

```
[14:49:32] [VISION] Detected input field: 'admin_login'
[14:49:34] [OCR] Extracted hash: 5d41402abc4b2a76...
[14:49:36] [NET] Port 443 open (HTTPS/TLS1.3)
[14:49:38] [AI] Reasoning: Potential SQLi vector identified
[14:49:40] [GUARD] Blocked destructive command: rm -rf
[14:49:42] [RIVA] Voice command: 'Enumerate services'
[14:49:44] [MEM] Context window updated (14k tokens)
[14:49:46] [STEALTH] Anti-forensics cleanup executed
[14:49:48] [NIM] Llama-3.3 inference completed (45ms)
[14:49:50] [SAFE] PII detected and redacted in output
```

---

## LGPD & Privacy Compliance

ShadowForge is designed with privacy-first principles:

- **No cloud data storage** — all data stays local
- **NVIDIA API** — prompts sent to NIM contain no PII by default
- **Local database** — SQLite for state, ChromaDB for RAG knowledge
- **Configurable retention** — auto-cleanup after campaign
- **Privacy Policy** — see [PRIVACY.md](PRIVACY.md)

---

## Project Structure

```
shadowforge/
├── main.py                    # Entry point
├── pyproject.toml             # Project config & build
├── core/                      # Agent engine
│   ├── agent.py               # OODA Loop + kill chain
│   ├── config.py              # Pydantic v2 configuration
│   ├── state.py               # Campaign state machine
│   └── memory.py              # Short/long-term memory
├── models/                    # NVIDIA AI integration
│   ├── nim_client.py          # NIM API client with fallback
│   ├── multimodal.py          # Vision-language model
│   ├── embeddings.py          # Vector embeddings
│   ├── prompts.py             # Prompt engineering
│   └── riva_client.py         # Riva ASR/TTS
├── vision/                    # Visual perception
│   ├── screen.py              # Screen capture
│   ├── ocr.py                 # OCR with PII detection
│   ├── detector.py            # YOLOv8 UI detection
│   └── understanding.py       # Visual analysis
├── control/                   # Human-like interaction
│   ├── mouse.py               # Bezier curve mouse movement
│   ├── keyboard.py            # Human-like typing
│   ├── shell.py               # Stealth shell
│   └── stealth.py             # Anti-forensics
├── planning/                  # Tactical planning
│   ├── orchestrator.py        # Campaign orchestration
│   └── rag.py                 # MITRE ATT&CK / OWASP RAG
├── speech/                    # Voice interface
│   ├── asr.py                 # Automatic speech recognition
│   ├── tts.py                 # Text-to-speech
│   └── voice_interface.py     # Full voice interface
├── hacker_tools/              # Security tools
│   ├── recon/                 # Scanning & OSINT
│   ├── exploit/               # Web & network attacks
│   ├── post_exploitation/     # Privilege escalation & pivot
│   └── reporting/             # Report generation
├── tests/                     # Test suite
├── scripts/                   # Utility scripts
└── config/                    # YAML configuration
```

---

## Configuration

Configuration is loaded in priority order:

1. **CLI arguments** (`python main.py --mode stealth`)
2. **Environment variables** (`.env` file)
3. **YAML config** (`config/default.yaml`)
4. **Defaults** (Pydantic models)

See [.env.example](.env.example) for all available environment variables.

---

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linter
ruff check .

# Run type checker
mypy core/ models/ planning/

# Run tests
python tests/test_imports.py
python tests/test_api_nvidia.py

# Run security scan
bandit -r core/ models/ planning/ -ll --skip B101,B311
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full contribution guidelines.

---

## Security

For security vulnerabilities, please see [SECURITY.md](SECURITY.md) for responsible disclosure.

---

## License

This project is licensed under the MIT License with an **Ethical Use Requirement** — see [LICENSE](LICENSE) for details.

---

## Disclaimer

This software is provided for **authorized security testing, research, and educational purposes only**. Unauthorized use against systems you do not own or have explicit written permission to test is **illegal**. The authors assume no liability for misuse.

> **Ethics first, hack second.**

---

<p align="center">
  <strong>Wellington de Lima Catarina</strong><br>
  <a href="https://linkedin.com/in/wellington-de-lima-catarina">LinkedIn</a> · <a href="mailto:lelolima806@gmail.com">Email</a>
</p>
