"""Testes do escopo de alvos autorizados e da autorização do scanner."""

import pytest

from core.config import ShadowForgeConfig
from core.scope import EscopoAutorizado, alvo_em_lista_bloqueio, normalizar_alvo
from hacker_tools.recon.scanner import ReconScanner


@pytest.mark.parametrize(
    ("alvo", "esperado"),
    [
        ("10.0.0.5", True),
        ("10.0.0.0/25", True),
        ("10.0.1.5", False),
        ("10.0.0.0/16", False),  # rede maior que o escopo
        ("lab.local", True),
        ("www.lab.local", True),
        ("a.b.lab.local", False),
        ("lab.local.evil.com", False),
        ("http://www.lab.local:8080/login", True),
        ("x.corp.test", True),
        ("deep.x.corp.test", True),
        ("corp.test", False),
        ("", False),
    ],
)
def test_escopo_permite(alvo, esperado):
    escopo = EscopoAutorizado.de_lista(["10.0.0.0/24", "lab.local", "*.corp.test", "# comentario"])
    assert escopo.permite(alvo) is esperado


def test_normalizar_alvo():
    assert normalizar_alvo("HTTPS://Lab.Local:443/x") == "lab.local"
    assert normalizar_alvo("10.0.0.0/24") == "10.0.0.0/24"


def test_lista_bloqueio_sobreposicao():
    assert alvo_em_lista_bloqueio("127.0.0.1", ["127.0.0.0/8"]) == "127.0.0.0/8"
    assert alvo_em_lista_bloqueio("0.0.0.0/0", ["127.0.0.0/8"]) == "127.0.0.0/8"
    assert alvo_em_lista_bloqueio("10.0.0.1", ["127.0.0.0/8"]) is None
    assert alvo_em_lista_bloqueio("localhost", ["localhost"]) == "localhost"


def test_scanner_autoriza_pelo_escopo_da_config():
    cfg = ShadowForgeConfig()
    scanner = ReconScanner(config=cfg)
    ok, _ = scanner.verificar_autorizacao("10.0.0.5")
    assert ok is False  # sem escopo
    cfg.etica.whitelist_hosts = ["10.0.0.0/24"]
    ok, motivo = scanner.verificar_autorizacao("10.0.0.5")
    assert ok is True, motivo
    ok, _ = scanner.verificar_autorizacao("127.0.0.1")
    assert ok is False  # blacklist prevalece


def test_scanner_autorizar_explicito():
    scanner = ReconScanner()
    scanner.autorizar("lab.local")
    assert scanner.verificar_autorizacao("www.lab.local")[0] is True
    assert scanner.verificar_autorizacao("lab.local.evil.com")[0] is False


NMAP_XML = """<?xml version="1.0"?>
<nmaprun>
  <host><status state="up"/><address addr="10.0.0.5" addrtype="ipv4"/>
    <hostnames><hostname name="web.lab.local"/></hostnames>
    <ports>
      <port protocol="tcp" portid="22"><state state="open"/><service name="ssh" version="8.9"/></port>
      <port protocol="tcp" portid="80"><state state="open"/><service name="http"/></port>
      <port protocol="tcp" portid="81"><state state="closed"/></port>
    </ports>
  </host>
  <host><status state="down"/><address addr="10.0.0.6" addrtype="ipv4"/></host>
</nmaprun>"""


def test_parsear_nmap_xml_le_hosts_ativos():
    """Antes, host_elem.get('status') era tratado como atributo e todo host era descartado."""
    hosts = ReconScanner()._parsear_nmap_xml(NMAP_XML)
    assert len(hosts) == 1
    host = hosts[0]
    assert host.endereco == "10.0.0.5"
    assert host.hostname == "web.lab.local"
    assert [p.porta for p in host.portas_abertas] == [22, 80]
