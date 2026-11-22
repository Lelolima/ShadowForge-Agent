"""Testes de regressão da auditoria 2026-11-22 (sem rede e sem subprocessos reais)."""

from unittest.mock import patch

import pytest

from control.shell import StealthShell
from core.security.injection_prevention import (
    escape_like_pattern,
    execute_safe_command,
    validate_and_sanitize_filename,
)
from core.security.input_validation import ValidationError
from observability import alerting


def test_escape_like_pattern_nao_escapa_duas_vezes():
    bs = chr(92)  # barra invertida
    assert escape_like_pattern("100%") == "100" + bs + "%"
    assert escape_like_pattern("a_b") == "a" + bs + "_b"
    assert escape_like_pattern("C:" + bs + "x") == "C:" + bs * 2 + "x"


@pytest.mark.parametrize("nome", ["../etc/passwd", "/abs/path", ".." + chr(92) + "win.ini", ".."])
def test_filename_com_componentes_de_caminho_e_rejeitado(nome):
    with pytest.raises(ValidationError):
        validate_and_sanitize_filename(nome)


def test_execute_safe_command_inexistente_retorna_127():
    with patch("subprocess.run", side_effect=FileNotFoundError("nao existe")):
        res = execute_safe_command("comandoinexistente", [])
    assert res.returncode == 127


@pytest.mark.asyncio
async def test_shell_oserror_nao_vira_nameerror():
    """Antes: `subprocess` não era importado e OSError virava NameError."""
    shell = StealthShell()
    with patch("asyncio.create_subprocess_shell", side_effect=OSError("falha simulada")), \
         patch("asyncio.create_subprocess_exec", side_effect=OSError("falha simulada")):
        res = await shell.executar("echo teste")
    assert res.returncode == -1
    assert "falha simulada" in res.stderr


def test_alerta_dispara_webhook_com_mensagem(monkeypatch):
    """Antes: `_()` indefinido gerava NameError e regra de quantil nunca disparava."""
    for nome in alerting._alert_state:
        monkeypatch.setitem(alerting._alert_state, nome, False)
        monkeypatch.setitem(alerting._last_alert_time, nome, 0)
    for regra in alerting.ALERT_RULES:
        monkeypatch.setenv(regra["webhook_key"], "http://webhook.invalid/x")
    enviados = []
    monkeypatch.setattr(alerting, "_send_webhook", lambda url, p: enviados.append(p) or True)
    valores = {
        "shadowforge_errors_total": 50,
        "shadowforge_ooda_duration_seconds": 9.0,
        "shadowforge_subsystem_health": 0.0,
    }
    alerting.evaluate_alert_rules(get_metric_fn=valores.get)
    nomes = {p["alert"] for p in enviados}
    assert nomes == {"high_error_rate", "high_ooda_latency", "subsystem_unhealthy"}
    assert all(p["message"] for p in enviados)
