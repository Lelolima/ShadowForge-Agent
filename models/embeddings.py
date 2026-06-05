"""
============================================================
NVIDIA ShadowForge Agent - NVIDIA Embeddings
Arquivo: models/embeddings.py
============================================================
Geração de embeddings via NVIDIA NeMo Retriever
para RAG com busca semântica e similaridade cosseno.
============================================================
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger("shadowforge.models.embeddings")


class NVIDIAEmbeddings:
    """Geração de embeddings via NVIDIA NeMo Retriever.

    Usa modelos NVIDIA para gerar embeddings densos
    para RAG, busca semântica e clustering de técnicas.
    Com caching para evitar recálculo.
    """

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._modelo = "nvidia/nv-embed-v1"
        self._dimensoes = 1024
        self._batch_size = 32
        self._api_key = ""
        self._base_url = "https://integrate.api.nvidia.com/v1"
        self._cache: dict[str, list[float]] = {}

        if config:
            import os
            self._api_key = getattr(config, "api_key", "")
            if self._api_key.startswith("${"):
                self._api_key = os.environ.get(self._api_key[2:-1], "")
            self._base_url = getattr(config, "base_url", self._base_url)
            modelos = getattr(config, "modelos", None)
            if modelos and hasattr(modelos, "embeddings"):
                self._modelo = modelos.embeddings.modelo
                self._dimensoes = getattr(modelos.embeddings, "dimensoes", 1024)

    async def gerar(self, texto: str) -> list[float]:
        """Gera embedding para um texto.

        Args:
            texto: Texto para embedding

        Returns:
            Lista de floats (vetor embedding)
        """
        # M-02 FIX: Usar blake2b em vez de MD5 (sem colisões conhecidas, mais rápido)
        cache_key = hashlib.blake2b(texto.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self._modelo,
                    "input": [texto],
                    "encoding_format": "float",
                }
                headers = {
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                }

                async with session.post(
                    f"{self._base_url}/embeddings",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embedding = data.get("data", [{}])[0].get("embedding", [])
                        self._cache[cache_key] = embedding
                        return embedding
                    else:
                        logger.error("Embeddings API erro: %d", resp.status)
                        return self._embedding_fallback(texto)

        except ImportError:
            return self._embedding_fallback(texto)
        except Exception as e:
            logger.error("Erro embedding: %s", e)
            return self._embedding_fallback(texto)

    async def gerar_batch(self, textos: list[str]) -> list[list[float]]:
        """Gera embeddings para múltiplos textos em batch."""
        resultados = []
        for i in range(0, len(textos), self._batch_size):
            batch = textos[i:i + self._batch_size]
            batch_embeddings = []
            for texto in batch:
                emb = await self.gerar(texto)
                batch_embeddings.append(emb)
            resultados.extend(batch_embeddings)
        return resultados

    @staticmethod
    def similaridade_cosseno(a: list[float], b: list[float]) -> float:
        """Calcula similaridade cosseno entre dois vetores."""
        if not a or not b or len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def _embedding_fallback(self, texto: str) -> list[float]:
        """Embedding fallback simples baseado em hash.

        M-03 FIX: Trunca o vetor para exatamente _dimensoes dimensões.
        Antes produzia dim incorreta (1056 em vez de 1024).
        """
        h = hashlib.sha256(texto.encode()).digest()
        # Expande o hash para cobrir as dimensões necessárias
        raw = [b / 255.0 for b in h]
        repeats = (self._dimensoes // 32) + (1 if self._dimensoes % 32 else 0)
        vetor = raw * repeats
        # Trunca para exatamente _dimensoes dimensões
        return vetor[:self._dimensoes]
