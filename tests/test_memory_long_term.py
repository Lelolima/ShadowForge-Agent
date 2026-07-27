"""
============================================================
NVIDIA ShadowForge Agent - Testes de Memoria Longo Prazo
Arquivo: tests/test_memory_long_term.py
================================================================
Testes para: MemoriaLongoPrazo (memoria persistente com embeddings).
================================================================
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

# Adiciona root ao path para import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from core.memory import MemoriaLongoPrazo, EntradaMemoria


class TestMemoriaLongoPrazo:
    def setup_method(self) -> None:
        """Cria um banco temporario para cada teste."""
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_file.name
        self.temp_file.close()
        self.mem_lp = MemoriaLongoPrazo(db_path=self.db_path)

    def teardown_method(self) -> None:
        """Remove o banco temporario apos o teste."""
        # Fecha a conexao assincrona se existir
        if self.mem_lp:
            try:
                asyncio.run(self.mem_lp.close())
            except Exception:
                pass  # Ignora erros durante o fechamento
        # Remove o arquivo
        Path(self.db_path).unlink(missing_ok=True)

    def test_armazenar_e_buscar_semantico(self) -> None:
        """Testa armazenamento e busca semantica na memória longo prazo."""
        async def test():
            entrada = EntradaMemoria(
                id="id1",
                tipo="licao",
                conteudo="Ataque SQL injection comum em parametros de login",
                contexto="teste",
                importancia=0.9,
                tags=["sql_injection", "licao"],
            )
            await self.mem_lp.armazenar(entrada)

            # Busca por termo relacionado
            resultados = await self.mem_lp.buscar_semantico("sql injection", limite=5)
            assert len(resultados) == 1
            assert resultados[0].tipo == "licao"
            assert "SQL injection" in resultados[0].conteudo
            assert resultados[0].importancia == 0.9

        asyncio.run(test())

    def test_buscar_por_campanha(self) -> None:
        """Testa busca por ID de campanha."""
        async def test():
            entrada1 = EntradaMemoria(
                id="id1",
                tipo="observacao",
                conteudo="Host 192.168.1.1 ativo",
                contexto="recon",
                campanha_id="camp123",
                importancia=0.5,
            )
            entrada2 = EntradaMemoria(
                id="id2",
                tipo="observacao",
                conteudo="Host 10.0.0.1 ativo",
                contexto="recon",
                campanha_id="camp456",
                importancia=0.5,
            )
            await self.mem_lp.armazenar(entrada1)
            await self.mem_lp.armazenar(entrada2)

            resultados = await self.mem_lp.buscar_por_campanha("camp123")
            assert len(resultados) == 1
            assert resultados[0].conteudo == "Host 192.168.1.1 ativo"
            assert resultados[0].campanha_id == "camp123"

        asyncio.run(test())

    def test_recuperar_licoes(self) -> None:
        """Testa recuperacao de lições aplicadas."""
        async def test():
            licao1 = EntradaMemoria(
                id="id1",
                tipo="licao",
                conteudo="Senha fraca encontrada em servico SSH",
                contexto="post_exploit",
                importancia=0.8,
                tags=["senha_fraca", "ssh"],
            )
            licao2 = EntradaMemoria(
                id="id2",
                tipo="licao",
                conteudo="Porta 8080 exposta sem autenticacao",
                contexto="scan",
                importancia=0.6,
                tags=["porta_aberta", "8080"],
            )
            # Uma entrada que nao é licao
            obs = EntradaMemoria(
                id="id3",
                tipo="observacao",
                conteudo="Scan completo finalizado",
                contexto="scan",
                importancia=0.3,
            )

            await self.mem_lp.armazenar(licao1)
            await self.mem_lp.armazenar(licao2)
            await self.mem_lp.armazenar(obs)

            liccoes = await self.mem_lp.recuperar_licoes(limite=5)
            assert len(liccoes) == 2
            assert all(l.tipo == "licao" for l in liccoes)
            # Verifica que estao ordenadas por importancia (maior primeiro)
            assert liccoes[0].importancia >= liccoes[1].importancia

        asyncio.run(test())

    def test_estatisticas(self) -> None:
        """Testa obtencao de estatisticas da memoria longo prazo."""
        async def test():
            entrada1 = EntradaMemoria(
                id="id1",
                tipo="observacao",
                conteudo="obs1",
                importancia=0.3,
            )
            entrada2 = EntradaMemoria(
                id="id2",
                tipo="licao",
                conteudo="licao1",
                importancia=0.8,
            )
            entrada3 = EntradaMemoria(
                id="id3",
                tipo="acao",
                conteudo="acao1",
                importancia=0.5,
            )

            await self.mem_lp.armazenar(entrada1)
            await self.mem_lp.armazenar(entrada2)
            await self.mem_lp.armazenar(entrada3)

            stats = await self.mem_lp.estatisticas()
            assert stats["total_entradas"] == 3
            assert stats["por_tipo"]["observacao"] == 1
            assert stats["por_tipo"]["licao"] == 1
            assert stats["por_tipo"]["acao"] == 1

        asyncio.run(test())

    def test_limite_busca_semantico(self) -> None:
        """Testa que o limite de resultados na busca semantica eh respeitado."""
        async def test():
            for i in range(10):
                entrada = EntradaMemoria(
                    id=f"id{i}",
                    tipo="observacao",
                    conteudo=f"info {i}",
                    importancia=0.1 * i,  # importancia crescente
                )
                await self.mem_lp.armazenar(entrada)

            resultados = await self.mem_lp.buscar_semantico("info", limite=3)
            assert len(resultados) == 3
            # Verifica que os resultados sao os de maior importancia (devido ao ORDER BY importancia DESC)
            assert resultados[0].importancia >= resultados[1].importancia >= resultados[2].importancia

        asyncio.run(test())