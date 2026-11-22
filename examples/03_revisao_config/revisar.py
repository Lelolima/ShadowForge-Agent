"""
Exemplo 03 — Revisão de configuração insegura.

Analisa um YAML de configuração do ShadowForge e aponta guardrails desativados,
escopo amplo, blacklist inadequada, TLS sem verificação e segredos em texto claro
(sem imprimir o valor do segredo).

    python examples/03_revisao_config/revisar.py                  # config de exemplo insegura
    python examples/03_revisao_config/revisar.py --config config/default.yaml
    python examples/03_revisao_config/revisar.py --falhar-se-grave  # exit 1 se crítico/alto (uso em CI)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))

from core.revisao_config import revisar_arquivo  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=AQUI / "dados" / "config_insegura.yaml")
    parser.add_argument("--saida", type=Path, default=Path("saida") / "03_revisao_config")
    parser.add_argument("--falhar-se-grave", action="store_true")
    args = parser.parse_args(argv)

    try:
        achados = revisar_arquivo(args.config)
    except (OSError, ValueError) as erro:
        print(f"Não foi possível revisar {args.config}: {erro}", file=sys.stderr)
        return 2

    print(f"Revisão de {args.config.name}: {len(achados)} achado(s)")
    for achado in achados:
        print(f"[{achado.severidade.value.upper():<8}] {achado.chave}: {achado.mensagem}")
        print(f"           -> {achado.recomendacao}")

    args.saida.mkdir(parents=True, exist_ok=True)
    destino = args.saida / "revisao_config.json"
    destino.write_text(
        json.dumps([a.to_dict() for a in achados], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Resultado JSON: {destino}")

    graves = [a for a in achados if a.severidade.value in {"critical", "high"}]
    return 1 if args.falhar_se_grave and graves else 0


if __name__ == "__main__":
    raise SystemExit(main())
