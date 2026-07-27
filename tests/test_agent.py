"""
============================================================
NVIDIA ShadowForge Agent - Testes Unitarios para o Agente Principal
Arquivo: tests/test_agent.py
============================================================
Testes para: Agent (loop OODA, state machine, integracao de componentes).
============================================================
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import sys
from pathlib import Path

# Adiciona root ao path para import
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from core.agent import ShadowForgeAgent
from core.config import ShadowForgeConfig, ModoOperacao
from core.state import EstadoAgente, FaseOperacao


def test_agent_criacao_basica() -> None:
    """Testa a criação básica do agente com mocks no carregamento de config."""
    # Mock do carregamento de config para evitar necessidade de arquivo yaml ou env
    with patch('core.config.ShadowForgeConfig.carregar_de_yaml') as mock_yaml, \
         patch('core.config.ShadowForgeConfig.carregar_de_env') as mock_env:
        # Configura o mock para retornar um config padrão
        mock_config = MagicMock(spec=ShadowForgeConfig)
        mock_config.data_dir = Path("/tmp/test_shadowforge")
        mock_config.nvidia = MagicMock()
        mock_config.nvidia.modelos = MagicMock()
        mock_config.nvidia.modelos.visao = MagicMock()
        mock_config.nvidia.modelos.visao.modelo = "test_model"
        mock_config.nvidia.modelos.visao.temperatura = 0.3
        mock_config.nvidia.modelos.visao.max_tokens = 2048
        mock_config.etica = MagicMock()
        mock_config.etica.exigir_autorizacao = True
        mock_yaml.return_value = mock_config
        mock_env.return_value = mock_config

        agent = ShadowForgeAgent(
            config_path="config/default.yaml",
            mode="stealth",
            target="192.168.1.1",
            voice_enabled=False,
            simulate=False,
            gpu_id=0,
            campaign="TEST_CAMP"
        )

        # Verifica que o agente foi criado com as configurações corretas
        assert agent.config == mock_config
        assert agent.estado is not None
        assert isinstance(agent.estado, EstadoAgente)
        assert agent.estado.fase_atual == FaseOperacao.IDLE
        assert agent.estado.alvo_principal == "192.168.1.1"
        assert agent.estado.campanha_id == "TEST_CAMP"


def test_agent_transicao_fases() -> None:
    """Testa a transicao de fases via metodo avancar_fase do estado."""
    # Este teste ja esta em test_core.py, mas podemos replicar aqui para garantir
    # que o agente usa o estado corretamente.
    with patch('core.config.ShadowForgeConfig.carregar_de_yaml') as mock_yaml, \
         patch('core.config.ShadowForgeConfig.carregar_de_env') as mock_env:
        mock_config = MagicMock(spec=ShadowForgeConfig)
        mock_config.data_dir = Path("/tmp/test_shadowforge")
        mock_config.nvidia = MagicMock()
        mock_config.nvidia.modelos = MagicMock()
        mock_config.nvidia.modelos.visao = MagicMock()
        mock_config.nvidia.modelos.visao.modelo = "test_model"
        mock_config.nvidia.modelos.visao.temperatura = 0.3
        mock_config.nvidia.modelos.visao.max_tokens = 2048
        mock_config.etica = MagicMock()
        mock_config.etica.exigir_autorizacao = True
        mock_yaml.return_value = mock_config
        mock_env.return_value = mock_config

        agent = ShadowForgeAgent()

        # Verifica a fase inicial
        assert agent.estado.fase_atual == FaseOperacao.IDLE

        # Avança uma fase
        agent.estado.avancar_fase()
        assert agent.estado.fase_atual == FaseOperacao.RECON

        # Avança outra fase
        agent.estado.avancar_fase()
        assert agent.estado.fase_atual == FaseOperacao.SCAN


if __name__ == "__main__":
    # Executa os testes de forma simples
    test_agent_criacao_basica()
    print("[OK] test_agent_criacao_basica passou")

    test_agent_transicao_fases()
    print("[OK] test_agent_transicao_fases passou")

    print("\n[TODOS OK] Todos os testes do agente passaram!")