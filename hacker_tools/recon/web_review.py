"""
Revisão defensiva de cabeçalhos de resposta HTTP.

Recebe cabeçalhos já obtidos (de uma requisição autorizada ou de dados gravados)
e aponta ausências de cabeçalhos de segurança e vazamento de versão de software.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from core.state import Severidade

_VERSAO_NO_BANNER = re.compile(r"\d+\.\d+")


@dataclass
class AchadoCabecalho:
    severidade: Severidade
    cabecalho: str
    titulo: str
    recomendacao: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severidade": self.severidade.value,
            "cabecalho": self.cabecalho,
            "titulo": self.titulo,
            "recomendacao": self.recomendacao,
        }


# cabeçalho -> (severidade, recomendação, exige HTTPS)
CABECALHOS_RECOMENDADOS: dict[str, tuple[Severidade, str, bool]] = {
    "Content-Security-Policy": (
        Severidade.MEDIUM, "Definir uma CSP restritiva (ex.: default-src 'self').", False,
    ),
    "X-Frame-Options": (
        Severidade.MEDIUM, "Definir DENY ou SAMEORIGIN (ou frame-ancestors na CSP).", False,
    ),
    "X-Content-Type-Options": (Severidade.LOW, "Definir nosniff.", False),
    "Referrer-Policy": (Severidade.LOW, "Definir strict-origin-when-cross-origin.", False),
    "Strict-Transport-Security": (
        Severidade.MEDIUM, "Definir max-age=31536000; includeSubDomains.", True,
    ),
}


def analisar_cabecalhos(cabecalhos: Mapping[str, str], https: bool = False) -> list[AchadoCabecalho]:
    """Retorna os problemas encontrados nos cabeçalhos de uma resposta."""
    normalizados = {k.lower(): v for k, v in cabecalhos.items()}
    achados: list[AchadoCabecalho] = []
    for nome, (severidade, recomendacao, so_https) in CABECALHOS_RECOMENDADOS.items():
        if so_https and not https:
            continue
        if nome.lower() not in normalizados:
            achados.append(AchadoCabecalho(severidade, nome, f"Cabeçalho {nome} ausente", recomendacao))
    for nome in ("Server", "X-Powered-By"):
        valor = normalizados.get(nome.lower(), "")
        if valor and _VERSAO_NO_BANNER.search(valor):
            achados.append(AchadoCabecalho(
                Severidade.LOW, nome, f"{nome} expõe versão de software ({valor})",
                f"Remover ou genericizar o cabeçalho {nome}.",
            ))
    cookie = normalizados.get("set-cookie", "")
    if cookie:
        atributos = cookie.lower()
        faltando = [a for a in ("httponly", "samesite") if a not in atributos]
        if https and "secure" not in atributos:
            faltando.append("secure")
        if faltando:
            achados.append(AchadoCabecalho(
                Severidade.MEDIUM, "Set-Cookie",
                f"Cookie sem atributos: {', '.join(faltando)}",
                "Marcar cookies de sessão com HttpOnly, Secure e SameSite.",
            ))
    return achados
