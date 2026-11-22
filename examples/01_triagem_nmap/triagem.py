"""
Exemplo 01 — Triagem de resultados de scanner já existentes.

Lê um XML do Nmap gravado, descarta hosts fora do escopo autorizado, classifica as
exposições por severidade e gera relatório (Markdown/JSON/HTML). Nada é executado
contra a rede.

    python examples/01_triagem_nmap/triagem.py
    python examples/01_triagem_nmap/triagem.py --xml meu_scan.xml --escopo escopo.txt --saida saida/
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

from core.scope import EscopoAutorizado  # noqa: E402
from core.state import EstadoAgente  # noqa: E402
from hacker_tools.recon.scanner import ReconScanner  # noqa: E402
from hacker_tools.recon.triagem import registrar_no_estado, triar_hosts  # noqa: E402
from hacker_tools.reporting.report_generator import ReportGenerator  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--xml", type=Path, default=AQUI / "dados" / "scan_lab.xml")
    parser.add_argument("--escopo", type=Path, default=AQUI / "dados" / "escopo.txt")
    parser.add_argument("--saida", type=Path, default=Path("saida") / "01_triagem_nmap")
    args = parser.parse_args(argv)

    for arquivo in (args.xml, args.escopo):
        if not arquivo.is_file():
            print(f"Arquivo não encontrado: {arquivo}", file=sys.stderr)
            return 2

    escopo = EscopoAutorizado.de_lista(args.escopo.read_text(encoding="utf-8").splitlines())
    hosts = ReconScanner().parsear_nmap_xml(args.xml.read_text(encoding="utf-8"))
    resultado = triar_hosts(hosts, escopo)

    print(f"Hosts ativos no XML: {len(hosts)} | analisados (no escopo): {resultado.hosts_analisados}")
    if resultado.fora_do_escopo:
        print(f"Ignorados por estarem FORA do escopo: {', '.join(resultado.fora_do_escopo)}")
    print(f"{'SEVERIDADE':<10} {'ALVO':<18} ACHADO")
    for achado in resultado.ordenados():
        alvo = f"{achado.host}:{achado.porta}"
        print(f"{achado.severidade.value.upper():<10} {alvo:<18} {achado.titulo}")
    print("Resumo:", json.dumps(resultado.contagem()))

    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida / "triagem.json").write_text(
        json.dumps(
            {
                "fonte": str(args.xml.name),
                "escopo": escopo.entradas,
                "fora_do_escopo": resultado.fora_do_escopo,
                "contagem": resultado.contagem(),
                "achados": [a.to_dict() for a in resultado.ordenados()],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    estado = EstadoAgente()
    estado.alvo_principal = ", ".join(escopo.entradas)
    registrar_no_estado(resultado.ordenados(), estado)
    gerador = ReportGenerator()
    relatorio = asyncio.run(gerador.gerar(estado))
    relatorio["meta"]["titulo"] = "Triagem de resultados de scanner (dados gravados)"
    arquivos = asyncio.run(gerador.salvar_em_arquivo(relatorio, str(args.saida), ["md", "json", "html"]))
    for formato, caminho in arquivos.items():
        print(f"Relatório {formato}: {caminho}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
