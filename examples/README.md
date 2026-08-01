# Exemplos — Agente ShadowForge

> Demonstrações executáveis do agente de hacking ético em ação. Cada script abaixo é **seguro** (`--simulate`) e roda em alvos simulados.

---

## Começo Rápido

```bash
# Ative seu ambiente virtual
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# Instale as dependências dos exemplos
pip install -r ../requirements.txt

# Execute qualquer demonstração abaixo
python pentest_lab.py
```

---

## Demonstrações

| Script                          | O que mostra                                  | Executar                     |
|---------------------------------|----------------------------------------------|------------------------------|
| `pentest_lab.py`                | Kill-chain completa em um alvo de laboratório (similar ao DVWA) | `python pentest_lab.py` |
| `bug_bounty_simulation.py`      | Fluxo de bug bounty: encontrar PoC, gerar relatório | `python bug_bounty_simulation.py` |
| `voice_campaign.py`             | Campanha sem uso das mãos via NVIDIA Riva ASR/TTS | `python voice_campaign.py` |
| `doom_control.py`               | Automação de mouse/teclado para jogos CTF-like | `python doom_control.py` |

---

### `pentest_lab.py`

Uma campanha completa de hacking ético contra um alvo de laboratório autorizado.

**Recursos:**
- Recon (varredura de portas Nmap, enumeração de serviços)
- Descoberta de vulnerabilidades (SQLi, XSS, CSRF, listagem de diretórios)
- Exploração com geração de PoC (simulada)
- Análise pós-exploração
- Limpeza de OPSEC
- Relatório final com pontuação de risco

```bash
python pentest_lab.py
```

**Pré-visualização da saída:**
```
--- FASE 1: RECONHECIMENTO ---
  [*] Iniciando varredura de portas Nmap...
  [+] Porta 22/tcp - SSH (OpenSSH 8.9)
  [+] Porta 80/tcp - HTTP (Apache 2.4.54)

--- FASE 6: RELATÓRIO FINAL ---
  V-001  CRITICAL  SQL Injection   /wp-login.php  9.8
  V-002  HIGH      XSS Reflected   /search?q=     7.5
```

---

### `bug_bounty_simulation.py`

Pipeline automatizado de bug bounty: escopo, descobrir, explorar, verificar e relatar.

```bash
python bug_bounty_simulation.py
```

---

### `voice_campaign.py`

Campanha controlada por voz usando NVIDIA Riva ASR/TTS.

```bash
python voice_campaign.py
```

---

### `doom_control.py`

Automação de mouse e teclado para jogos/ambientes CTF-like.

```bash
python doom_control.py
```

---

## Pré-requisitos

Todos os exemplos precisam do projeto principal instalado:

```bash
pip install -r ../requirements.txt
```

Extras opcionais por exemplo:

```bash
pip install -r ../requirements-vision.txt   # Para demonstrações visuais
pip install -r ../requirements-speech.txt   # Para campanha de voz
```

---

## Verificar se tudo funciona

```bash
python -c "import sys; print('OK')"
```