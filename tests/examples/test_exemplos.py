"""Executa cada exemplo de examples/ como o usuário faria (subprocesso, dados sintéticos)."""

import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EXEMPLOS = RAIZ / "examples"


def _rodar(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "NO_PROXY": "127.0.0.1,localhost"}
    env.pop("NVIDIA_API_KEY", None)
    return subprocess.run(
        [sys.executable, str(EXEMPLOS / script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        stdin=subprocess.DEVNULL,
        timeout=120,
        check=False,
    )


def test_01_triagem_nmap(tmp_path):
    r = _rodar("01_triagem_nmap/triagem.py", "--saida", str(tmp_path))
    assert r.returncode == 0, r.stderr
    assert "FORA do escopo: 10.10.20.7" in r.stdout
    dados = json.loads((tmp_path / "triagem.json").read_text(encoding="utf-8"))
    assert dados["contagem"] == {"critical": 0, "high": 3, "medium": 4, "low": 1, "info": 0}
    assert all(not a["host"].startswith("10.10.20.") for a in dados["achados"])
    assert list(tmp_path.glob("report_*.html"))


def test_01_arquivo_inexistente(tmp_path):
    r = _rodar("01_triagem_nmap/triagem.py", "--xml", str(tmp_path / "nao.xml"), "--saida", str(tmp_path))
    assert r.returncode == 2


def test_02_relatorio_achados(tmp_path):
    r = _rodar("02_relatorio_achados/gerar_relatorio.py", "--saida", str(tmp_path))
    assert r.returncode == 0, r.stderr
    assert "risco CRÍTICO" in r.stdout
    md = (tmp_path / "report_LAB-2026-01.md").read_text(encoding="utf-8")
    assert "SQL Injection no parâmetro de busca" in md
    relatorio = json.loads((tmp_path / "report_LAB-2026-01.json").read_text(encoding="utf-8"))
    assert relatorio["resumo_executivo"]["total_vulnerabilidades"] == 4


def test_02_entrada_invalida(tmp_path):
    ruim = tmp_path / "ruim.json"
    ruim.write_text(json.dumps({"achados": [{"tipo": "inexistente"}]}), encoding="utf-8")
    r = _rodar("02_relatorio_achados/gerar_relatorio.py", "--achados", str(ruim), "--saida", str(tmp_path))
    assert r.returncode == 2
    assert "Entrada inválida" in r.stderr


def test_03_revisao_config(tmp_path):
    r = _rodar("03_revisao_config/revisar.py", "--saida", str(tmp_path))
    assert r.returncode == 0, r.stderr
    assert "valor-ficticio" not in r.stdout  # nunca imprime o segredo
    achados = json.loads((tmp_path / "revisao_config.json").read_text(encoding="utf-8"))
    chaves = {a["chave"] for a in achados}
    assert {"etica.exigir_autorizacao", "nvidia.api_key", "hacker_ferramentas.verify_ssl"} <= chaves
    r = _rodar("03_revisao_config/revisar.py", "--saida", str(tmp_path), "--falhar-se-grave")
    assert r.returncode == 1


def test_03_config_padrao_sem_achado_grave(tmp_path):
    r = _rodar(
        "03_revisao_config/revisar.py", "--config", str(RAIZ / "config" / "default.yaml"),
        "--saida", str(tmp_path), "--falhar-se-grave",
    )
    assert r.returncode == 0, r.stdout


def test_04_lab_web_local(tmp_path):
    r = _rodar("04_lab_web_local/lab_web.py", "--yes", "--saida", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HTTP 200 em http://127.0.0.1:" in r.stdout
    assert "Cookie sem atributos" in r.stdout
    assert "íntegra=True" in r.stdout
    assert list(tmp_path.glob("report_*.md"))


def test_04_sem_confirmacao_nao_toca_o_alvo(tmp_path):
    r = _rodar("04_lab_web_local/lab_web.py", "--saida", str(tmp_path))
    assert r.returncode == 3
    assert "nada foi enviado ao alvo" in r.stdout
    trilha = next((tmp_path / "audit").glob("*.jsonl")).read_text(encoding="utf-8")
    assert '"confirmado": false' in trilha
    assert "acao_executada" not in trilha
