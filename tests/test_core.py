"""
============================================================
NVIDIA ShadowForge - Testes Unitarios do Core
Arquivo: tests/test_core.py
============================================================
Testes para: EstadoAgente, Memoria, Guardrails Eticos, OODA.
============================================================
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

# Adiciona root ao path para import
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from core.state import (
    EstadoAgente,
    FaseOperacao,
    Severidade,
    TipoVulnerabilidade,
    HostAlvo,
)
from core.memory import MemoriaCurtoPrazo, EntradaMemoria
from core.config import ShadowForgeConfig, ModoOperacao

# =============================================================================
# L-09 FIX: Testes unitarios para EstadoAgente (state)
# =============================================================================


class TestEstadoAgente:
    def test_criacao_basica(self) -> None:
        estado = EstadoAgente()
        assert estado.fase_atual == FaseOperacao.IDLE
        assert estado.alvo_principal is None
        assert len(estado.alvos) == 0
        assert len(estado.vulnerabilidades) == 0
        assert estado.campanha_id.startswith("SF-")

    def test_registrar_vulnerabilidade(self) -> None:
        estado = EstadoAgente()
        vuln = estado.registrar_vulnerabilidade(
            tipo=TipoVulnerabilidade.SQL_INJECTION,
            severidade=Severidade.CRITICAL,
            titulo="SQLi no login",
            descricao="Injection no parametro username",
            localizacao="/login.php",
            cvss_score=9.8,
        )
        assert vuln.id.startswith("V-")
        assert vuln.tipo == TipoVulnerabilidade.SQL_INJECTION
        assert vuln.severidade == Severidade.CRITICAL
        assert vuln.cvss_score == 9.8
        assert len(estado.vulnerabilidades) == 1
        assert estado.vuln_counter == 1

    def test_registrar_acao(self) -> None:
        estado = EstadoAgente()
        acao = estado.registrar_acao(
            fase="reconnaissance",
            tipo="scan",
            descricao="Port scan do alvo",
            alvo="192.168.1.1",
            sucesso=True,
        )
        assert acao.id.startswith("A-")
        assert acao.fase == "reconnaissance"
        assert acao.sucesso is True
        assert len(estado.acoes) == 1
        assert estado.acao_counter == 1

    def test_avancar_fase(self) -> None:
        estado = EstadoAgente()
        assert estado.fase_atual == FaseOperacao.IDLE
        estado.avancar_fase()
        assert estado.fase_atual == FaseOperacao.RECON
        estado.avancar_fase()
        assert estado.fase_atual == FaseOperacao.SCAN
        # Verifica que fase_anterior é atualizada
        assert estado.fase_anterior == FaseOperacao.RECON

    def test_adicionar_alvo(self) -> None:
        estado = EstadoAgente()
        host = HostAlvo(endereco="192.168.1.1", hostname="target.local")
        estado.adicionar_alvo(host)
        assert len(estado.alvos) == 1
        assert estado.alvos[0].endereco == "192.168.1.1"

    def test_resumo(self) -> None:
        estado = EstadoAgente()
        estado.alvo_principal = "192.168.1.1"
        estado.registrar_vulnerabilidade(
            TipoVulnerabilidade.SQL_INJECTION, Severidade.CRITICAL, "SQLi", "desc"
        )
        resumo = estado.resumo()
        assert resumo["fase_atual"] == "idle"
        assert resumo["total_vulnerabilidades"] == 1
        assert resumo["alvo_principal"] == "192.168.1.1"
        assert "severidade_dist" in resumo

    def test_persistencia_db(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            estado = EstadoAgente(db_path=db_path)
            estado.registrar_vulnerabilidade(
                TipoVulnerabilidade.SQL_INJECTION, Severidade.HIGH, "teste", "desc"
            )
            estado.registrar_acao(fase="recon", tipo="scan", descricao="test", sucesso=True)
            # Verifica que DB foi criado (não lança erro)
            import sqlite3
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {row[0] for row in cursor.fetchall()}
                assert "vulnerabilidades" in tables
                assert "acoes" in tables
                assert "campanhas" in tables
        finally:
            # Attempt to delete the temporary file, retrying on PermissionError (Windows)
            import time
            for _ in range(3):
                try:
                    Path(db_path).unlink(missing_ok=True)
                    break
                except PermissionError:
                    time.sleep(0.1)
            else:
                import warnings
                warnings.warn(f"Could not delete temporary file {db_path} after multiple attempts.")


# =============================================================================
# L-09 FIX: Testes para Memoria (curto e longo prazo)
# =============================================================================


class TestMemoriaCurtoPrazo:
    def test_adicionar_e_buscar(self) -> None:
        mem = MemoriaCurtoPrazo(capacidade=10)
        entrada = mem.adicionar(
            tipo="observacao",
            conteudo="Host 192.168.1.1 tem SSH aberto",
            contexto="recon",
            importancia=0.8,
            tags=["ssh", "recon"],
        )
        assert isinstance(entrada, EntradaMemoria)
        assert entrada.tipo == "observacao"
        assert entrada.id.startswith("MCP-")

        resultados = mem.buscar_por_tipo("observacao")
        assert len(resultados) == 1
        assert resultados[0].conteudo == "Host 192.168.1.1 tem SSH aberto"

    def test_buscar_por_tags(self) -> None:
        mem = MemoriaCurtoPrazo(capacidade=10)
        mem.adicionar("observacao", "Host A", tags=["ssh"])
        mem.adicionar("observacao", "Host B", tags=["http"])
        mem.adicionar("acao", "Brute force", tags=["ssh"])

        resultados = mem.buscar_por_tags(["ssh"])
        assert len(resultados) == 2

    def test_evict(self) -> None:
        mem = MemoriaCurtoPrazo(capacidade=5)
        for i in range(7):
            mem.adicionar("observacao", f"entrada {i}", importancia=0.1 * i)
        assert mem.tamanho <= 5

    def test_contexto_recente(self) -> None:
        mem = MemoriaCurtoPrazo(capacidade=10)
        mem.adicionar("observacao", "SSH na porta 22")
        mem.adicionar("acao", "Executar nmap")
        ctx = mem.contexto_recente(2)
        assert "acao" in ctx
        assert "nmap" in ctx


# =============================================================================
# L-09 FIX: Testes para Guardrails Eticos
# =============================================================================


class TestGuardrailsEticos:
    def test_verificar_etica_acao_segura(self) -> None:
        config = ShadowForgeConfig()
        permitido, motivo = config.verificar_etica("scan", "192.168.1.1")
        assert permitido is True
        assert "reconnaissance" in motivo.lower()

    def test_verificar_etica_acao_destrutiva(self) -> None:
        config = ShadowForgeConfig()
        permitido, motivo = config.verificar_etica("delete", "192.168.1.1")
        assert permitido is False
        assert "destrutiva" in motivo.lower()

    def test_verificar_etica_backdoor(self) -> None:
        config = ShadowForgeConfig()
        permitido, motivo = config.verificar_etica("implant_persistence", "192.168.1.1")
        assert permitido is False
        assert "backdoor" in motivo.lower()

    def test_verificar_etica_blacklist(self) -> None:
        config = ShadowForgeConfig()
        # 127.0.0.1 está na blacklist default
        permitido, motivo = config.verificar_etica("scan", "127.0.0.1")
        assert permitido is False
        assert "blacklist" in motivo.lower()

    def test_verificar_etica_modo_desenvolvimento(self) -> None:
        config = ShadowForgeConfig()
        config.etica.exigir_autorizacao = False
        permitido, _ = config.verificar_etica("anything", "anywhere")
        assert permitido is True

    def test_verificar_etica_whitelist(self) -> None:
        config = ShadowForgeConfig()
        config.etica.whitelist_hosts = ["192.168."]
        # 10.0.0.1 não está na whitelist
        permitido, motivo = config.verificar_etica("scan", "10.0.0.1")
        assert permitido is False
        assert "whitelist" in motivo.lower()


# =============================================================================
# L-09 FIX: Testes para sequencia OODA / Kill Chain
# =============================================================================


class TestOODAKillChain:
    def test_fluxo_fases(self) -> None:
        estado = EstadoAgente()
        fases_esperadas = [
            FaseOperacao.IDLE,
            FaseOperacao.RECON,
            FaseOperacao.SCAN,
            FaseOperacao.ENUM,
            FaseOperacao.EXPLOIT,
            FaseOperacao.POST,
            FaseOperacao.REPORT,
            FaseOperacao.COMPLETED,
        ]
        for i in range(1, len(fases_esperadas)):
            estado.avancar_fase()
            assert estado.fase_atual == fases_esperadas[i], (
                f"Falha no passo {i}: esperado {fases_esperadas[i].value}, "
                f"obtido {estado.fase_atual.value}"
            )

    def test_fase_emoji(self) -> None:
        assert FaseOperacao.RECON.emoji == "\U0001f50d"
        assert FaseOperacao.EXPLOIT.emoji == "⚡"
        assert FaseOperacao.COMPLETED.emoji == "✅"

    def test_severidade_cvss_range(self) -> None:
        assert Severidade.CRITICAL.cvss_range == (9.0, 10.0)
        assert Severidade.HIGH.cvss_range == (7.0, 8.9)
        assert Severidade.LOW.cvss_range == (0.1, 3.9)


# =============================================================================
# Entry point para execucao manual
# =============================================================================


if __name__ == "__main__":
    import traceback

    all_passed = 0
    all_failed = 0

    print("\n" + "=" * 60)
    print("  NVIDIA ShadowForge - Testes Unitarios Core")
    print("=" * 60)

    test_classes = [
        TestEstadoAgente,
        TestMemoriaCurtoPrazo,
        TestGuardrailsEticos,
        TestOODAKillChain,
    ]

    for cls in test_classes:
        print(f"\n  {cls.__name__}:")
        instance = cls()
        for name in dir(instance):
            if not name.startswith("test_"):
                continue
            method = getattr(instance, name)
            try:
                result = method()
                # Suporta tanto sync quanto async
                if asyncio.iscoroutine(result):
                    asyncio.run(result)
                print(f"    [OK]   {name}")
                all_passed += 1
            except Exception as e:
                print(f"    [FAIL] {name}: {e}")
                traceback.print_exc()
                all_failed += 1

    print(f"\n{'=' * 60}")
    print(f"  Resultado: {all_passed} PASS | {all_failed} FAIL")
    print(f"{'=' * 60}\n")