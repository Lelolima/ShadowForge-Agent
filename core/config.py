"""
============================================================
 NVIDIA ShadowForge Agent - Configuração Central
 Arquivo: core/config.py
============================================================
 Sistema de configuração baseado em Pydantic com suporte
 a YAML, variáveis de ambiente e validação rigorosa.
============================================================
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class ModoOperacao(str, Enum):
    """Modos de operação do agente."""
    STEALTH = "stealth"
    AGRESSIVO = "agressivo"
    RECON_ONLY = "recon_only"
    DEBUG = "debug"


class NivelLog(str, Enum):
    """Níveis de logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ConfigModeloNVIDIA(BaseModel):
    """Configuração de um modelo NVIDIA."""
    modelo: str = Field(..., description="Nome do modelo NVIDIA")
    nim_endpoint: str = Field("https://integrate.api.nvidia.com/v1", description="Endpoint NIM")
    temperatura: float = Field(0.5, ge=0.0, le=2.0, description="Temperatura de sampling")
    max_tokens: int = Field(2048, ge=1, le=32768, description="Máximo de tokens")
    top_p: float = Field(0.95, ge=0.0, le=1.0, description="Top-p sampling")
    stream: bool = Field(True, description="Streaming de respostas")


class ConfigModelos(BaseModel):
    """Configuração de todos os modelos NVIDIA."""
    planejamento: ConfigModeloNVIDIA = Field(default_factory=lambda: ConfigModeloNVIDIA(
        modelo="meta/llama-3.3-70b-instruct", temperatura=0.7, max_tokens=4096, top_p=0.95
    ))
    raciocinio: ConfigModeloNVIDIA = Field(default_factory=lambda: ConfigModeloNVIDIA(
        modelo="meta/llama-3.3-70b-instruct", temperatura=0.4, max_tokens=8192, top_p=0.9
    ))
    visao: ConfigModeloNVIDIA = Field(default_factory=lambda: ConfigModeloNVIDIA(
        modelo="meta/llama-3.2-90b-vision-instruct", temperatura=0.3, max_tokens=2048
    ))
    codigo: ConfigModeloNVIDIA = Field(default_factory=lambda: ConfigModeloNVIDIA(
        modelo="meta/llama-3.1-8b-instruct", temperatura=0.2, max_tokens=4096
    ))
    embeddings: ConfigModeloNVIDIA = Field(default_factory=lambda: ConfigModeloNVIDIA(
        modelo="meta/llama-3.2-11b-vision-instruct", temperatura=0.0, max_tokens=512
    ))


class ConfigRivaASR(BaseModel):
    """Configuração ASR NVIDIA Riva."""
    modelo: str = "nvidia/riva-asr"
    idioma: str = "pt-BR"
    sample_rate: int = Field(16000, ge=8000, le=48000)
    enable_automatic_punctuation: bool = True
    enable_vad: bool = True
    vad_sensibilidade: float = Field(0.5, ge=0.0, le=1.0)
    max_latencia_ms: int = Field(250, ge=50, le=2000)


class ConfigRivaTTS(BaseModel):
    """Configuração TTS NVIDIA Riva."""
    modelo: str = "nvidia/riva-tts"
    idioma: str = "pt-BR"
    voz: str = "default"
    sample_rate: int = Field(22050, ge=8000, le=48000)
    velocidade: float = Field(1.0, ge=0.5, le=3.0)
    tom: float = Field(1.0, ge=0.5, le=2.0)


class ConfigRiva(BaseModel):
    """Configuração NVIDIA Riva."""
    servidor: str = "localhost:50051"
    asr: ConfigRivaASR = Field(default_factory=ConfigRivaASR)
    tts: ConfigRivaTTS = Field(default_factory=ConfigRivaTTS)


class ConfigGPU(BaseModel):
    """Configuração de GPU NVIDIA."""
    dispositivo: int = Field(0, ge=-1, le=7, description="GPU ID (-1=auto)")
    multi_gpu: bool = False
    memoria_max_mb: int = Field(8192, ge=1024, le=65536)
    tensorrt: bool = True
    fp16: bool = True
    int8: bool = False

    @model_validator(mode="after")
    def validar_gpu(self) -> ConfigGPU:
        """Valida configuração de GPU."""
        if self.int8 and not self.fp16:
            self.fp16 = True  # INT8 requer FP16
        return self


class ConfigNVIDIA(BaseModel):
    """Configuração completa da stack NVIDIA."""
    api_key: str = Field("", description="NVIDIA API Key (via env var)")
    base_url: str = "https://integrate.api.nvidia.com/v1"
    org_id: str = ""
    modelos: ConfigModelos = Field(default_factory=ConfigModelos)
    riva: ConfigRiva = Field(default_factory=ConfigRiva)
    gpu: ConfigGPU = Field(default_factory=ConfigGPU)

    @field_validator("api_key", mode="before")
    @classmethod
    def resolver_env(cls, v: str) -> str:
        """Resolve variáveis de ambiente no formato ${VAR}."""
        if v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            return os.environ.get(env_var, v)
        return v


class ConfigEtica(BaseModel):
    """Guardrails éticos - NUNCA desativar em produção."""
    exigir_autorizacao: bool = True
    verificar_escopo: bool = True
    registrar_todas_acoes: bool = True
    recusar_ilegal: bool = True
    modo_simulacao: bool = False
    whitelist_hosts: list[str] = Field(default_factory=list)
    blacklist_hosts: list[str] = Field(
        default_factory=lambda: ["0.0.0.0/0", "224.0.0.0/4", "127.0.0.1"]
    )
    max_severidade_exploracao: str = "high"
    impedir_destruicao: bool = True
    impedir_backdoor: bool = True
    impedir_exfiltracao_real: bool = True

    @field_validator("max_severidade_exploracao")
    @classmethod
    def validar_severidade(cls, v: str) -> str:
        """Valida nivel de severidade permitido."""
        permitidos = {"low", "medium", "high", "critical"}
        if v not in permitidos:
            raise ValueError(f"Severidade deve ser uma de: {permitidos}")
        return v


class ConfigOODA(BaseModel):
    """Configuração do loop OODA."""
    intervalo_observe_ms: int = Field(500, ge=100, le=5000)
    intervalo_orient_ms: int = Field(1000, ge=200, le=10000)
    intervalo_decide_ms: int = Field(800, ge=100, le=5000)
    intervalo_act_ms: int = Field(200, ge=50, le=2000)
    max_iteracoes: int = Field(1000, ge=1, le=100000)
    timeout_campanha_min: int = Field(480, ge=10, le=1440)


class ConfigStealth(BaseModel):
    """Configuração do modo stealth."""
    anti_forensics: bool = True
    proxy_chain: list[str] = Field(default_factory=list)
    user_agent_rotation: bool = True
    user_agents: list[str] = Field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    ])
    mac_spoof: bool = False
    dns_over_https: bool = True
    limpar_historial: bool = True


class ConfigCaptureTela(BaseModel):
    """Configuração de captura de tela."""
    monitor: int = 0
    fps_min: int = Field(1, ge=1, le=60)
    fps_max: int = Field(30, ge=1, le=120)
    formato: str = "PNG"
    qualidade_jpeg: int = Field(85, ge=10, le=100)
    diff_threshold: float = Field(0.05, ge=0.01, le=1.0)
    regiao_interesse: dict | None = None


class ShadowForgeConfig(BaseModel):
    """Configuração principal do agente ShadowForge."""

    # Identidade
    nome: str = "ShadowForge"
    versao: str = "1.0.0"
    codinome: str = "SH4D0WF0RG3"
    modo: ModoOperacao = ModoOperacao.STEALTH
    idioma: str = "pt-BR"
    leetspeak_logs: bool = True
    tema: str = "matrix"
    log_nivel: NivelLog = NivelLog.INFO
    log_arquivo: str = "logs/shadowforge.log"
    log_rotacao_mb: int = 50
    log_retenciao_dias: int = 30

    # Subsistemas
    ooda: ConfigOODA = Field(default_factory=ConfigOODA)
    etica: ConfigEtica = Field(default_factory=ConfigEtica)
    nvidia: ConfigNVIDIA = Field(default_factory=ConfigNVIDIA)
    visao_captura: ConfigCaptureTela = Field(default_factory=ConfigCaptureTela)
    stealth: ConfigStealth = Field(default_factory=ConfigStealth)

    # Alvos
    alvo_inicial: str | None = None
    campanha_id: str | None = None

    # Paths
    raiz_projeto: Path = Field(default_factory=lambda: Path.cwd())
    data_dir: Path = Field(default_factory=lambda: Path.cwd() / "data")
    logs_dir: Path = Field(default_factory=lambda: Path.cwd() / "logs")

    model_config = {"env_prefix": "SHADOWFORGE_", "env_nested_delimiter": "__"}

    @classmethod
    def carregar_de_yaml(cls, caminho: str | Path) -> ShadowForgeConfig:
        """Carrega configuração de arquivo YAML."""
        caminho = Path(caminho)
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {caminho}")

        with open(caminho, encoding="utf-8") as f:
            dados = yaml.safe_load(f)

        # Flatten seções aninhadas do YAML
        agente = dados.get("agente", {})
        nvidia = dados.get("nvidia", {})
        etica = dados.get("etica", dados.get("agente", {}).get("etica", {}))

        config_dict = {
            "nome": agente.get("nome", "ShadowForge"),
            "versao": agente.get("versao", "1.0.0"),
            "codinome": agente.get("codinome", "SH4D0WF0RG3"),
            "modo": agente.get("modo", "stealth"),
            "idioma": agente.get("idioma", "pt-BR"),
            "leetspeak_logs": agente.get("leetspeak_logs", True),
            "tema": agente.get("tema", "matrix"),
            "log_nivel": agente.get("log_nivel", "INFO"),
            "etica": etica,
            "nvidia": nvidia,
        }

        return cls(**config_dict)

    @classmethod
    def carregar_de_env(cls) -> ShadowForgeConfig:
        """Carrega configuração de variáveis de ambiente."""
        api_key = os.environ.get("NVIDIA_API_KEY", "")
        modo = os.environ.get("SHADOWFORGE_MODE", "stealth")

        return cls(
            nvidia=ConfigNVIDIA(api_key=api_key),
            modo=ModoOperacao(modo),
        )

    def verificar_etica(self, acao: str, alvo: str = "") -> tuple[bool, str]:
        """Verifica se uma ação é ética e permitida.

        Returns:
            Tupla (permitido, motivo) indicando se a ação pode prosseguir.
        """
        if not self.etica.exigir_autorizacao:
            return True, "Verificação de autorização desativada (modo desenvolvimento)"

        # Ações de reconnaissance são geralmente seguras
        acoes_seguras = {"scan", "recon", "enumerate", "crawl", "screenshot", "ocr"}
        if any(segura in acao.lower() for segura in acoes_seguras):
            return True, "Ação de reconnaissance permitida"

        # Verifica blacklist
        if alvo:
            for bloqueado in self.etica.blacklist_hosts:
                if alvo == bloqueado or alvo.startswith(bloqueado.split("/")[0]):
                    return False, f"Alvo {alvo} esta na blacklist: {bloqueado}"

        # Verifica whitelist (se definida)
        if self.etica.whitelist_hosts and alvo:
            autorizado = any(alvo.startswith(w) for w in self.etica.whitelist_hosts)
            if not autorizado:
                return False, f"Alvo {alvo} não está na whitelist"

        # Verifica ações destrutivas
        acoes_destrutivas = {"delete", "destroy", "rm", "drop", "wipe", "format"}
        if any(d in acao.lower() for d in acoes_destrutivas) and self.etica.impedir_destruicao:
                return False, "Ação destrutiva bloqueada por policy ética"

        # Verifica backdoor
        acoes_backdoor = {"backdoor", "persist", "implant", "rootkit"}
        if any(b in acao.lower() for b in acoes_backdoor) and self.etica.impedir_backdoor:
                return False, "Instalação de backdoor bloqueada por policy ética"

        # Verifica exfiltração
        acoes_exfiltracao = {"exfiltrate", "download_db", "dump_creds"}
        if any(e in acao.lower() for e in acoes_exfiltracao) and self.etica.impedir_exfiltracao_real:
                return False, "Exfiltração real bloqueada - use modo simulação"

        return True, "Ação permitida pelos guardrails éticos"
