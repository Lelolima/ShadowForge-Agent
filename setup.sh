#!/usr/bin/env bash
# ============================================================
#  NVIDIA ShadowForge Agent - Script de Setup
#  Detecção automática de GPU NVIDIA + instalação
#  Uso: chmod +x setup.sh && ./setup.sh
# ============================================================

set -euo pipefail

# Cores cyberpunk
RST='\033[0m'
GRN='\033[0;32m'
RED='\033[0;31m'
CYN='\033[0;36m'
YEL='\033[1;33m'
GRN_BOLD='\033[1;32m'
DIM='\033[2m'

# Banner
echo -e "${GRN}"
cat << "BANNER"
  ╔═══════════════════════════════════════════════════════════════╗
  ║                                                               ║
  ║   ███████╗██╗  ██╗ █████╗ ██████╗  ██████╗ ██╗    ██╗        ║
  ║   ██╔════╝██║  ██║██╔══██╗██╔══██╗██╔═══██╗██║    ██║        ║
  ║   ███████╗███████║███████║██║  ██║██║   ██║██║ █╗ ██║        ║
  ║   ╚════██║██╔══██║██╔══██║██║  ██║██║   ██║██║███╗██║        ║
  ║   ███████║██║  ██║██║  ██║██████╔╝╚██████╔╝╚███╔███╔╝        ║
  ║   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝         ║
  ║                                                               ║
  ║   ███████╗███████╗ ██████╗ █████╗ ██████╗ ███████╗            ║
  ║   ██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝            ║
  ║   ███████╗█████╗  ██║     ███████║██████╔╝█████╗              ║
  ║   ╚════██║██╔══╝  ██║     ██╔══██║██╔══██╗██╔══╝              ║
  ║   ███████║██║     ╚██████╗██║  ██║██║  ██║███████╗            ║
  ║   ╚══════╝╚═╝      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝            ║
  ║                                                               ║
  ║   [ SH4D0WF0RG3 Agent v1.0.0 | 1337 Mode ]                   ║
  ║   Autonomous Ethical Hacking AI | NVIDIA Powered              ║
  ║                                                               ║
  ╚═══════════════════════════════════════════════════════════════╝
BANNER
echo -e "${RST}"

log_info()  { echo -e "${GRN}[+]${RST} $1"; }
log_warn()  { echo -e "${YEL}[!]${RST} $1"; }
log_error() { echo -e "${RED}[-]${RST} $1"; }
log_step()  { echo -e "${CYN}[*]${RST} $1"; }
log_1337()  { echo -e "${GRN_BOLD}[>>]${RST} $1"; }

# --- Detecção de GPU NVIDIA ---
detect_gpu() {
    log_step "Detectando GPU NVIDIA..."

    if ! command -v nvidia-smi &>/dev/null; then
        log_error "nvidia-smi não encontrado! GPU NVIDIA não detectada."
        log_warn "O agente funcionará em modo CPU (limitado)."
        log_warn "Para Performance total, instale drivers NVIDIA: https://www.nvidia.com/Download/index.aspx"
        export SHADOWFORGE_GPU_MODE="cpu"
        return 1
    fi

    local gpu_info
    gpu_info=$(nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader 2>/dev/null || echo "ERRO")

    if [[ "$gpu_info" == "ERRO" || -z "$gpu_info" ]]; then
        log_error "Falha ao consultar GPU NVIDIA."
        export SHADOWFORGE_GPU_MODE="cpu"
        return 1
    fi

    echo -e "${GRN_BOLD}"
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║        GPU NVIDIA DETECTADA!             ║"
    echo "  ╠══════════════════════════════════════════╣"
    while IFS=, read -r nome mem driver cc; do
        nome=$(echo "$nome" | xargs)
        mem=$(echo "$mem" | xargs)
        driver=$(echo "$driver" | xargs)
        cc=$(echo "$cc" | xargs)
        printf "  ║  GPU:     %-30s ║\n" "$nome"
        printf "  ║  VRAM:    %-30s ║\n" "$mem"
        printf "  ║  Driver:  %-30s ║\n" "$driver"
        printf "  ║  CC:      %-30s ║\n" "$cc"
    done <<< "$gpu_info"
    echo "  ╚══════════════════════════════════════════╝"
    echo -e "${RST}"

    # Verifica CUDA
    if nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1 | grep -q "^[789]"; then
        log_1337 "Compute Capability 7.x+ detectado - TensorRT FP16/INT8 disponível!"
    fi

    export SHADOWFORGE_GPU_MODE="gpu"
    return 0
}

# --- Verificação de Python ---
check_python() {
    log_step "Verificando Python..."

    if command -v python3.11 &>/dev/null; then
        export PYTHON_CMD="python3.11"
    elif command -v python3 &>/dev/null; then
        local py_ver
        py_ver=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
        if [[ "$(echo "$py_ver" | cut -d. -f1)" -ge 3 && "$(echo "$py_ver" | cut -d. -f2)" -ge 11 ]]; then
            export PYTHON_CMD="python3"
        else
            log_error "Python 3.11+ necessário. Encontrado: $(python3 --version)"
            exit 1
        fi
    else
        log_error "Python 3.11+ não encontrado!"
        log_info "Instale: https://www.python.org/downloads/"
        exit 1
    fi

    log_info "Python: $($PYTHON_CMD --version)"
}

# --- Virtual Environment ---
setup_venv() {
    log_step "Criando ambiente virtual..."

    if [[ ! -d ".venv" ]]; then
        $PYTHON_CMD -m venv .venv
        log_info "Virtual environment criado."
    else
        log_info "Virtual environment já existe."
    fi

    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null
    pip install --upgrade pip setuptools wheel -q
}

# --- Instalação de Dependências ---
install_deps() {
    log_step "Instalando dependências..."

    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt -q 2>/dev/null
        if [[ $? -ne 0 ]]; then
            log_warn "Algumas dependências falharam. Instalando essenciais..."
            pip install pydantic pyyaml python-dotenv aiofiles Pillow \
                opencv-python numpy grpcio pyautogui psutil aiohttp \
                httpx python-nmap sqlalchemy aiosqlite chromadb \
                rich click colorama jinja2 markdown -q
        fi
        log_info "Dependências instaladas."
    fi
}

# --- Configuração ---
setup_config() {
    log_step "Configurando ambiente..."

    mkdir -p logs data/chromadb data/campaigns data/riva

    if [[ ! -f ".env" ]]; then
        cp .env.example .env
        log_info ".env criado a partir do template. EDITE com suas API keys!"
    fi

    if [[ ! -f "config/default.yaml" ]]; then
        log_warn "config/default.yaml não encontrado."
    fi

    log_info "Diretórios de runtime criados."
}

# --- Validação ---
validate_setup() {
    log_step "Validando instalação..."

    local failures=0

    $PYTHON_CMD -c "import pydantic" 2>/dev/null || { log_error "pydantic não disponível"; ((failures++)); }
    $PYTHON_CMD -c "import yaml" 2>/dev/null || { log_error "pyyaml não disponível"; ((failures++)); }
    $PYTHON_CMD -c "import aiohttp" 2>/dev/null || { log_error "aiohttp não disponível"; ((failures++)); }
    $PYTHON_CMD -c "import PIL" 2>/dev/null || { log_error "Pillow não disponível"; ((failures++)); }

    if [[ "$SHADOWFORGE_GPU_MODE" == "gpu" ]]; then
        $PYTHON_CMD -c "import torch; print(f'CUDA disponível: {torch.cuda.is_available()}')" 2>/dev/null || \
            log_warn "PyTorch/CUDA não disponível para verificação."
    fi

    if [[ $failures -gt 0 ]]; then
        log_warn "$failures dependência(s) essenciais faltando."
        return 1
    fi

    return 0
}

# --- Execução Principal ---
main() {
    log_1337 "Iniciando setup do NVIDIA ShadowForge Agent..."
    echo ""

    detect_gpu || true
    echo ""

    check_python
    echo ""

    setup_venv
    echo ""

    install_deps
    echo ""

    setup_config
    echo ""

    if validate_setup; then
        echo ""
        echo -e "${GRN_BOLD}  ╔═══════════════════════════════════════════════╗"
        echo -e "  ║  SH4D0WF0RG3 AGENTE INSTALADO COM SUCESSO!  ║"
        echo -e "  ╚═══════════════════════════════════════════════╝${RST}"
        echo ""
        log_info "Ative o venv:  source .venv/bin/activate"
        log_info "Configure API:  edite .env com suas chaves NVIDIA"
        log_info "Execute:       python -m core.agent --mode stealth"
        log_info "Docker:        docker compose up -d"
        echo ""
        echo -e "${DIM}  >> Lembre-se: ethics first, hack second. <<${RST}"
    else
        log_error "Setup incompleto. Verifique as dependências."
        exit 1
    fi
}

main "$@"
