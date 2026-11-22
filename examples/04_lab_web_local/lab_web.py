"""
Exemplo 04 — Reconhecimento web e relatório de um laboratório LOCAL.

O próprio exemplo sobe um servidor HTTP de laboratório em 127.0.0.1 (porta
aleatória) com configuração propositalmente fraca. Em seguida aplica as
salvaguardas do agente antes de qualquer requisição:

1. escopo autorizado explícito (só 127.0.0.1) verificado pelos guardrails;
2. confirmação do operador antes da ação que toca o alvo (``--yes`` ou prompt);
3. trilha de auditoria JSONL encadeada por hash.

Depois faz o fingerprint web, revisa os cabeçalhos de segurança e gera relatório.
Nenhum host além do servidor criado aqui é contatado.

    python examples/04_lab_web_local/lab_web.py --yes
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))

from core.audit import TrilhaAuditoria, verificar_trilha  # noqa: E402
from core.config import ShadowForgeConfig  # noqa: E402
from core.state import EstadoAgente, Severidade, TipoVulnerabilidade  # noqa: E402
from hacker_tools.recon.scanner import ReconScanner  # noqa: E402
from hacker_tools.reporting.report_generator import ReportGenerator  # noqa: E402

LAB_HOST = "127.0.0.1"


class _HandlerLab(BaseHTTPRequestHandler):
    """Aplicação de laboratório com cabeçalhos inseguros de propósito."""

    server_version = "Apache/2.4.41"
    sys_version = "(Ubuntu)"

    def do_GET(self) -> None:  # noqa: N802 - nome exigido por BaseHTTPRequestHandler
        corpo = b"<html><body><h1>Loja Lab</h1><a href='/wp-content/'>blog</a></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("X-Powered-By", "PHP/7.4.3")
        self.send_header("Set-Cookie", "sessao=lab123; Path=/")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *_args: object) -> None:  # silencia o log do servidor
        return


def iniciar_lab() -> ThreadingHTTPServer:
    servidor = ThreadingHTTPServer((LAB_HOST, 0), _HandlerLab)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


def configurar_lab() -> ShadowForgeConfig:
    """Config do laboratório: escopo = só o loopback; loopback sai da blacklist só aqui."""
    cfg = ShadowForgeConfig()
    cfg.etica.whitelist_hosts = [LAB_HOST]
    cfg.etica.blacklist_hosts = [b for b in cfg.etica.blacklist_hosts if b != "127.0.0.0/8"]
    return cfg


def confirmar(descricao: str, automatico: bool) -> bool:
    if automatico:
        return True
    if not sys.stdin.isatty():
        return False
    try:
        resposta = input(f"Confirmar ação intrusiva: {descricao}? [s/N] ")
    except EOFError:  # sem entrada disponível: nega (fail-closed)
        return False
    return resposta.strip().lower() in {"s", "sim"}


_SEVERIDADE = {"medium": Severidade.MEDIUM, "low": Severidade.LOW, "high": Severidade.HIGH}
_CVSS = {"high": 7.5, "medium": 5.3, "low": 3.1}


async def executar(saida: Path, automatico: bool) -> int:
    cfg = configurar_lab()
    estado = EstadoAgente()
    estado.alvo_principal = LAB_HOST
    trilha = TrilhaAuditoria(saida / "audit", estado.campanha_id)
    trilha.registrar("campanha_iniciada", alvo=LAB_HOST, escopo=cfg.etica.whitelist_hosts, simulado=False)

    servidor = iniciar_lab()
    url = f"http://{LAB_HOST}:{servidor.server_address[1]}/"
    try:
        permitido, motivo = cfg.verificar_etica("web_fingerprint", LAB_HOST)
        trilha.registrar("verificacao_etica", acao="web_fingerprint", alvo=url, permitido=permitido, motivo=motivo)
        print(f"Guardrails: {'PERMITIDO' if permitido else 'BLOQUEADO'} ({motivo})")
        if not permitido:
            return 1

        confirmado = confirmar(f"web_fingerprint contra {url}", automatico)
        trilha.registrar("confirmacao", acao="web_fingerprint", alvo=url, confirmado=confirmado)
        if not confirmado:
            print("Ação não confirmada pelo operador: nada foi enviado ao alvo (use --yes).")
            return 3

        resultado = await ReconScanner(config=cfg).web_fingerprint(url)
        if resultado.get("erro"):
            print(f"Falha no fingerprint: {resultado['erro']}", file=sys.stderr)
            trilha.registrar("acao_executada", acao="web_fingerprint", alvo=url, sucesso=False)
            return 1
        trilha.registrar("acao_executada", acao="web_fingerprint", alvo=url, sucesso=True)
    finally:
        servidor.shutdown()
        servidor.server_close()

    print(f"HTTP {resultado['status_code']} em {url}")
    print("Tecnologias:", ", ".join(resultado["tecnologias"]) or "nenhuma")
    for achado in resultado["analise_seguranca"]:
        sev = achado["severidade"]
        print(f"[{sev.upper():<6}] {achado['titulo']} -> {achado['recomendacao']}")
        estado.registrar_vulnerabilidade(
            tipo=TipoVulnerabilidade.MISCONFIG,
            severidade=_SEVERIDADE.get(sev, Severidade.INFO),
            titulo=achado["titulo"],
            descricao=f"{achado['titulo']}. Recomendação: {achado['recomendacao']}",
            localizacao=url,
            cvss_score=_CVSS.get(sev, 0.0),
        )

    gerador = ReportGenerator()
    relatorio = await gerador.gerar(estado)
    relatorio["meta"]["titulo"] = "Revisão web do laboratório local"
    arquivos = await gerador.salvar_em_arquivo(relatorio, str(saida), ["md", "json", "html"])
    trilha.registrar("campanha_encerrada", achados=len(estado.vulnerabilidades))
    for formato, caminho in arquivos.items():
        print(f"Relatório {formato}: {caminho}")
    integra, linhas = verificar_trilha(trilha.caminho)
    print(f"Trilha de auditoria: {trilha.caminho} ({linhas} eventos, íntegra={integra})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--saida", type=Path, default=Path("saida") / "04_lab_web_local")
    parser.add_argument("--yes", action="store_true", help="Confirma a ação contra o laboratório local")
    args = parser.parse_args(argv)
    args.saida.mkdir(parents=True, exist_ok=True)
    return asyncio.run(executar(args.saida, args.yes))


if __name__ == "__main__":
    raise SystemExit(main())
