"""
Revisão de configuração insegura do ShadowForge (YAML).

Aponta guardrails desativados, escopo ausente ou amplo demais, blacklist sem as
redes sensíveis e segredos gravados em texto claro no arquivo. Nunca imprime o
valor de um segredo: só a chave onde ele está.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from core.state import Severidade

_ORDEM = {s.value: i for i, s in enumerate(Severidade)}
_CHAVES_SECRETAS = ("api_key", "token", "secret", "senha", "password")
_REDES_OBRIGATORIAS = ("127.0.0.0/8", "169.254.0.0/16")


@dataclass
class AchadoConfig:
    severidade: Severidade
    chave: str
    mensagem: str
    recomendacao: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severidade": self.severidade.value,
            "chave": self.chave,
            "mensagem": self.mensagem,
            "recomendacao": self.recomendacao,
        }


def _secao_etica(dados: dict[str, Any]) -> dict[str, Any]:
    etica = dados.get("etica")
    if etica is None:
        etica = (dados.get("agente") or {}).get("etica")
    return etica or {}


def _procurar_segredos(no: Any, caminho: str, achados: list[AchadoConfig]) -> None:
    if isinstance(no, dict):
        for chave, valor in no.items():
            atual = f"{caminho}.{chave}" if caminho else str(chave)
            if (
                isinstance(valor, str)
                and valor
                and any(s in str(chave).lower() for s in _CHAVES_SECRETAS)
                and not (valor.startswith("${") and valor.endswith("}"))
                and valor not in {"changeme", "nvapi-xxxxx"}
            ):
                achados.append(AchadoConfig(
                    Severidade.CRITICAL, atual,
                    "Segredo gravado em texto claro no arquivo de configuração",
                    "Use ${VARIAVEL} e defina o valor no ambiente/.env; revogue e rotacione o segredo exposto.",
                ))
            else:
                _procurar_segredos(valor, atual, achados)
    elif isinstance(no, list):
        for indice, item in enumerate(no):
            _procurar_segredos(item, f"{caminho}[{indice}]", achados)


def revisar_config(dados: dict[str, Any]) -> list[AchadoConfig]:
    """Revisa um dicionário de configuração já carregado."""
    achados: list[AchadoConfig] = []
    etica = _secao_etica(dados)

    for chave, msg in (
        ("exigir_autorizacao", "Verificação de autorização desativada"),
        ("verificar_escopo", "Verificação de escopo desativada"),
        ("impedir_destruicao", "Ações destrutivas permitidas"),
        ("impedir_backdoor", "Instalação de backdoor permitida"),
        ("impedir_exfiltracao_real", "Exfiltração real permitida"),
    ):
        if etica.get(chave, True) is False:
            achados.append(AchadoConfig(
                Severidade.CRITICAL, f"etica.{chave}", msg, f"Defina etica.{chave}: true.",
            ))
    if etica.get("registrar_todas_acoes", True) is False:
        achados.append(AchadoConfig(
            Severidade.HIGH, "etica.registrar_todas_acoes", "Registro de ações desativado",
            "Mantenha o registro ativo para preservar a trilha de auditoria.",
        ))

    escopo = etica.get("whitelist_hosts") or []
    if not escopo:
        achados.append(AchadoConfig(
            Severidade.MEDIUM, "etica.whitelist_hosts",
            "Escopo vazio: execução real exigirá --scope a cada campanha",
            "Registre aqui o escopo do contrato (IPs/CIDRs/hosts autorizados por escrito).",
        ))
    for entrada in escopo:
        try:
            rede = ipaddress.ip_network(str(entrada), strict=False)
        except ValueError:
            continue
        if rede.num_addresses > 65536:
            achados.append(AchadoConfig(
                Severidade.HIGH, "etica.whitelist_hosts",
                f"Escopo amplo demais: {entrada} ({rede.num_addresses} endereços)",
                "Restrinja o escopo às redes efetivamente autorizadas.",
            ))

    bloqueios = [str(b) for b in etica.get("blacklist_hosts") or []]
    for obrigatoria in _REDES_OBRIGATORIAS:
        if obrigatoria not in bloqueios:
            achados.append(AchadoConfig(
                Severidade.MEDIUM, "etica.blacklist_hosts",
                f"Blacklist sem {obrigatoria}",
                f"Inclua {obrigatoria} (loopback/metadata de nuvem) na blacklist.",
            ))
    if "0.0.0.0/0" in bloqueios:
        achados.append(AchadoConfig(
            Severidade.HIGH, "etica.blacklist_hosts",
            "0.0.0.0/0 na blacklist bloqueia todo IPv4 (o agente não opera)",
            "Use 0.0.0.0/8 e 255.255.255.255/32 para 'this host' e broadcast.",
        ))

    ferramentas = dados.get("hacker_ferramentas") or {}
    if ferramentas.get("verify_ssl") is False:
        achados.append(AchadoConfig(
            Severidade.MEDIUM, "hacker_ferramentas.verify_ssl",
            "Verificação de certificado TLS desativada",
            "Mantenha verify_ssl: true; use CA própria do laboratório se necessário.",
        ))

    _procurar_segredos(dados, "", achados)
    return sorted(achados, key=lambda a: _ORDEM[a.severidade.value])


def revisar_arquivo(caminho: str | Path) -> list[AchadoConfig]:
    """Carrega o YAML e revisa."""
    with Path(caminho).open(encoding="utf-8") as arq:
        dados = yaml.safe_load(arq) or {}
    if not isinstance(dados, dict):
        raise ValueError(f"Configuração inválida (esperado um mapeamento YAML): {caminho}")
    return revisar_config(dados)
