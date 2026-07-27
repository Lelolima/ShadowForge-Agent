"""
============================================================
NVIDIA ShadowForge Agent - Sistema de Memória
Arquivo: core/memory.py
============================================================
Memória de curto e longo prazo com integração NVIDIA
Embeddings para busca semântica de experiências passadas.
============================================================
"""

from __future__ import annotations

import json
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger("shadowforge.core.memory")


@dataclass
class EntradaMemoria:
    """Uma entrada na memória do agente."""
    id: str = ""
    tipo: str = "observacao"  # observacao, acao, resultado, licao, tecnica
    conteudo: str = ""
    contexto: str = ""
    campanha_id: str = ""
    fase: str = ""
    importancia: float = 0.5
    embedding: list[float] | None = None
    tags: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        d = {
            "id": self.id,
            "tipo": self.tipo,
            "conteudo": self.conteudo,
            "contexto": self.contexto,
            "campanha_id": self.campanha_id,
            "fase": self.fase,
            "importancia": self.importancia,
            "tags": self.tags,
            "timestamp": self.timestamp,
        }
        if self.embedding is not None:
            d["embedding"] = self.embedding
        return d


class MemoriaCurtoPrazo:
    """Memória de curto prazo — sessão atual.

    Armazena observações, ações e resultados recentes
    em buffer circular com limite de tamanho.

    M-01 FIX: Usa OrderedDict com LRU para evict O(1) em vez de O(n²).
    """

    def __init__(self, capacidade: int = 500) -> None:
        self.capacidade = capacidade
        self._entradas: OrderedDict[str, EntradaMemoria] = OrderedDict()
        self._indice_por_tipo: dict[str, list[str]] = {}
        self._counter = 0

    def adicionar(self, tipo: str, conteudo: str, contexto: str = "",
                  importancia: float = 0.5, tags: list[str] | None = None) -> EntradaMemoria:
        """Adiciona entrada à memória de curto prazo."""
        self._counter += 1
        entry_id = f"MCP-{self._counter:06d}"

        entrada = EntradaMemoria(
            id=entry_id,
            tipo=tipo,
            conteudo=conteudo,
            contexto=contexto,
            importancia=importancia,
            tags=tags or [],
        )

        # Inserir ou mover para o fim (LRU)
        if entry_id in self._entradas:
            self._entradas.move_to_end(entry_id)
        else:
            self._entradas[entry_id] = entrada

        # Índice por tipo
        if tipo not in self._indice_por_tipo:
            self._indice_por_tipo[tipo] = []
        if entry_id not in self._indice_por_tipo[tipo]:
            self._indice_por_tipo[tipo].append(entry_id)

        # Evict se exceder capacidade (remove o mais antigo — FIFO/LRU)
        if len(self._entradas) > self.capacidade:
            oldest_id, oldest_entry = self._entradas.popitem(last=False)
            # Remover do índice por tipo
            tipo_list = self._indice_por_tipo.get(oldest_entry.tipo)
            if tipo_list:
                try:
                    tipo_list.remove(oldest_id)
                except ValueError:
                    pass
                if not tipo_list:
                    del self._indice_por_tipo[oldest_entry.tipo]

        return entrada

    def buscar_por_tipo(self, tipo: str, limite: int = 50) -> list[EntradaMemoria]:
        """Busca entradas do tipo especificado."""
        ids = self._indice_por_tipo.get(tipo, [])
        result = [self._entradas[eid] for eid in ids[-limite:] if eid in self._entradas]
        return result

    def buscar_recentes(self, limite: int = 20) -> list[EntradaMemoria]:
        """Retorna N entradas mais recentes."""
        all_entries = list(self._entradas.values())
        return all_entries[-limite:]

    def buscar_por_tags(self, tags: list[str], limite: int = 20) -> list[EntradaMemoria]:
        """Busca entradas que contenham qualquer das tags."""
        resultados = []
        tags_set = set(tags)
        for entrada in reversed(list(self._entradas.values())):
            if tags_set & set(entrada.tags):
                resultados.append(entrada)
            if len(resultados) >= limite:
                break
        return resultados

    def contexto_recente(self, n_entradas: int = 10) -> str:
        """Formata contexto recente para prompt do LLM."""
        recentes = self.buscar_recentes(n_entradas)
        if not recentes:
            return "Nenhuma observation anterior nesta sessão."

        linhas = []
        for e in recentes:
            linhas.append(f"[{e.tipo}|{e.timestamp[-8:]}] {e.conteudo}")
        return "\n".join(linhas)

    def limpar(self) -> None:
        """Limpa toda a memória de curto prazo."""
        self._entradas.clear()
        self._indice_por_tipo.clear()

    @property
    def tamanho(self) -> int:
        return len(self._entradas)


class MemoriaLongoPrazo:
    """Memória de longo prazo — persistida em SQLite + embeddings.

    Armazena lições aprendidas, técnicas bem-sucedidas,
    resultados de campanhas anteriores e conoscenza acumulado.

    H-03 FIX: Mantém conexão persistente aiosqlite em vez de abrir
    uma nova conexão a cada operação.
    """

    def __init__(self, db_path: str | Path = "data/memory/long_term.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False
        self._db: aiosqlite.Connection | None = None

    async def _ensure_db(self) -> aiosqlite.Connection:
        """Garante que o banco está inicializado e retorna conexão persistente.

        H-03 FIX: Retorna conexão persistente em vez de criar nova cada vez.
        """
        if self._db is not None and self._initialized:
            return self._db

        self._db = await aiosqlite.connect(str(self._db_path))
        self._db.row_factory = aiosqlite.Row

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS memoria_longo_prazo (
                id TEXT PRIMARY KEY,
                tipo TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                contexto TEXT,
                campanha_id TEXT,
                fase TEXT,
                importancia REAL DEFAULT 0.5,
                tags TEXT,
                timestamp TEXT NOT NULL,
                embedding_id TEXT
            )
        """)
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tipo ON memoria_longo_prazo(tipo)
        """)
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_campanha ON memoria_longo_prazo(campanha_id)
        """)
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_importancia ON memoria_longo_prazo(importancia DESC)
        """)
        await self._db.commit()

        self._initialized = True
        return self._db

    async def close(self) -> None:
        """Fecha a conexão persistente com o banco."""
        if self._db is not None:
            await self._db.close()
            self._db = None
            self._initialized = False

    async def armazenar(self, entrada: EntradaMemoria) -> str:
        """Armazena uma entrada na memória de longo prazo."""
        db = await self._ensure_db()

        await db.execute(
            """INSERT OR REPLACE INTO memoria_longo_prazo
            (id, tipo, conteudo, contexto, campanha_id, fase, importancia, tags, timestamp, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (entrada.id, entrada.tipo, entrada.conteudo, entrada.contexto,
             entrada.campanha_id, entrada.fase, entrada.importancia,
             json.dumps(entrada.tags), entrada.timestamp,
             str(hash(entrada.conteudo) % (10**9))),
        )
        await db.commit()

        return entrada.id

    async def buscar_semantico(self, query: str, limite: int = 10) -> list[EntradaMemoria]:
        """Busca semântica usando embeddings NVIDIA.

        Na ausência de embeddings calculados, faz busca por texto.
        """
        db = await self._ensure_db()
        resultados = []
        query_lower = query.lower()

        # Busca por texto (fallback quando embeddings não disponíveis)
        async with db.execute(
            """SELECT * FROM memoria_longo_prazo
            WHERE conteudo LIKE ? OR contexto LIKE ?
            ORDER BY importancia DESC LIMIT ?""",
            (f"%{query_lower}%", f"%{query_lower}%", limite),
        ) as cursor:
            async for row in cursor:
                resultados.append(EntradaMemoria(
                    id=row["id"],
                    tipo=row["tipo"],
                    conteudo=row["conteudo"],
                    contexto=row["contexto"] or "",
                    campanha_id=row["campanha_id"] or "",
                    fase=row["fase"] or "",
                    importancia=row["importancia"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    timestamp=row["timestamp"],
                ))

        return resultados

    async def buscar_por_campanha(self, campanha_id: str) -> list[EntradaMemoria]:
        """Recupera todas as entradas de uma campanha."""
        db = await self._ensure_db()
        resultados = []
        async with db.execute(
            "SELECT * FROM memoria_longo_prazo WHERE campanha_id=? ORDER BY timestamp",
            (campanha_id,),
        ) as cursor:
            async for row in cursor:
                resultados.append(EntradaMemoria(
                    id=row["id"], tipo=row["tipo"],
                    conteudo=row["conteudo"], contexto=row["contexto"] or "",
                    campanha_id=row["campanha_id"] or "",
                    fase=row["fase"] or "",
                    importancia=row["importancia"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    timestamp=row["timestamp"],
                ))

        return resultados

    async def recuperar_licoes(self, tipo_vuln: str = "", limite: int = 20) -> list[EntradaMemoria]:
        """Recupera lições aprendidas relevantes.

        H-06 FIX: Inclui campanha_id e fase na desserialização (antes faltavam).
        """
        db = await self._ensure_db()
        resultados = []

        query = "SELECT * FROM memoria_longo_prazo WHERE tipo='licao'"
        params: list[Any] = []

        if tipo_vuln:
            query += " AND (conteudo LIKE ? OR tags LIKE ?)"
            params.extend([f"%{tipo_vuln}%", f"%{tipo_vuln}%"])

        query += " ORDER BY importancia DESC LIMIT ?"
        params.append(limite)

        async with db.execute(query, params) as cursor:
            async for row in cursor:
                resultados.append(EntradaMemoria(
                    id=row["id"], tipo=row["tipo"],
                    conteudo=row["conteudo"], contexto=row["contexto"] or "",
                    campanha_id=row["campanha_id"] or "",  # H-06 FIX: campo estava faltando
                    fase=row["fase"] or "",                  # H-06 FIX: campo estava faltando
                    importancia=row["importancia"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    timestamp=row["timestamp"],
                ))

        return resultados

    async def estatisticas(self) -> dict[str, Any]:
        """Retorna estatísticas da memória de longo prazo."""
        db = await self._ensure_db()
        total = await db.execute_fetchall("SELECT COUNT(*) as c FROM memoria_longo_prazo")
        tipos = await db.execute_fetchall("SELECT tipo, COUNT(*) as c FROM memoria_longo_prazo GROUP BY tipo")

        return {
            "total_entradas": total[0][0] if total else 0,
            "por_tipo": {t[0]: t[1] for t in tipos},
        }