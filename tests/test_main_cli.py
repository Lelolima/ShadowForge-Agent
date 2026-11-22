"""Testes da linha de comando (main.py) sem iniciar o agente."""

import io

import pytest

import main


def _launcher(argv):
    launcher = main.ShadowForgeLauncher()
    launcher.args = launcher.parse_args(argv)
    return launcher


def test_dry_run_e_alias_de_simulate():
    assert _launcher(["--dry-run"]).args.simulate is True
    assert _launcher(["--simulate"]).args.simulate is True
    assert _launcher([]).args.simulate is False


def test_scope_repetivel_e_arquivo(tmp_path):
    arquivo = tmp_path / "escopo.txt"
    arquivo.write_text("# lab\n10.0.0.0/24\nlab.local\n", encoding="utf-8")
    args = _launcher(["--scope", "192.168.56.10", "--scope-file", str(arquivo)]).args
    assert "192.168.56.10" in args.scope
    assert "10.0.0.0/24" in args.scope and "lab.local" in args.scope


def test_scope_file_inexistente_falha(tmp_path):
    with pytest.raises(SystemExit):
        _launcher(["--scope-file", str(tmp_path / "nao_existe.txt")])


def test_confirmacao_yes_confirma():
    assert _launcher(["--yes"])._criar_confirmacao()("executar_recon contra x") is True


def test_confirmacao_sem_terminal_nega(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert _launcher([])._criar_confirmacao() is None


def test_confirmacao_interativa(monkeypatch):
    class Tty(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setattr("sys.stdin", Tty(""))
    monkeypatch.setattr("builtins.input", lambda _prompt: "s")
    assert _launcher([])._criar_confirmacao()("x") is True
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    assert _launcher([])._criar_confirmacao()("x") is False
