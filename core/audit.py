"""
Trilha de auditoria da campanha (JSON Lines, encadeada por hash).

Cada evento vira uma linha JSON com ``hash`` = SHA-256 do conteúdo da linha somado ao
hash da linha anterior. Alterar ou remover uma linha quebra a cadeia, o que
:func:`verificar_trilha` detecta. Campos com nome sensível (chave, token, senha...)
são mascarados antes de gravar.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SENSIVEL = re.compile(r"(api[_-]?key|token|secret|senha|password|passwd|credential)", re.IGNORECASE)
_HASH_INICIAL = "0" * 64


def _mascarar(valor: Any) -> Any:
    """Mascara recursivamente valores cujas chaves parecem segredos."""
    if isinstance(valor, dict):
        return {
            k: ("***" if _SENSIVEL.search(str(k)) and v else _mascarar(v)) for k, v in valor.items()
        }
    if isinstance(valor, (list, tuple)):
        return [_mascarar(v) for v in valor]
    if isinstance(valor, (str, int, float, bool)) or valor is None:
        return valor
    return str(valor)


def _hash_linha(conteudo: dict[str, Any], hash_anterior: str) -> str:
    bruto = json.dumps(conteudo, sort_keys=True, ensure_ascii=False) + hash_anterior
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()


class TrilhaAuditoria:
    """Grava eventos de auditoria em ``<diretorio>/<campanha>.jsonl``."""

    def __init__(self, diretorio: str | Path, campanha: str, operador: str | None = None) -> None:
        self.caminho = Path(diretorio) / f"{campanha}.jsonl"
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.campanha = campanha
        try:
            self.operador = operador or getpass.getuser()
        except Exception:  # getuser pode falhar em containers sem passwd
            self.operador = "desconhecido"
        self._lock = threading.Lock()
        self._ultimo_hash = self._carregar_ultimo_hash()

    def _carregar_ultimo_hash(self) -> str:
        if not self.caminho.exists():
            return _HASH_INICIAL
        ultimo = _HASH_INICIAL
        with self.caminho.open(encoding="utf-8") as arq:
            for linha in arq:
                if linha.strip():
                    ultimo = json.loads(linha).get("hash", ultimo)
        return ultimo

    def registrar(self, evento: str, **dados: Any) -> dict[str, Any]:
        """Registra um evento e retorna o registro gravado."""
        with self._lock:
            registro: dict[str, Any] = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "campanha": self.campanha,
                "operador": self.operador,
                "evento": evento,
                **_mascarar(dados),
            }
            registro["hash"] = _hash_linha(registro, self._ultimo_hash)
            with self.caminho.open("a", encoding="utf-8") as arq:
                arq.write(json.dumps(registro, ensure_ascii=False) + "\n")
            self._ultimo_hash = registro["hash"]
            return registro


def verificar_trilha(caminho: str | Path) -> tuple[bool, int]:
    """Verifica a cadeia de hashes.

    Returns:
        (íntegra, número de linhas válidas antes da primeira quebra)
    """
    anterior = _HASH_INICIAL
    validas = 0
    with Path(caminho).open(encoding="utf-8") as arq:
        for linha in arq:
            if not linha.strip():
                continue
            registro = json.loads(linha)
            esperado = registro.pop("hash", "")
            if _hash_linha(registro, anterior) != esperado:
                return False, validas
            anterior = esperado
            validas += 1
    return True, validas
