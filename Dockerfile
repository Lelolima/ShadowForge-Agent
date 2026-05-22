# ============================================================
#  NVIDIA ShadowForge Agent - Dockerfile
#  Base: NVIDIA CUDA 12.3 | Python 3.11
#  Otimizado para GPU NVIDIA com TensorRT
# ============================================================

FROM nvidia/cuda:12.3.1-runtime-ubuntu22.04 AS base

# Metadados cyberpunk
LABEL maintainer="ShadowForge Team"
LABEL description="NVIDIA ShadowForge Agent - Autonomous Ethical Hacking AI"
LABEL version="1.0.0"
LABEL codename="SH4D0WF0RG3"

# Evita prompts interativos
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxdamage1 \
    libxtst6 \
    libxrandr2 \
    libxfixes3 \
    libxkbcommon0 \
    libdbus-1-3 \
    libgomp1 \
    libportaudio2 \
    portaudio19-dev \
    libasound2 \
    libpulse0 \
    libopus0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    nmap \
    nikto \
    sqlmap \
    hydra \
    tcpdump \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root para OPSEC
RUN groupadd -r shadowforge && \
    useradd -r -g shadowforge -m -s /bin/bash shadowforge && \
    mkdir -p /opt/shadowforge && \
    chown -R shadowforge:shadowforge /opt/shadowforge

WORKDIR /opt/shadowforge

# Python virtual environment
RUN python3.11 -m venv /opt/shadowforge/.venv
ENV PATH="/opt/shadowforge/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/shadowforge/.venv"

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copia requirements primeiro (cache de camadas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || \
    pip install --no-cache-dir \
    pydantic pydantic-settings pyyaml python-dotenv \
    aiofiles tenacity Pillow opencv-python numpy \
    grpcio pyaudio sounddevice pyautogui pynput \
    psutil aiohttp httpx python-nmap \
    jinja2 markdown rich click colorama \
    sqlalchemy aiosqlite chromadb \
    requests scapy paramiko langchain

# Copia código fonte
COPY --chown=shadowforge:shadowforge . .

# Cria diretórios de runtime
RUN mkdir -p logs data/chromadb data/campaigns config && \
    chown -R shadowforge:shadowforge logs data

# ------- Estágio de Produção -------
FROM base AS production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python3.11 -c "import core; print('SH4D0WF0RG3 OK')" || exit 1

# Variáveis de runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,video
ENV SHADOWFORGE_CONFIG=/opt/shadowforge/config/default.yaml
ENV SHADOWFORGE_LOG_DIR=/opt/shadowforge/logs
ENV SHADOWFORGE_DATA_DIR=/opt/shadowforge/data

# Portas: 8443 (API), 50051 (Riva gRPC), 55553 (Metasploit RPC)
EXPOSE 8443 50051 55553

# Volume para persistência
VOLUME ["/opt/shadowforge/data", "/opt/shadowforge/logs", "/opt/shadowforge/config"]

# Switch para usuário não-root
USER shadowforge

# Entrypoint
ENTRYPOINT ["python3.11", "-m", "core.agent"]
CMD ["--config", "/opt/shadowforge/config/default.yaml", "--mode", "stealth"]

# ============================================================
#  BUILD:  docker build -t shadowforge:latest .
#  RUN:    docker run --gpus all -e NVIDIA_API_KEY=xxx shadowforge
#  BASH:   docker run --gpus all -it shadowforge /bin/bash
# ============================================================
