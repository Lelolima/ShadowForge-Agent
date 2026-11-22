"""
Escopo de alvos autorizados.

Regra única usada pela configuração ética, pelo scanner e pelo agente para decidir
se um alvo (IP, rede CIDR ou hostname) está dentro do escopo combinado com o cliente.

Semântica:
- Entrada IP ou CIDR (``10.0.0.0/24``): autoriza qualquer IP ou sub-rede contida nela.
- Entrada hostname (``lab.local``): autoriza o próprio host e subdomínios de um nível
  (``www.lab.local``), mas nunca ``lab.local.evil.com``.
- Entrada ``*.lab.local``: autoriza subdomínios de qualquer profundidade.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Iterable
from dataclasses import dataclass, field

Rede = ipaddress.IPv4Network | ipaddress.IPv6Network


def _como_rede(valor: str) -> Rede | None:
    """Converte ``valor`` em rede IP; ``None`` se não for IP/CIDR."""
    try:
        return ipaddress.ip_network(valor.strip(), strict=False)
    except ValueError:
        return None


def normalizar_alvo(alvo: str) -> str:
    """Remove esquema/porta/caminho de uma URL e normaliza caixa."""
    alvo = alvo.strip().lower()
    if "://" in alvo:
        alvo = alvo.split("://", 1)[1]
    alvo = alvo.split("/", 1)[0] if not _como_rede(alvo) else alvo
    # host:porta (não confundir com IPv6)
    if alvo.count(":") == 1:
        alvo = alvo.split(":", 1)[0]
    return alvo.rstrip(".")


def host_corresponde(host: str, autorizado: str) -> bool:
    """Hostname exato ou subdomínio de um nível (evita ``lab.local.evil.com``)."""
    host = host.lower().rstrip(".")
    autorizado = autorizado.lower().rstrip(".")
    if not host or not autorizado:
        return False
    if autorizado.startswith("*."):
        return host.endswith(autorizado[1:]) and host != autorizado[2:]
    if host == autorizado:
        return True
    if host.endswith("." + autorizado):
        prefixo = host[: -len(autorizado) - 1]
        return bool(prefixo) and "." not in prefixo
    return False


def rede_contem(rede: Rede, alvo: Rede) -> bool:
    """True se ``alvo`` (IP ou rede) está inteiramente dentro de ``rede``."""
    if rede.version != alvo.version:
        return False
    return alvo.subnet_of(rede)  # type: ignore[arg-type]


@dataclass
class EscopoAutorizado:
    """Conjunto de alvos autorizados por escrito para a campanha."""

    entradas: list[str] = field(default_factory=list)

    @classmethod
    def de_lista(cls, valores: Iterable[str]) -> EscopoAutorizado:
        limpos = [v.strip() for v in valores if v and v.strip() and not v.strip().startswith("#")]
        return cls(entradas=limpos)

    @property
    def vazio(self) -> bool:
        return not self.entradas

    def permite(self, alvo: str) -> bool:
        """True se ``alvo`` está dentro de alguma entrada do escopo."""
        if not alvo:
            return False
        alvo_norm = normalizar_alvo(alvo)
        rede_alvo = _como_rede(alvo_norm)
        for entrada in self.entradas:
            rede = _como_rede(entrada)
            if rede_alvo is not None:
                if rede is not None and rede_contem(rede, rede_alvo):
                    return True
            elif rede is None and host_corresponde(alvo_norm, entrada):
                return True
        return False


def alvo_em_lista_bloqueio(alvo: str, bloqueios: Iterable[str]) -> str | None:
    """Retorna a entrada de bloqueio que cobre ``alvo`` (ou ``None``).

    Para IPs/redes, bloqueia se houver qualquer sobreposição com a rede bloqueada.
    Para hostnames, só correspondência exata.
    """
    alvo_norm = normalizar_alvo(alvo)
    rede_alvo = _como_rede(alvo_norm)
    for bloqueio in bloqueios:
        rede_bloq = _como_rede(bloqueio)
        if rede_alvo is not None and rede_bloq is not None:
            if rede_alvo.version == rede_bloq.version and rede_alvo.overlaps(rede_bloq):  # type: ignore[arg-type]
                return bloqueio
        elif rede_alvo is None and alvo_norm == bloqueio.strip().lower():
            return bloqueio
    return None
