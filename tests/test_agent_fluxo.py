"""Fluxo de ponta a ponta do agente (OODA) sem rede: dry-run, bloqueio e modo real mockado."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from core.agent import ShadowForgeAgent
from core.state import FaseOperacao

CONFIG = str(Path(__file__).parent.parent / "config" / "default.yaml")


def _agente(tmp_path, monkeypatch, **kwargs) -> ShadowForgeAgent:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    agente = ShadowForgeAgent(config_path=CONFIG, **kwargs)
    ooda = agente.config.ooda
    ooda.intervalo_observe_ms = ooda.intervalo_orient_ms = 100
    ooda.intervalo_decide_ms = 100
    ooda.intervalo_act_ms = 50
    return agente


@pytest.mark.asyncio
async def test_dry_run_conclui_campanha_e_salva_relatorio(tmp_path, monkeypatch):
    agente = _agente(tmp_path, monkeypatch, target="10.0.0.5", simulate=True, max_iteracoes=20)
    try:
        await agente.run()
    finally:
        await agente.shutdown()
    assert agente.estado.fase_atual == FaseOperacao.COMPLETED
    tipos = [a.tipo for a in agente.estado.acoes]
    assert "executar_recon" in tipos  # fase de recon não é mais pulada
    relatorios = list((tmp_path / "data" / "reports").glob("report_*.md"))
    assert relatorios, "relatório markdown não foi salvo"
    assert "DRY-RUN" in relatorios[0].read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_modo_real_sem_escopo_e_bloqueado_e_encerra(tmp_path, monkeypatch):
    agente = _agente(tmp_path, monkeypatch, target="10.0.0.5", simulate=False, max_iteracoes=50)
    try:
        await agente.run()
    finally:
        await agente.shutdown()
    assert agente._iteracao <= ShadowForgeAgent.MAX_BLOQUEIOS_CONSECUTIVOS
    assert agente.estado.fase_atual != FaseOperacao.COMPLETED


@pytest.mark.asyncio
async def test_modo_real_com_escopo_chama_scanner(tmp_path, monkeypatch):
    agente = _agente(
        tmp_path, monkeypatch, target="10.0.0.5", simulate=False, scope=["10.0.0.0/24"], max_iteracoes=3
    )
    await agente.inicializar_subsistemas()
    scanner = agente._hacker_tools["recon"]
    # Nenhuma execução real: port_scan e DNS mockados
    scanner.port_scan = AsyncMock(return_value=[])
    scanner.dns_enumeration = AsyncMock(return_value={})
    agente.inicializar_subsistemas = AsyncMock()  # já inicializado
    try:
        await agente.run()
    finally:
        await agente.shutdown()
    scanner.port_scan.assert_awaited_once()
    assert scanner.port_scan.await_args.args[0] == "10.0.0.5"
