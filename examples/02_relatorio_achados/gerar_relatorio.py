"""
Exemplo 02 — Relatório de pentest a partir de achados registrados.

Converte um JSON de achados (anotados durante um teste autorizado) em relatório
com resumo executivo, score, recomendações por tipo e anexos em Markdown/JSON/HTML.

    python examples/02_relatorio_achados/gerar_relatorio.py
    python examples/02_relatorio_achados/gerar_relatorio.py --achados meus_achados.json --saida saida/
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))

from core.state import EstadoAgente, Severidade, TipoVulnerabilidade  # noqa: E402
from hacker_tools.reporting.report_generator import ReportGenerator  # noqa: E402


def carregar_achados(caminho: Path) -> dict:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(dados.get("achados"), list):
        raise ValueError("JSON precisa da chave 'achados' com uma lista")
    for i, achado in enumerate(dados["achados"]):
        for campo in ("tipo", "severidade", "titulo", "descricao"):
            if not achado.get(campo):
                raise ValueError(f"achado #{i} sem o campo obrigatório '{campo}'")
        TipoVulnerabilidade(achado["tipo"])  # valida enum (ValueError se inválido)
        Severidade(achado["severidade"])
    return dados


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--achados", type=Path, default=AQUI / "dados" / "achados.json")
    parser.add_argument("--saida", type=Path, default=Path("saida") / "02_relatorio_achados")
    args = parser.parse_args(argv)

    try:
        dados = carregar_achados(args.achados)
    except (OSError, ValueError) as erro:
        print(f"Entrada inválida: {erro}", file=sys.stderr)
        return 2

    estado = EstadoAgente()
    estado.campanha_id = dados.get("campanha", estado.campanha_id)
    estado.alvo_principal = dados.get("alvo")
    for achado in dados["achados"]:
        estado.registrar_vulnerabilidade(
            tipo=TipoVulnerabilidade(achado["tipo"]),
            severidade=Severidade(achado["severidade"]),
            titulo=achado["titulo"],
            descricao=achado["descricao"],
            localizacao=achado.get("localizacao", ""),
            cvss_score=float(achado.get("cvss_score", 0.0)),
            cve_id=achado.get("cve_id"),
        )

    gerador = ReportGenerator()
    relatorio = asyncio.run(gerador.gerar(estado))
    resumo = relatorio["resumo_executivo"]
    print(f"Campanha {estado.campanha_id} | alvo {estado.alvo_principal}")
    print(f"Vulnerabilidades: {resumo['total_vulnerabilidades']} "
          f"(críticas {resumo['criticas']}, altas {resumo['altas']}) | risco {resumo['nivel_risco']} "
          f"| score {relatorio['score_geral']}/10")
    arquivos = asyncio.run(gerador.salvar_em_arquivo(relatorio, str(args.saida), ["md", "json", "html"]))
    for formato, caminho in arquivos.items():
        print(f"Relatório {formato}: {caminho}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
