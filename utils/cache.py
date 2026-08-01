"""
============================================================
NVIDIA ShadowForge Agent - Cache Utilities
Arquivo: utils/cache.py
============================================================
Utilitários de caching para melhoria de performance,
incluindo LRU cache com TTL e decoradores prontos para uso.
============================================================
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps
import logging

logger = logging.getLogger("shadowforge.utils.cache")

T = TypeVar('T')


class LRUCache:
    """
    LRU (Least Recently Used) Cache com suporte a TTL (Time To Live).

    Implementação thread-safe para uso em ambientes assíncronos.
    """

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 300):
        """
        Inicializa o cache LRU.

        Args:
            maxsize: Número máximo de entradas no cache
            ttl_seconds: Tempo de vida das entradas em segundos
        """
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    def _make_key(self, *args, **kwargs) -> str:
        """
        Cria uma chave única a partir dos argumentos.

        Args:
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados

        Returns:
            String hash da chave
        """
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_json.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """
        Obtem valor do cache se existir e não estiver expirado.

        Args:
            key: Chave do cache

        Returns:
            Valor cached ou None se não encontrado/expirado
        """
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            # Verificar se expirou
            if time.time() - self._timestamps[key] > self.ttl_seconds:
                # Remover entrada expirada
                del self._cache[key]
                del self._timestamps[key]
                self._misses += 1
                return None

            # Mover para o final (mais recentemente usado)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    async def set(self, key: str, value: Any) -> None:
        """
        Armazena valor no cache, removendo o mais antigo se necessário.

        Args:
            key: Chave do cache
            value: Valor a ser armazenado
        """
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                # Verificar se precisa fazer limpeza
                if len(self._cache) >= self.maxsize:
                    # Remover o item menos recently used
                    oldest_key, _ = self._cache.popitem(last=False)
                    del self._timestamps[oldest_key]

            self._cache[key] = value
            self._timestamps[key] = time.time()

    async def delete(self, key: str) -> bool:
        """
        Remove uma chave do cache.

        Args:
            key: Chave a ser removida

        Returns:
            True se a chave existed e foi removida, False caso contrário
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
                return True
            return False

    async def clear(self) -> None:
        """Limpa todo o cache."""
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0

    async def size(self) -> int:
        """
        Retorna o tamanho atual do cache.

        Returns:
            Número de entradas no cache
        """
        async with self._lock:
            return len(self._cache)

    async def stats(self) -> dict:
        """
        Retorna estatísticas do cache.

        Returns:
            Dicionário com hit rate, miss rate, tamanho, etc.
        """
        async with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
                "ttl_seconds": self.ttl_seconds,
            }


# Instâncias globais de cache para diferentes propósitos
# Cache para resultados de RAG (tempo de vida mais longo devido à natureza estática dos dados)
rag_cache = LRUCache(maxsize=500, ttl_seconds=1800)  # 30 minutos

# Cache para respostas de modelos NIM (tempo de vida médio)
nim_response_cache = LRUCache(maxsize=1000, ttl_seconds=300)  # 5 minutos

# Cache para resultados de ferramentas de hacker (tempo de vida curto devido à volatilidade)
hacker_tool_cache = LRUCache(maxsize=2000, ttl_seconds=60)  # 1 minuto

# Cache para análise de vulnerabilidades (tempo de vida médio)
vulnerability_cache = LRUCache(maxsize=500, ttl_seconds=600)  # 10 minutos


def cached(cache_instance: LRUCache):
    """
    Decortor para caching de funções assíncronas.

    Args:
        cache_instance: Instância do LRUCache a ser usada

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave única baseada na função e argumentos
            key_parts = [func.__module__, func.__qualname__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            key_string = ":".join(key_parts)
            key = hashlib.sha256(key_string.encode()).hexdigest()

            # Tentar obter do cache
            cached_result = await cache_instance.get(key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for {func.__name__}")
                return cached_result

            # Executar função e armazenar resultado
            logger.debug(f"Cache MISS for {func.__name__}")
            result = await func(*args, **kwargs)
            await cache_instance.set(key, result)
            return result

        return wrapper
    return decorator


def cache_rag_result(func: Callable) -> Callable:
    """Decorator específico para cache de resultados RAG."""
    return cached(rag_cache)(func)


def cache_nim_response(func: Callable) -> Callable:
    """Decorator específico para cache de respostas NIM."""
    return cached(nim_response_cache)(func)


def cache_hacker_tool_result(func: Callable) -> Callable:
    """Decorator específico para cache de resultados de ferramentas hacker."""
    return cached(hacker_tool_cache)(func)


def cache_vulnerability_result(func: Callable) -> Callable:
    """Decorator específico para cache de resultados de vulnerabilidade."""
    return cached(vulnerability_cache)(func)


# Funções de conveniência para manipulação directa do cache
async def warm_up_cache():
    """Aquece o cache com dados comuns (placeholder para implementação futura)."""
    logger.info("Cache warm-up not implemented yet")


async def get_cache_stats() -> dict:
    """
    Obtém estatísticas de todos os caches.

    Returns:
        Dicionário com estatísticas de cada cache
    """
    return {
        "rag_cache": await rag_cache.stats(),
        "nim_response_cache": await nim_response_cache.stats(),
        "hacker_tool_cache": await hacker_tool_cache.stats(),
        "vulnerability_cache": await vulnerability_cache.stats(),
    }


async def clear_all_caches() -> None:
    """Limpa todos os caches."""
    await rag_cache.clear()
    await nim_response_cache.clear()
    await hacker_tool_cache.clear()
    await vulnerability_cache.clear()
    logger.info("All caches cleared")