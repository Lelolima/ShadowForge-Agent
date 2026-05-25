# Examples — ShadowForge Agent

> Runnable demos of the ethicaI hackKI1I agent in action. Every script below is **safe** (`--simulate`) and runs against mock targets.

---

## Quick Start

```bash
# Activate your venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# Install examples deps
pip install -r ../requirements.txt

# Run any demo below
python pentest_lab.py
```

---

## Demos

| Script | What it shows | Run |
|--------|--------------|-----|
| `pentest_lab.py` | Full kill-chain on a lab target (DVWA-like) | `python pentest_lab.py` |
| `bug_bounty_simulation.py` | Bug bounty workflow: find PoC, generate report | `python bug_bounty_simulation.py` |
| `voice_campaign.py` | Hands-free campaign via NVIDIA Riva ASR/TTS | `python voice_campaign.py` |
| `doom_control.py` | Mouse/Kb automation for CTF-like games | `python doom_control.py` |

---

### `pentest_lab.py`

A full ethical-hacking campaign against an authorized lab target.

**Features:**
- Recon (Nmap port scan, service enumeration)
- Vulnerability discovery (SQLi, XSS, CSRF, directory listing)
- Exploitation with PoC generation (simulated)
- Post-exploitation analysis
- OPSEC cleanup
- Final report with risk score

```bash
python pentest_lab.py
```

**Output preview:**
```
--- FASE 1: RECONNAISSANCE ---
  [*] Iniciando port scan Nmap...
  [+] Porta 22/tcp - SSH (OpenSSH 8.9)
  [+] Porta 80/tcp - HTTP (Apache 2.4.54)

--- FASE 6: RELATORIO FINAL ---
  V-001  CRITICAL  SQL Injection   /wp-login.php  9.8
  V-002  HIGH      XSS Reflected   /search?q=     7.5
```

---

### `bug_bounty_simulation.py`

Bug-bounty automated pipeline: scope, discover, exploit, verify, and report.

```bash
python bug_bounty_simulation.py
```

---

### `voice_campaign.py`

Voice-controlled campaign using NVIDIA Riva ASR/TTS.

```bash
python voice_campaign.py
```

---

### `doom_control.py`

Mouse & keyboard automation for gaming / CTF-like environments.

```bash
python doom_control.py
```

---

## Requirements

All examples need the main project installed:

```bash
pip install -r ../requirements.txt
```

Optional extras per example:

```bash
pip install -r ../requirements-vision.txt   # For visual demos
pip install -r ../requirements-speech.txt   # For voice campaign
```

---

## Verify everything works

```bash
python -c "import sys; print('OK')"