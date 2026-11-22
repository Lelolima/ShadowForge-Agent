"""Testes unitários de triagem, revisão de cabeçalhos e revisão de configuração."""

from core.revisao_config import revisar_config
from core.scope import EscopoAutorizado
from core.state import EstadoAgente, Severidade
from hacker_tools.recon.scanner import ResultadoHost, ResultadoPorta
from hacker_tools.recon.triagem import registrar_no_estado, triar_hosts
from hacker_tools.recon.web_review import analisar_cabecalhos


def _host(ip, *portas):
    host = ResultadoHost(endereco=ip)
    host.portas = [ResultadoPorta(porta=p, protocolo="tcp", estado="open", servico=s, versao=v) for p, s, v in portas]
    return host


def test_triagem_classifica_e_respeita_escopo():
    hosts = [
        _host("10.0.0.1", (23, "telnet", ""), (22, "ssh", "OpenSSH 9.6")),
        _host("10.9.9.9", (3306, "mysql", "")),
    ]
    r = triar_hosts(hosts, EscopoAutorizado.de_lista(["10.0.0.0/24"]))
    assert r.fora_do_escopo == ["10.9.9.9"]
    assert [a.titulo for a in r.achados] == ["Telnet exposto (credenciais em texto claro)"]
    estado = EstadoAgente()
    assert registrar_no_estado(r.achados, estado) == 1
    assert estado.vulnerabilidades[0].severidade == Severidade.HIGH


def test_triagem_versao_so_para_produto_certo():
    r = triar_hosts([_host("10.0.0.1", (443, "https", "nginx 1.24.0"), (22, "ssh", "OpenSSH 7.4"))])
    titulos = [a.titulo for a in r.achados]
    assert "OpenSSH desatualizado (OpenSSH 7.4)" in titulos
    assert not any("Apache" in t for t in titulos)


def test_cabecalhos_seguros_sem_achados():
    seguros = {
        "Content-Security-Policy": "default-src 'self'",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Strict-Transport-Security": "max-age=31536000",
        "Server": "nginx",
        "Set-Cookie": "s=1; Secure; HttpOnly; SameSite=Lax",
    }
    assert analisar_cabecalhos(seguros, https=True) == []


def test_cabecalhos_inseguros():
    achados = analisar_cabecalhos({"Server": "Apache/2.4.41"}, https=True)
    nomes = {a.cabecalho for a in achados}
    assert {"Content-Security-Policy", "Strict-Transport-Security", "Server"} <= nomes


def test_revisao_config_segura_e_insegura():
    segura = {"agente": {"etica": {"whitelist_hosts": ["10.0.0.0/24"],
                                   "blacklist_hosts": ["127.0.0.0/8", "169.254.0.0/16"]}},
              "nvidia": {"api_key": "${NVIDIA_API_KEY}"}}
    assert revisar_config(segura) == []
    insegura = {"etica": {"impedir_destruicao": False, "whitelist_hosts": ["0.0.0.0/0"]},
                "servicos": [{"token": "abc"}]}
    chaves = {a.chave for a in revisar_config(insegura)}
    assert {"etica.impedir_destruicao", "servicos[0].token", "etica.whitelist_hosts"} <= chaves


async def test_relatorio_exporta_formatos_com_escape(tmp_path):
    from core.state import TipoVulnerabilidade
    from hacker_tools.reporting.report_generator import ReportGenerator

    estado = EstadoAgente()
    estado.alvo_principal = "lab.local"
    estado.registrar_vulnerabilidade(
        TipoVulnerabilidade.XSS_REFLECTED, Severidade.HIGH, "<script>XSS</script> na busca", "desc", "https://lab.local/q", cvss_score=7.1
    )
    estado.registrar_vulnerabilidade(TipoVulnerabilidade.MISCONFIG, Severidade.LOW, "Banner", "desc")
    gerador = ReportGenerator()
    relatorio = await gerador.gerar(estado)
    assert relatorio["resumo_executivo"]["nivel_risco"] == "ALTO"
    arquivos = await gerador.salvar_em_arquivo(relatorio, str(tmp_path), ["md", "json", "html"])
    html = (tmp_path / arquivos["html"].split("\\")[-1].split("/")[-1]).read_text(encoding="utf-8")
    assert "<script>XSS</script>" not in html  # título escapado no HTML
    assert set(arquivos) == {"markdown", "json", "html"}


async def test_relatorio_sem_vulnerabilidades_risco_baixo():
    from hacker_tools.reporting.report_generator import ReportGenerator

    relatorio = await ReportGenerator().gerar(EstadoAgente())
    assert relatorio["resumo_executivo"]["nivel_risco"] == "BAIXO"
    assert "não comprova" in relatorio["resumo_executivo"]["conclusao"]
