"""Testes da trilha de auditoria encadeada por hash."""

import json

from core.audit import TrilhaAuditoria, verificar_trilha


def test_registra_e_verifica_cadeia(tmp_path):
    trilha = TrilhaAuditoria(tmp_path, "C1", operador="op")
    trilha.registrar("campanha_iniciada", alvo="10.0.0.5")
    trilha.registrar("acao_executada", acao="executar_recon", sucesso=True)
    assert verificar_trilha(trilha.caminho) == (True, 2)


def test_continua_cadeia_apos_reabrir(tmp_path):
    TrilhaAuditoria(tmp_path, "C1", operador="op").registrar("a")
    TrilhaAuditoria(tmp_path, "C1", operador="op").registrar("b")
    assert verificar_trilha(tmp_path / "C1.jsonl") == (True, 2)


def test_detecta_adulteracao(tmp_path):
    trilha = TrilhaAuditoria(tmp_path, "C1", operador="op")
    for i in range(3):
        trilha.registrar("evento", indice=i)
    linhas = trilha.caminho.read_text(encoding="utf-8").splitlines()
    registro = json.loads(linhas[1])
    registro["indice"] = 99
    linhas[1] = json.dumps(registro)
    trilha.caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    assert verificar_trilha(trilha.caminho) == (False, 1)


def test_mascara_campos_sensiveis(tmp_path):
    trilha = TrilhaAuditoria(tmp_path, "C1", operador="op")
    registro = trilha.registrar("cfg", api_key="valor-secreto", dados={"senha": "x", "porta": 22})
    conteudo = trilha.caminho.read_text(encoding="utf-8")
    assert "valor-secreto" not in conteudo
    assert registro["api_key"] == "***"
    assert registro["dados"] == {"senha": "***", "porta": 22}
