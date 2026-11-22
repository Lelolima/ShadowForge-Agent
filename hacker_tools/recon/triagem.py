"""
Triagem defensiva de resultados de scanner já existentes (ex.: XML do Nmap).

Não executa nada contra a rede: recebe hosts/portas já coletados, separa o que
está fora do escopo autorizado e classifica exposições por severidade com
recomendações de correção.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass

from core.scope import EscopoAutorizado
from core.state import EstadoAgente, Severidade, TipoVulnerabilidade
from hacker_tools.recon.scanner import ResultadoHost

_ORDEM_SEVERIDADE = {s: i for i, s in enumerate(["critical", "high", "medium", "low", "info"])}


@dataclass
class Achado:
    """Exposição identificada na triagem."""

    host: str
    porta: int
    servico: str
    severidade: Severidade
    tipo: TipoVulnerabilidade
    titulo: str
    descricao: str
    recomendacao: str

    def to_dict(self) -> dict[str, object]:
        dados = asdict(self)
        dados["severidade"] = self.severidade.value
        dados["tipo"] = self.tipo.value
        return dados


@dataclass(frozen=True)
class _RegraPorta:
    portas: frozenset[int]
    severidade: Severidade
    tipo: TipoVulnerabilidade
    titulo: str
    recomendacao: str


REGRAS_PORTA: tuple[_RegraPorta, ...] = (
    _RegraPorta(
        frozenset({23}), Severidade.HIGH, TipoVulnerabilidade.SENSITIVE_DATA,
        "Telnet exposto (credenciais em texto claro)",
        "Desativar Telnet e usar SSH com autenticação por chave.",
    ),
    _RegraPorta(
        frozenset({3306, 5432, 1433, 1521, 27017, 6379, 9200, 11211}), Severidade.HIGH,
        TipoVulnerabilidade.MISCONFIG,
        "Banco de dados/cache acessível pela rede",
        "Restringir a porta ao segmento da aplicação (firewall/bind local) e exigir autenticação.",
    ),
    _RegraPorta(
        frozenset({21}), Severidade.MEDIUM, TipoVulnerabilidade.SENSITIVE_DATA,
        "FTP exposto (sem criptografia)",
        "Substituir por SFTP/FTPS ou restringir o acesso.",
    ),
    _RegraPorta(
        frozenset({445, 139}), Severidade.MEDIUM, TipoVulnerabilidade.MISCONFIG,
        "SMB exposto",
        "Bloquear SMB fora da rede interna e desativar SMBv1.",
    ),
    _RegraPorta(
        frozenset({3389, 5900}), Severidade.MEDIUM, TipoVulnerabilidade.MISCONFIG,
        "Acesso remoto de desktop exposto (RDP/VNC)",
        "Publicar apenas via VPN/bastion com MFA.",
    ),
    _RegraPorta(
        frozenset({80, 8080, 8000}), Severidade.LOW, TipoVulnerabilidade.SENSITIVE_DATA,
        "Serviço HTTP sem TLS",
        "Redirecionar para HTTPS e habilitar HSTS.",
    ),
)

# (serviço, regex de versão, versão mínima recomendada)
_VERSAO = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")
REGRAS_VERSAO: tuple[tuple[str, tuple[int, int, int], str], ...] = (
    ("ssh", (8, 0, 0), "OpenSSH"),
    ("http", (2, 4, 54), "Apache httpd"),
)


def _versao_tupla(texto: str) -> tuple[int, int, int] | None:
    achado = _VERSAO.search(texto or "")
    if not achado:
        return None
    return int(achado.group(1)), int(achado.group(2)), int(achado.group(3) or 0)


@dataclass
class ResultadoTriagem:
    achados: list[Achado]
    fora_do_escopo: list[str]
    hosts_analisados: int

    def ordenados(self) -> list[Achado]:
        return sorted(self.achados, key=lambda a: (_ORDEM_SEVERIDADE[a.severidade.value], a.host, a.porta))

    def contagem(self) -> dict[str, int]:
        contagem = {s.value: 0 for s in Severidade}
        for achado in self.achados:
            contagem[achado.severidade.value] += 1
        return contagem


def triar_hosts(hosts: Iterable[ResultadoHost], escopo: EscopoAutorizado | None = None) -> ResultadoTriagem:
    """Classifica portas abertas dos hosts dentro do escopo."""
    achados: list[Achado] = []
    fora: list[str] = []
    analisados = 0
    for host in hosts:
        if escopo is not None and not escopo.permite(host.endereco):
            fora.append(host.endereco)
            continue
        analisados += 1
        for porta in host.portas_abertas:
            for regra in REGRAS_PORTA:
                if porta.porta in regra.portas:
                    achados.append(Achado(
                        host=host.endereco, porta=porta.porta, servico=porta.servico,
                        severidade=regra.severidade, tipo=regra.tipo, titulo=regra.titulo,
                        descricao=f"{porta.servico or 'serviço'} {porta.versao}".strip()
                        + f" aberto em {host.endereco}:{porta.porta}/{porta.protocolo}",
                        recomendacao=regra.recomendacao,
                    ))
            for servico, minima, produto in REGRAS_VERSAO:
                versao = _versao_tupla(porta.versao)
                produto_presente = produto.split()[0].lower() in porta.versao.lower()
                if porta.servico == servico and produto_presente and versao and versao < minima:
                    achados.append(Achado(
                        host=host.endereco, porta=porta.porta, servico=porta.servico,
                        severidade=Severidade.MEDIUM, tipo=TipoVulnerabilidade.KNOWN_CVE,
                        titulo=f"{produto} desatualizado ({porta.versao})",
                        descricao=f"Versão {porta.versao} abaixo da mínima recomendada "
                        f"{'.'.join(map(str, minima))} em {host.endereco}:{porta.porta}",
                        recomendacao=f"Atualizar {produto} para a versão suportada mais recente.",
                    ))
    return ResultadoTriagem(achados=achados, fora_do_escopo=fora, hosts_analisados=analisados)


_CVSS_POR_SEVERIDADE = {"critical": 9.5, "high": 7.5, "medium": 5.3, "low": 3.1, "info": 0.0}


def registrar_no_estado(achados: Iterable[Achado], estado: EstadoAgente) -> int:
    """Registra achados como vulnerabilidades no estado (para gerar relatório)."""
    total = 0
    for achado in achados:
        estado.registrar_vulnerabilidade(
            tipo=achado.tipo,
            severidade=achado.severidade,
            titulo=achado.titulo,
            descricao=f"{achado.descricao}. Recomendação: {achado.recomendacao}",
            localizacao=f"{achado.host}:{achado.porta}",
            cvss_score=_CVSS_POR_SEVERIDADE[achado.severidade.value],
        )
        total += 1
    return total
