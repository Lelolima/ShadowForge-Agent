"""
============================================================
NVIDIA ShadowForge Agent - Estado do Agente
Arquivo: core/state.py
============================================================
Sistema de estado com fases de operação, persistência
em SQLite e serialização/deserialização completa.
============================================================
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("shadowforge.core.state")


class FaseOperacao(str, Enum):
    """Fases de uma campanha de pentest."""
    IDLE = "idle"
    RECON = "reconnaissance"
    SCAN = "scanning"
    ENUM = "enumeration"
    EXPLOIT = "exploitation"
    POST = "post_exploitation"
    REPORT = "reporting"
    COMPLETED = "completed"
    ABORTED = "aborted"

    @property
    def proxima(self) -> FaseOperacao:
        """Retorna a próxima fase na kill chain."""
        sequencia = [
            FaseOperacao.IDLE,
            FaseOperacao.RECON,
            FaseOperacao.SCAN,
            FaseOperacao.ENUM,
            FaseOperacao.EXPLOIT,
            FaseOperacao.POST,
            FaseOperacao.REPORT,
            FaseOperacao.COMPLETED,
        ]
        try:
            idx = sequencia.index(self)
            return sequencia[min(idx + 1, len(sequencia) - 1)]
        except ValueError:
            return FaseOperacao.IDLE

    @property
    def emoji(self) -> str:
        """Emoji visual da fase."""
        mapa = {
            "idle": "⏸️",
            "reconnaissance": "\U0001f50d",
            "scanning": "\U0001f4e1",
            "enumeration": "\U0001f4cb",
            "exploitation": "⚡",
            "post_exploitation": "\U0001f513",
            "reporting": "\U0001f4ca",
            "completed": "✅",
            "aborted": "\U0001f6d1",
        }
        return mapa.get(self.value, "❓")


class TipoVulnerabilidade(str, Enum):
    """Tipos de vulnerabilidade detectáveis."""
    SQL_INJECTION = "sql_injection"
    XSS_REFLECTED = "xss_reflected"
    XSS_STORED = "xss_stored"
    CSRF = "csrf"
    SSRF = "ssrf"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    LFI = "local_file_inclusion"
    RFI = "remote_file_inclusion"
    IDOR = "idor"
    BROKEN_AUTH = "broken_authentication"
    SENSITIVE_DATA = "sensitive_data_exposure"
    MISCONFIG = "security_misconfiguration"
    KNOWN_CVE = "known_cve"
    PRIV_ESC = "privilege_escalation"
    INFO_DISC = "information_disclosure"
    OUTRO = "outro"


class Severidade(str, Enum):
    """Níveis de severidade."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @property
    def cvss_range(self) -> tuple[float, float]:
        """Range CVSS correspondente."""
        ranges = {
            "critical": (9.0, 10.0),
            "high": (7.0, 8.9),
            "medium": (4.0, 6.9),
            "low": (0.1, 3.9),
            "info": (0.0, 0.0),
        }
        return ranges[self.value]


@dataclass
class VulnerabilidadeDescoberta:
    """Registro de uma vulnerabilidade descoberta."""
    id: str = ""
    tipo: TipoVulnerabilidade = TipoVulnerabilidade.OUTRO
    severidade: Severidade = Severidade.INFO
    titulo: str = ""
    descricao: str = ""
    localizacao: str = ""
    prova_conceito: str = ""
    cvss_score: float = 0.0
    cve_id: str | None = None
    remediacao: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    explorada: bool = False  # Marca se PoC foi validado

    def to_dict(self) -> dict[str, Any]:
        """Serializa para dicionário."""
        d = asdict(self)
        d["tipo"] = self.tipo.value
        d["severidade"] = self.severidade.value
        return d

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> VulnerabilidadeDescoberta:
        """Desserializa de dicionário."""
        dados = dados.copy()
        dados["tipo"] = TipoVulnerabilidade(dados.get("tipo", "outro"))
        dados["severidade"] = Severidade(dados.get("severidade", "info"))
        return cls(**dados)

    @classmethod
    def builder(cls) -> 'VulnerabilidadeDescobertaBuilder':
        """Cria um builder para construir instâncias de VulnerabilidadeDescoberta de forma fluente."""
        return VulnerabilidadeDescobertaBuilder()


@dataclass
class VulnerabilidadeDescobertaBuilder:
    """Builder para criar instâncias de VulnerabilidadeDescoberta de forma fluente e legível."""
    id: str = ""
    tipo: TipoVulnerabilidade = TipoVulnerabilidade.OUTRO
    severidade: Severidade = Severidade.INFO
    titulo: str = ""
    descricao: str = ""
    localizacao: str = ""
    prova_conceito: str = ""
    cvss_score: float = 0.0
    cve_id: str | None = None
    remediacao: str = ""
    timestamp: str = None
    explorada: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def com_id(self, vuln_id: str) -> 'VulnerabilidadeDescobertaBuilder':
        """Define o ID da vulnerabilidade."""
        self.id = vuln_id
        return self

    def com_tipo(self, tipo: TipoVulnerabilidade) -> 'VulnerabilidadeDescobertaBuilder':
        """Define o tipo da vulnerabilidade."""
        self.tipo = tipo
        return self

    def com_severidade(self, severidade: Severidade) -> 'VulnerabilidadeDescobertaBuilder':
        """Define a severidade da vulnerabilidade."""
        self.severidade = severidade
        return self

    def com_titulo(self, titulo: str) -> 'VulnerabilidadeDescobertaBuilder':
        """Define o título da vulnerabilidade."""
        self.titulo = titulo
        return self

    def com_descricao(self, descricao: str) -> 'VulnerabilidadeDescobertaBuilder':
        """Define a descrição da vulnerabilidade."""
        self.descricao = descricao
        return self

    def com_localizacao(self, localizacao: str) -> 'VulnerabilidadeDescobertaBuilder':
        """Define a localização da vulnerabilidade."""
        self.localizacao = localizacao
        return self

    def com_prova_conceito(self, poc: str) -> 'VulnerabilidadeDescobertaBuilder':
        """Define a prova de conceito da vulnerabilidade."""
        self.prova_conceito = poc
        return self

    def com_cvss_score(self, score: float) -> 'VulnerabilidadeDescobertaBuilder':
        """Define o score CVSS da vulnerabilidade."""
        self.cvss_score = score
        return self

    def com_cve_id(self, cve_id: str) -> 'VulnerabilidadeDescobertaBuilder':
        """Define o ID CVE da vulnerabilidade."""
        self.cve_id = cve_id
        return self

    def com_remediacao(self, remediacao: str) -> 'VulnerabilidadeDescobertaBuilder':
        """Define a remediação da vulnerabilidade."""
        self.remediacao = remediacao
        return self

    def com_timestamp(self, timestamp: str) -> 'VulnerabilidadeDescobertaBuilder':
        """Define o timestamp da vulnerabilidade."""
        self.timestamp = timestamp
        return self

    def com_explorada(self, explorada: bool = True) -> 'VulnerabilidadeDescobertaBuilder':
        """Marca a vulnerabilidade como explorada."""
        self.explorada = explorada
        return self

    def build(self) -> VulnerabilidadeDescoberta:
        """Constrói e retorna a instância de VulnerabilidadeDescoberta."""
        return VulnerabilidadeDescoberta(
            id=self.id,
            tipo=self.tipo,
            severidade=self.severidade,
            titulo=self.titulo,
            descricao=self.descricao,
            localizacao=self.localizacao,
            prova_conceito=self.prova_conceito,
            cvss_score=self.cvss_score,
            cve_id=self.cve_id,
            remediacao=self.remediacao,
            timestamp=self.timestamp,
            explorada=self.explorada
        )


@dataclass
class HostAlvo:
    """Informações sobre um host alvo."""
    endereco: str = ""
    hostname: str = ""
    portas_abertas: list[int] = field(default_factory=list)
    servicos: dict[int, str] = field(default_factory=dict)
    os_detectado: str = ""
    vulnerabilidades: list[str] = field(default_factory=list)  # IDs de vulnerabilidades
    autorizado: bool = False
    timestamp_scan: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> HostAlvo:
        return cls(**dados)

    @classmethod
    def builder(cls) -> 'HostAlvoBuilder':
        """Cria um builder para construir instâncias de HostAlvo de forma fluente."""
        return HostAlvoBuilder()


@dataclass
class HostAlvoBuilder:
    """Builder para criar instâncias de HostAlvo de forma fluente e legível."""
    endereco: str = ""
    hostname: str = ""
    portas_abertas: list[str] = None  # Aceita strings para facilitar o uso, converte internamente
    servicos: dict[int, str] = None
    os_detectado: str = ""
    vulnerabilidades: list[str] = None
    autorizado: bool = False
    timestamp_scan: str = None

    def __post_init__(self):
        if self.portas_abertas is None:
            self.portas_abertas = []
        if self.servicos is None:
            self.servicos = {}
        if self.vulnerabilidades is None:
            self.vulnerabilidades = []
        if self.timestamp_scan is None:
            self.timestamp_scan = datetime.now().isoformat()

    def com_endereco(self, endereco: str) -> 'HostAlvoBuilder':
        """Define o endereço IP do host."""
        self.endereco = endereco
        return self

    def com_hostname(self, hostname: str) -> 'HostAlvoBuilder':
        """Define o hostname do host."""
        self.hostname = hostname
        return self

    def com_portas_abertas(self, portas: list[int]) -> 'HostAlvoBuilder':
        """Define as portas abertas do host."""
        self.portas_abertas = portas
        return self

    def com_servico(self, porta: int, servico: str) -> 'HostAlvoBuilder':
        """Adiciona um serviço específico em uma porta."""
        if self.servicos is None:
            self.servicos = {}
        self.servicos[porta] = servico
        return self

    def com_servicos(self, servicos: dict[int, str]) -> 'HostAlvoBuilder':
        """Define todos os serviços do host."""
        self.servicos = servicos
        return self

    def com_os_detectado(self, os_detectado: str) -> 'HostAlvoBuilder':
        """Define o sistema operacional detectado."""
        self.os_detectado = os_detectado
        return self

    def com_vulnerabilidade(self, vuln_id: str) -> 'HostAlvoBuilder':
        """Adiciona uma vulnerabilidade ao host."""
        if self.vulnerabilidades is None:
            self.vulnerabilidades = []
        self.vulnerabilidades.append(vuln_id)
        return self

    def com_vulnerabilidades(self, vuln_ids: list[str]) -> 'HostAlvoBuilder':
        """Define todas as vulnerabilidades do host."""
        self.vulnerabilidades = vuln_ids
        return self

    def com_autorizado(self, autorizado: bool = True) -> 'HostAlvoBuilder':
        """Define se o host está autorizado para teste."""
        self.autorizado = autorizado
        return self

    def com_timestamp(self, timestamp: str) -> 'HostAlvoBuilder':
        """Define o timestamp do scan."""
        self.timestamp_scan = timestamp
        return self

    def build(self) -> HostAlvo:
        """Constrói e retorna a instância de HostAlvo."""
        # Converte portas_abertas de string para int se necessário
        portas_abertas_int = []
        if self.portas_abertas:
            for porta in self.portas_abertas:
                if isinstance(porta, str):
                    try:
                        portas_abertas_int.append(int(porta))
                    except ValueError:
                        pass  # Ignora portas inválidas
                else:
                    portas_abertas_int.append(porta)

        return HostAlvo(
            endereco=self.endereco,
            hostname=self.hostname,
            portas_abertas=portas_abertas_int,
            servicos=self.servicos or {},
            os_detectado=self.os_detectado,
            vulnerabilidades=self.vulnerabilidades or [],
            autorizado=self.autorizado,
            timestamp_scan=self.timestamp_scan or datetime.now().isoformat()
        )


@dataclass
class AcaoRegistrada:
    """Registro de uma ação executada pelo agente (audit trail)."""
    id: str = ""
    fase: str = ""
    tipo: str = ""
    descricao: str = ""
    alvo: str = ""
    comando: str = ""
    resultado: str = ""
    sucesso: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    autorizada: bool = True
    motivo_etico: str = ""


class EstadoAgente:
    """Estado completo do agente durante uma campanha.

    Mantém registro de todas as informações da campanha atual,
    incluindo fases, alvos, vulnerabilidades e ações executadas.
    Persiste em SQLite para recuperação em caso de falha.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.campanha_id: str = f"SF-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.fase_atual: FaseOperacao = FaseOperacao.IDLE
        self.fase_anterior: FaseOperacao | None = None
        self.alvos: list[HostAlvo] = []
        self.vulnerabilidades: list[VulnerabilidadeDescoberta] = []
        self.acoes: list[AcaoRegistrada] = []
        self.alvo_principal: str | None = None
        self.inicio: datetime = datetime.now()
        self.ultima_atualizacao: datetime = datetime.now()
        self.metadata: dict[str, Any] = {}
        self.vuln_counter: int = 0
        self.acao_counter: int = 0
        self._db_path = db_path

        if db_path:
            self._init_db(db_path)

    def _init_db(self, db_path: str | Path) -> None:
        """Inicializa banco SQLite para persistência."""
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campanhas (
                    id TEXT PRIMARY KEY,
                    fase_atual TEXT,
                    alvo_principal TEXT,
                    inicio TEXT,
                    ultima_atualizacao TEXT,
                    metadata TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vulnerabilidades (
                    id TEXT PRIMARY KEY,
                    campanha_id TEXT,
                    tipo TEXT,
                    severidade TEXT,
                    titulo TEXT,
                    descricao TEXT,
                    localizacao TEXT,
                    prova_conceito TEXT,
                    cvss_score REAL,
                    cve_id TEXT,
                    explorada INTEGER,
                    timestamp TEXT,
                    FOREIGN KEY (campanha_id) REFERENCES campanhas(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS acoes (
                    id TEXT PRIMARY KEY,
                    campanha_id TEXT,
                    fase TEXT,
                    tipo TEXT,
                    descricao TEXT,
                    alvo TEXT,
                    comando TEXT,
                    resultado TEXT,
                    sucesso INTEGER,
                    timestamp TEXT,
                    autorizada INTEGER,
                    motivo_etico TEXT,
                    FOREIGN KEY (campanha_id) REFERENCES campanhas(id)
                )
            """)

            conn.commit()

    def registrar_vulnerabilidade(
        self,
        tipo: TipoVulnerabilidade,
        severidade: Severidade,
        titulo: str,
        descricao: str,
        localizacao: str = "",
        prova_conceito: str = "",
        cvss_score: float = 0.0,
        cve_id: str | None = None,
    ) -> VulnerabilidadeDescoberta:
        """Registra uma nova vulnerabilidade descoberta."""
        self.vuln_counter += 1
        vuln_id = f"V-{self.campanha_id}-{self.vuln_counter:03d}"

        vuln = (
            VulnerabilidadeDescoberta.builder()
            .com_id(vuln_id)
            .com_tipo(tipo)
            .com_severidade(severidade)
            .com_titulo(titulo)
            .com_descricao(descricao)
            .com_localizacao(localizacao)
            .com_prova_conceito(prova_conceito)
            .com_cvss_score(cvss_score)
            .com_cve_id(cve_id)
            .build()
        )

        self.vulnerabilidades.append(vuln)
        self.ultima_atualizacao = datetime.now()

        # Persiste no SQLite
        if self._db_path:
            self._salvar_vulnerabilidade_db(vuln)

        return vuln

    def registrar_acao(
        self,
        fase: str,
        tipo: str,
        descricao: str,
        alvo: str = "",
        comando: str = "",
        resultado: str = "",
        sucesso: bool = False,
        autorizada: bool = True,
        motivo_etico: str = "",
    ) -> AcaoRegistrada:
        """Registra uma ação executada (audit trail)."""
        self.acao_counter += 1
        acao_id = f"A-{self.campanha_id}-{self.acao_counter:04d}"

        acao = AcaoRegistrada(
            id=acao_id,
            fase=fase,
            tipo=tipo,
            descricao=descricao,
            alvo=alvo,
            comando=comando,
            resultado=resultado,
            sucesso=sucesso,
            autorizada=autorizada,
            motivo_etico=motivo_etico,
        )

        self.acoes.append(acao)
        self.ultima_atualizacao = datetime.now()

        if self._db_path:
            self._salvar_acao_db(acao)

        return acao

    def avancar_fase(self) -> FaseOperacao:
        """Avança para a próxima fase da kill chain."""
        self.fase_anterior = self.fase_atual
        self.fase_atual = self.fase_atual.proxima
        self.ultima_atualizacao = datetime.now()

        if self._db_path:
            self._atualizar_fase_db()

        return self.fase_atual

    def adicionar_alvo(self, host: HostAlvo) -> None:
        """Adiciona um host alvo à campanha."""
        self.alvos.append(host)
        self.ultima_atualizacao = datetime.now()

    def resumo(self) -> dict[str, Any]:
        """Gera resumo da campanha atual."""
        sev_count: dict[str, int] = {}
        for v in self.vulnerabilidades:
            sev_count[v.severidade.value] = sev_count.get(v.severidade.value, 0) + 1

        return {
            "campanha_id": self.campanha_id,
            "fase_atual": self.fase_atual.value,
            "alvo_principal": self.alvo_principal,
            "total_alvos": len(self.alvos),
            "total_vulnerabilidades": len(self.vulnerabilidades),
            "total_acoes": len(self.acoes),
            "severidade_dist": sev_count,
            "inicio": self.inicio.isoformat(),
            "duracao_min": (datetime.now() - self.inicio).total_seconds() / 60,
            "ultima_atualizacao": self.ultima_atualizacao.isoformat(),
        }

    def to_dict(self) -> dict[str, Any]:
        """Serializa estado completo."""
        return {
            "campanha_id": self.campanha_id,
            "fase_atual": self.fase_atual.value,
            "fase_anterior": self.fase_anterior.value if self.fase_anterior else None,
            "alvos": [a.to_dict() for a in self.alvos],
            "vulnerabilidades": [v.to_dict() for v in self.vulnerabilidades],
            "alvo_principal": self.alvo_principal,
            "inicio": self.inicio.isoformat(),
            "metadata": self.metadata,
        }

    # --- Métodos privados de persistência SQLite ---

    def _salvar_vulnerabilidade_db(self, vuln: VulnerabilidadeDescoberta) -> None:
        """Persiste vulnerabilidade no SQLite.

        H-01 FIX: Usa `with` para garantir que a conexão seja fechada mesmo em caso de exceção.
        H-02 FIX: Registra erro em logger em vez de engolir silenciosamente.
        """
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO vulnerabilidades
                    (id, campanha_id, tipo, severidade, titulo, descricao,
                    localizacao, prova_conceito, cvss_score, cve_id, explorada, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (vuln.id, self.campanha_id, vuln.tipo.value, vuln.severidade.value,
                    vuln.titulo, vuln.descricao, vuln.localizacao, vuln.prova_conceito,
                    vuln.cvss_score, vuln.cve_id, int(vuln.explorada), vuln.timestamp),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error("Falha ao persistir vulnerabilidade %s no SQLite: %s", vuln.id, e)

    def _salvar_acao_db(self, acao: AcaoRegistrada) -> None:
        """Persiste ação no SQLite.

        H-01 FIX: Usa `with` para garantir que a conexão seja fechada mesmo em caso de exceção.
        H-02 FIX: Registra erro em logger em vez de engolir silenciosamente.
        """
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO acoes
                    (id, campanha_id, fase, tipo, descricao, alvo,
                    comando, resultado, sucesso, timestamp, autorizada, motivo_etico)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (acao.id, self.campanha_id, acao.fase, acao.tipo, acao.descricao,
                    acao.alvo, acao.comando, acao.resultado, int(acao.sucesso),
                    acao.timestamp, int(acao.autorizada), acao.motivo_etico),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error("Falha ao persistir ação %s no SQLite: %s", acao.id, e)

    def _atualizar_fase_db(self) -> None:
        """Atualiza fase no SQLite.

        H-02 FIX: Registra erro em logger em vez de engolir silenciosamente.
        """
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE campanhas SET fase_atual=?, ultima_atualizacao=? WHERE id=?",
                    (self.fase_atual.value, datetime.now().isoformat(), self.campanha_id),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error("Falha ao atualizar fase no SQLite: %s", e)
