from core.config import ModoOperacao, NivelLog, ShadowForgeConfig


def test_config_defaults():
    cfg = ShadowForgeConfig()
    assert cfg.nome == "ShadowForge"
    assert cfg.versao == "1.1.0"
    assert cfg.codinome == "SH4D0WF0RG3"
    assert cfg.modo == ModoOperacao.STEALTH
    assert cfg.idioma == "pt-BR"
    assert cfg.leetspeak_logs is True
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
    assert cfg.leetspeak_logs is False
    assert cfg.tema == "dark"
    assert cfg.log_nivel == NivelLog.DEBUG
    assert cfg.nvidia.api_key == "test-key"

def test_config_from_env(monkeypatch):
    monkeypatch.setenv("SHADOWFORGE_MODE", "debug")
    monkeypatch.setenv("SHADOWFORGE__NVIDIA__API_KEY", "env-key")
    cfg = ShadowForgeConfig.carregar_de_env()
    assert cfg.modo == ModoOperacao.DEBUG
    assert cfg.nvidia.api_key == "env-key"

def test_modo_aceita_nome_do_campo_e_alias():
    assert ShadowForgeConfig(modo=ModoOperacao.DEBUG).modo == ModoOperacao.DEBUG
    assert ShadowForgeConfig(mode="agressivo").modo == ModoOperacao.AGRESSIVO


def test_carregar_de_env_nao_imprime_api_key(monkeypatch, capsys):
    monkeypatch.setenv("SHADOWFORGE__NVIDIA__API_KEY", "valor-sensivel-de-teste")
    monkeypatch.setenv("SHADOWFORGE_MODE", "debug")
    cfg = ShadowForgeConfig.carregar_de_env()
    saida = capsys.readouterr()
    assert "valor-sensivel-de-teste" not in saida.out + saida.err
    assert cfg.modo == ModoOperacao.DEBUG
