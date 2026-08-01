import pytest
from pathlib import Path
from core.config import ShadowForgeConfig, ModoOperacao, NivelLog

def test_config_defaults():
    cfg = ShadowForgeConfig()
    assert cfg.nome == "ShadowForge"
    assert cfg.versao == "1.1.0"
    assert cfg.codinome == "SH4D0WF0RG3"
    assert cfg.modo == ModoOperacao.STEALTH
    assert cfg.idioma == "pt-BR"
    assert cfg.leetspeak_logs == True
    assert cfg.tema == "matrix"
    assert cfg.log_nivel == NivelLog.INFO

def test_config_from_yaml(tmp_path):
    yaml_content = """
agente:
  nome: "TestAgent"
  versao: "2.0.0"
  codinome: "TEST"
  modo: "agressivo"
  idioma: "en-US"
  leetspeak_logs: false
  tema: "dark"
  log_nivel: "DEBUG"
etica:
  exigir_autorizacao: true
  bloquear_destruicao: true
nvidia:
  api_key: "test-key"
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)
    cfg = ShadowForgeConfig.carregar_de_yaml(config_file)
    assert cfg.nome == "TestAgent"
    assert cfg.versao == "2.0.0"
    assert cfg.codinome == "TEST"
    assert cfg.modo == ModoOperacao.AGRESSIVO
    assert cfg.idioma == "en-US"
    assert cfg.leetspeak_logs == False
    assert cfg.tema == "dark"
    assert cfg.log_nivel == NivelLog.DEBUG
    assert cfg.nvidia.api_key == "test-key"

def test_config_from_env(monkeypatch):
    monkeypatch.setenv("SHADOWFORGE_MODE", "debug")
    monkeypatch.setenv("SHADOWFORGE__NVIDIA__API_KEY", "env-key")
    cfg = ShadowForgeConfig.carregar_de_env()
    assert cfg.modo == ModoOperacao.DEBUG
    assert cfg.nvidia.api_key == "env-key"