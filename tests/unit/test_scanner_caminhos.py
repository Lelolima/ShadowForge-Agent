"""Caminhos críticos do ReconScanner sem rede externa (shell mockado / laboratório em 127.0.0.1)."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import AsyncMock, patch

import pytest

from control.shell import ResultadoComando
from core.config import ShadowForgeConfig
from hacker_tools.recon.scanner import ReconScanner

XML = """<nmaprun><host><status state="up"/><address addr="10.0.0.5" addrtype="ipv4"/>
<ports><port protocol="tcp" portid="22"><state state="open"/><service name="ssh" product="OpenSSH" version="9.6"/></port></ports>
</host></nmaprun>"""


def _ok(stdout: str) -> ResultadoComando:
    res = ResultadoComando(comando="nmap")
    res.returncode, res.stdout = 0, stdout
    return res


@pytest.mark.asyncio
async def test_port_scan_fallback_filtra_flags_e_parseia():
    executar = AsyncMock(return_value=_ok(XML))
    with patch.dict("sys.modules", {"nmap": None}), patch("control.shell.StealthShell.executar", executar):
        hosts = await ReconScanner().port_scan("10.0.0.5", argumentos_extra="-p 22 --interactive -oN /tmp/x")
    comando = executar.await_args.args[0]
    assert "--interactive" not in comando and "-oN" not in comando  # flags fora da whitelist
    assert "-p" in comando
    assert hosts[0].endereco == "10.0.0.5"
    assert hosts[0].portas[0].versao == "OpenSSH 9.6"


@pytest.mark.asyncio
async def test_port_scan_falha_retorna_vazio():
    falha = ResultadoComando(comando="nmap")
    falha.returncode, falha.stderr = 1, "nmap: command not found"
    with patch.dict("sys.modules", {"nmap": None}), \
         patch("control.shell.StealthShell.executar", AsyncMock(return_value=falha)):
        assert await ReconScanner().port_scan("10.0.0.5") == []


@pytest.mark.asyncio
async def test_full_recon_fora_do_escopo_nao_executa():
    scanner = ReconScanner(config=ShadowForgeConfig())
    scanner.port_scan = AsyncMock()
    resultado = await scanner.executar_full_recon("10.0.0.5")
    assert resultado["autorizado"] is False
    scanner.port_scan.assert_not_awaited()


@pytest.mark.asyncio
async def test_full_recon_simulado_respeita_blacklist():
    resultado = await ReconScanner(config=ShadowForgeConfig()).executar_full_recon("127.0.0.1", simulate=True)
    assert resultado["autorizado"] is False


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(b"<div data-reactroot></div>")

    def log_message(self, *_a):
        return


@pytest.fixture
def lab():
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}/"
    servidor.shutdown()
    servidor.server_close()


@pytest.mark.asyncio
async def test_web_fingerprint_loopback_bloqueado_sem_escopo(lab):
    resultado = await ReconScanner(config=ShadowForgeConfig()).web_fingerprint(lab)
    assert "SSRF" in resultado["erro"]


@pytest.mark.asyncio
async def test_web_fingerprint_lab_no_escopo(lab, monkeypatch):
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    cfg = ShadowForgeConfig()
    cfg.etica.whitelist_hosts = ["127.0.0.1"]
    resultado = await ReconScanner(config=cfg).web_fingerprint(lab)
    assert resultado["status_code"] == 200
    assert "React/Next.js" in resultado["tecnologias"]
    cabecalhos = {a["cabecalho"] for a in resultado["analise_seguranca"]}
    assert "Content-Security-Policy" in cabecalhos and "X-Frame-Options" not in cabecalhos


@pytest.mark.asyncio
async def test_metadata_nunca_liberado_mesmo_no_escopo():
    cfg = ShadowForgeConfig()
    cfg.etica.whitelist_hosts = ["169.254.169.254"]
    resultado = await ReconScanner(config=cfg).web_fingerprint("http://169.254.169.254/latest/meta-data/")
    assert "SSRF" in resultado["erro"]
