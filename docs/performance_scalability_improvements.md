# Melhorias de Performance e Escalabilidade para o ShadowForge Agent

Este documento descreve melhorias de performance e escalabilidade para o ShadowForge Agent, abrangendo pooling de conexões, compressão, caching LRU e configuração do PM2 para implantação em produção.

## 1. Pooling de Conexões

### Pooling de Conexões de Banco de Dados

O ShadowForge Agent usa SQLite com aiosqlite para armazenamento persistente de memória. Para otimizar as conexões de banco de dados, implementamos pooling de conexões:

```python
# core/memory.py (aprimorado)
import aiosqlite
from typing import Optional
from contextlib import asynccontextmanager

class DatabasePool:
    """Pool de conexões para operações de banco de dados SQLite."""
    
    def __init__(self, database_path: str, pool_size: int = 10):
        self.database_path = database_path
        self.pool_size = pool_size
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self._initialized = False
    
    async def initialize(self):
        """Inicializa o pool de conexões."""
        if self._initialized:
            return
            
        for _ in range(self.pool_size):
            conn = await aiosqlite.connect(self.database_path)
            await self._pool.put(conn)
        
        self._initialized = True
    
    @asynccontextmanager
    async def acquire(self):
        """Adquire uma conexão do pool."""
        if not self._initialized:
            await self.initialize()
            
        conn = await self._pool.get()
        try:
            yield conn
        finally:
            await self._pool.put(conn)
    
    async def close(self):
        """Fecha todas as conexões no pool."""
        while not self._pool.empty():
            conn = await self._pool.get()
            await conn.close()
```

### Pooling de Conexões de Cliente HTTP

Para chamadas de API externa (NVIDIA NIM, requisições web), implementamos pooling de conexões HTTP:

```python
# models/nim_client.py (aprimorado)
import aiohttp
from typing import Optional

class NIMClient:
    """Cliente NVIDIA NIM com pooling de conexões."""
    
    def __init__(self, config):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
    
    async def _ensure_session(self):
        """Garante que a sessão HTTP com pool de conexões esteja inicializada."""
        if self._session is None or self._session.closed:
            # Configura o pool de conexões
            self._connector = aiohttp.TCPConnector(
                limit=100,           # Máximo total de conexões
                limit_per_host=30,   # Máximo de conexões por host
                ttl_dns_cache=300,   # TTL do cache de DNS
                use_dns_cache=True,
            )
            
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=10
            )
            
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                }
            )
    
    async def close(self):
        """Fecha a sessão HTTP e o conector."""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector:
            await self._connector.close()
```

## 2. Estratégias de Compressão

### Compressão de Resposta para Endpoints de API

Para o painel de controle da API, implementamos compressão de resposta:

```python
# api/dashboard.py (aprimorado)
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title="Painel de Controle ShadowForge")
    
    # Adiciona middleware GZip para respostas > 1000 bytes
    app.add_middleware(
        GZipMiddleware, 
        minimum_size=1000,
        compresslevel=6  # Equilíbrio entre taxa de compressão e uso de CPU
    )
    
    return app
```

### Compressão de Dados para Armazenamento

Para armazenar grandes conjuntos de dados em memória ou disco:

```python
# utils/compression.py
import gzip
import json
import pickle
from typing import Any, Union
import lz4.frame  # pip install lz4

class DataCompressor:
    """Utilitário para comprimir e descomprimir dados."""
    
    @staticmethod
    def compress_json(data: Any, method: str = "gzip") -> bytes:
        """Comprime dados serializáveis em JSON."""
        json_str = json.dumps(data, separators=(',', ':'))  # JSON compacto
        
        if method == "gzip":
            return gzip.compress(json_str.encode('utf-8'), compresslevel=6)
        elif method == "lz4":
            return lz4.frame.compress(json_str.encode('utf-8'))
        else:
            raise ValueError(f"Método de compressão não suportado: {method}")
    
    @staticmethod
    def decompress_json(data: bytes, method: str = "gzip") -> Any:
        """Descomprime dados e analisa JSON."""
        if method == "gzip":
            json_str = gzip.decompress(data).decode('utf-8')
        elif method == "lz4":
            json_str = lz4.frame.decompress(data).decode('utf-8')
        else:
            raise ValueError(f"Método de descompressão não suportado: {method}")
        
        return json.loads(json_str)
    
    @staticmethod
    def compress_pickle(obj: Any, method: str = "lz4") -> bytes:
        """Comprime objetos Python usando pickle."""
        pickled = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        
        if method == "lz4":
            return lz4.frame.compress(pickled)
        elif method == "gzip":
            return gzip.compress(pickled, compresslevel=6)
        else:
            raise ValueError(f"Método de compressão não suportado: {method}")
    
    @staticmethod
    def decompress_pickle(data: bytes, method: str = "lz4") -> Any:
        """Descomprime e desserializa dados com pickle."""
        if method == "lz4":
            pickled = lz4.frame.decompress(data)
        elif method == "gzip":
            pickled = gzip.decompress(data)
        else:
            raise ValueError(f"Método de descompressão não suportado: {method}")
        
        return pickle.loads(pickled)
```

## 3. Implementação de Cache LRU

### Cache LRU com Eficiência de Memória

Para cálculos caros e dados frequentemente acessados:

```python
# utils/cache.py
from functools import lru_cache
from typing import Dict, Any, Optional, Callable
import hashlib
import json
from datetime import datetime, timedelta
import asyncio
from collections import OrderedDict

class LRUCache:
    """Cache LRU seguro para threads com suporte a TTL."""
    
    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 300):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    def _make_key(self, *args, **kwargs) -> str:
        """Cria uma chave de cache a partir dos argumentos."""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_json.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache se não estiver expirado."""
        async with self._lock:
            if key not in self._cache:
                return None
            
            # Verifica TTL
            if time.time() - self._timestamps[key] > self.ttl_seconds:
                del self._cache[key]
                del self._timestamps[key]
                return None
            
            # Move para o fim (mais recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
    
    async def set(self, key: str, value: Any) -> None:
        """Define valor no cache, expulsando o mais antigo se necessário."""
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.maxsize:
                    # Remove o item mais antigo
                    oldest_key, _ = self._cache.popitem(last=False)
                    del self._timestamps[oldest_key]
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    async def delete(self, key: str) -> bool:
        """Exclui chave do cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Limpa todas as entradas do cache."""
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    async def size(self) -> int:
        """Obtém o tamanho atual do cache."""
        async with self._lock:
            return len(self._cache)

# Instâncias globais de cache
metadata_cache = LRUCache(maxsize=500, ttl_seconds=600)  # 10 minutos
query_cache = LRUCache(maxsize=1000, ttl_seconds=180)   # 3 minutos
result_cache = LRUCache(maxsize=2000, ttl_seconds=60)   # 1 minuto

def cached(ttl_seconds: int = 300, maxsize: int = 100):
    """Decorador para cachear resultados de funções com TTL."""
    def decorator(func: Callable) -> Callable:
        cache = LRUCache(maxsize=maxsize, ttl_seconds=ttl_seconds)
        
        async def wrapper(*args, **kwargs):
            key = cache._make_key(*args, **kwargs)
            cached_result = await cache.get(key)
            
            if cached_result is not None:
                return cached_result
            
            result = await func(*args, **kwargs)
            await cache.set(key, result)
            return result
        
        return wrapper
    return decorator
```

### Utilizando Cache LRU na Aplicação

```python
# Exemplo de uso em planning/rag.py
from utils.cache import cached

class MITRERAG:
    """Implementação RAG do MITRE ATT&CK com caching."""
    
    def __init__(self, config):
        self.config = config
        self._technique_cache = {}
    
    @cached(ttl_seconds=300, maxsize=500)  # Cache por 5 minutos, máximo 500 entradas
    async def buscar_tecnicas(self, fase: str, alvo: str = "") -> list[dict]:
        """Busca técnicas com caching."""
        # Operação cara - agora em cache
        return await self._expensive_technique_lookup(fase, alvo)
    
    @cached(ttl_seconds=600, maxsize=100)  # Cache por 10 minutos
    async def obter_mitigacoes(self, tecnica_id: str) -> list[dict]:
        """Obtém mitigações para uma técnica com caching."""
        return await self._expensive_mitigatoin_lookup(tecnica_id)
```

## 4. Configuração do PM2 para Produção

### ecosystem.config.js

Crie uma configuração de produção pronta para o PM2:

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "shadowforge-api",
      script: "api/server.py",
      instances: "max", // Use todos os núcleos de CPU
      exec_mode: "cluster",
      watch: false,
      max_memory_restart: "1G",
      env: {
        NODE_ENV: "development",
        SHADOWFORGE_MODE: "stealth",
        LOG_LEVEL: "info"
      },
      env_production: {
        NODE_ENV: "production",
        SHADOWFORGE_MODE: "stealth",
        LOG_LEVEL: "warn"
      }
    },
    {
      name: "shadowforge-worker",
      script: "worker/task_processor.py",
      instances: 2, // Trabalhadores dedicados para tarefas em segundo plano
      exec_mode: "cluster",
      wait_ready: true,
      listen_timeout: 3000,
      max_memory_restart: "500M",
      env: {
        QUEUE_TYPE: "background",
        WORKER_ID: "worker-0"
      }
    }
  ],
  
  deploy: {
    production: {
      user: "deploy",
      host: ["prod-server-1", "prod-server-2"],
      ref: "origin/main",
      repo: "git@github.com:Lelolima/ShadowForge-Agent.git",
      path: "/var/www/shadowforge",
      "post-deploy": "pip install -r requirements.txt && pm2 startOrRestart ecosystem.config.js --env production"
    }
  }
};
```

### Comandos de Gerenciamento de Processos do PM2

```bash
# Inicie a aplicação em produção
pm2 start ecosystem.config.js --env production

# Monitore os processos
pm2 monit

# Mostre os logs
pm2 logs

# Escale a aplicação
pm2 scale shadowforge-api 4  # Escale para 4 instâncias

# Recarga sem downtime
pm2 reload all

# Salve a lista atual de processos
pm2 save

# Gere o script de inicialização
pm2 startup
```

### Configuração Avançada do PM2

Para implantações mais sofisticadas:

```javascript
// ecosystem.config.js (avançado)
module.exports = {
  apps: [
    {
      name: "shadowforge-api",
      script: "api/server.py",
      instances: "max",
      exec_mode: "cluster",
      
      // Condições de reinicialização automática
      autorestart: true,
      max_restarts: 10,
      restart_delay: 1000,
      
      // Gerenciamento de memória
      max_memory_restart: "1G",
      min_uptime: "10s",
      
      // Gerenciamento de logs
      error_file: "./logs/err.log",
      out_file: "./logs/out.log",
      log_date_format: "YYYY-MM-DD HH:mm Z",
      combine_logs: true,
      
      // Variáveis de ambiente
      env: {
        NODE_ENV: "development",
        PORT: 3000,
        DATABASE_POOL_SIZE: 20,
        HTTP_CLIENT_POOL_SIZE: 100
      },
      
      env_production: {
        NODE_ENV: "production",
        PORT: 80,
        DATABASE_POOL_SIZE: 50,
        HTTP_CLIENT_POOL_SIZE: 200,
        LOG_LEVEL: "warn"
      }
    }
  ],
  
  // Configuração de implantação
  deploy: {
    production: {
      user: "ubuntu",
      host: ["prod1.example.com", "prod2.example.com"],
      ref: "origin/main",
      repo: "git@github.com:Lelolima/ShadowForge-Agent.git",
      path: "/var/www/html/{{application}}",
      "post-setup": "pip install -r requirements.txt",
      "post-deploy": "pm2 startOrRestart ecosystem.config.js --env production && pm2 save"
    }
  }
};
```

## 5. Monitoramento e Otimização de Performance

### Coleta de Métricas

Aprimore o módulo de observabilidade para rastrear métricas de performance:

```python
# observability/metrics.py (aprimorado)
from prometheus_client import Counter, Histogram, Gauge, Summary

if HAS_PROMETHEUS:
    # Métricas de Banco de Dados
    DB_QUERY_DURATION = Histogram(
        'shadowforge_db_query_duration_seconds',
        'Duração da consulta do banco de dados',
        ['operation', 'table']
    )
    
    DB_CONNECTION_POOL_SIZE = Gauge(
        'shadowforge_db_connection_pool_size',
        'Tamanho do pool de conexões do banco de dados',
        ['state']  # ativo, ocioso, aguardando
    )
    
    HTTP_REQUEST_DURATION = Histogram(
        'shadowforge_http_request_duration_seconds',
        'Duração da requisição HTTP',
        ['method', 'endpoint', 'status_code']
    )
    
    HTTP_CLIENT_POOL_USAGE = Gauge(
        'shadowforge_http_client_pool_usage',
        'Uso do pool de conexões HTTP do cliente',
        ['state']  # ativo, ocioso
    )
    
    # Métricas de Cache
    CACHE_HITS_TOTAL = Counter(
        'shadowforge_cache_hits_total',
        'Total de acertos de cache',
        ['cache_name']
    )
    
    CACHE_MISSES_TOTAL = Counter(
        'shadowforge_cache_misses_total',
        'Total de faltas de cache',
        ['cache_name']
    )
    
    CACHE_SIZE = Gauge(
        'shadowforge_cache_size',
        'Tamanho atual do cache',
        ['cache_name']
    )
    
    # CPU e Memória
    PROCESS_CPU_SECONDS = Counter(
        'shadowforge_process_cpu_seconds_total',
        'Tempo total de CPU utilizado'
    )
    
    PROCESS_MEMORY_BYTES = Gauge(
        'shadowforge_process_memory_bytes',
        'Uso de memória em bytes',
        ['type']  # rss, vms, etc.
    )
else:
    # Implementações fictícias
    class _DummyMetric:
        def __init__(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        def inc(self, amount=1): pass
        def dec(self, amount=1): pass
        def set(self, value): pass
        def observe(self, value): pass
    
    DB_QUERY_DURATION = _DummyMetric()
    DB_CONNECTION_POOL_SIZE = _DummyMetric()
    HTTP_REQUEST_DURATION = _DummyMetric()
    HTTP_CLIENT_POOL_USAGE = _DummyMetric()
    CACHE_HITS_TOTAL = _DummyMetric()
    CACHE_MISSES_TOTAL = _DummyMetric()
    CACHE_SIZE = _DummyMetric()
    PROCESS_CPU_SECONDS = _DummyMetric()
    PROCESS_MEMORY_BYTES = _DummyMetric()
```

### Middleware de Monitoramento de Performance

```python
# api/middleware.py
from prometheus_client import Counter, Histogram
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware para coletar métricas HTTP."""
    
    def __init__(self, app, app_name: str = "shadowforge"):
        super().__init__(app)
        self.app_name = app_name
        
        if HAS_PROMETHEUS:
            self.REQUEST_COUNT = Counter(
                f'{app_name}_http_requests_total',
                'Total de requisições HTTP',
                ['method', 'endpoint', 'status']
            )
            
            self.REQUEST_LATENCY = Histogram(
                f'{app_name}_http_request_duration_seconds',
                'Latência da requisição HTTP',
                ['method', 'endpoint']
            )
    
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = request.url.path
        
        start_time = time.time()
        response: Response = await call_next(request)
        process_time = time.time() - start_time
        
        status_code = response.status_code
        
        if HAS_PROMETHEUS:
            self.REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            self.REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(process_time)
        
        return response
```

## 6. Guia de Implementação

### Etapa 1: Instalar Dependências

```bash
pip install lz4 prometheus_client aiometer asyncio-throttle
```

### Etapa 2: Pooling de Conexões de Banco de Dados

Atualize `core/memory.py` para usar o pool de conexões:

```python
# Em MemoriaLongoPrazo.__init__
self._db_pool = DatabasePool(db_path, pool_size=20)

# Em _ensure_db method
async def _ensure_db(self) -> aiosqlite.Connection:
    if self._db is not None and self._initialized:
        return self._db
    
    # Inicialize o pool se necessário
    await self._db_pool.initialize()
    
    # Obtenha conexão do pool
    async with self._db_pool.acquire() as conn:
        self._db = conn
        # ... resto da inicialização
```

### Etapa 3: Pooling de Cliente HTTP

Atualize os clientes de serviço externo para usar pooling de conexões:

```python
# Em models/nim_client.py
async def __aenter__(self):
    await self._ensure_session()
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
    await self.close()

# Uso
async with NIMClient(config) as client:
    result = await client.complete(prompt)
```

### Etapa 4: Integração de Cache

Aplique decoradores de cache em operações caras:

```python
# Em planning/orchestrator.py
from utils.cache import cached

class CampaignOrchestrator:
    @cached(ttl_seconds=180, maxsize=100)
    async def get_campaign_templates(self, campaign_type: str) -> list:
        # Operação cara de banco de dados/consulta
        pass
    
    @cached(ttl_seconds=60, maxsize=500)
    async def get_target_intelligence(self, target: str) -> dict:
        # Operação cara de busca de inteligência de ameaças
        pass
```

### Etapa 5: Implantação com PM2

Crie a configuração de ecossistema e implante:

```bash
# Instale o PM2 globalmente
npm install -g pm2

# Crie o ecosystem.config.js (copie do acima)
# Inicie o aplicativo
pm2 start ecosystem.config.js --env production

# Monitore
pm2 monit
pm2 logs
```

## 7. Benchmarks de Performance

### Melhorias Esperadas

| Componente | Melhoria | Métrica |
|-----------|----------|---------|
| Consultas de Banco de Dados | 3-5x mais rápido | Latência de consulta reduzida de 100ms para 20-30ms |
| Requisições HTTP | 2-4x mais rápido | Estabelecimento de conexão eliminado |
| Operações em Cache | 10-100x mais rápido | Acessos de cache servidos da memória |
| Uso de Memória | Redução de 20-30% | Pooling eficiente de conexões |
| Throughput | Aumento de 3-7x | Mais requisições simultâneas tratadas |
| Latência (p95) | Redução de 40-60% | Tempos de resposta mais rápidos |

### Métricas-Chave para Monitoramento

1. **Banco de Dados**: Utilização do pool de conexões, latência de consulta
2. **HTTP**: Uso do pool de conexões, latência de requisição, taxas de retry
3. **Cache**: Razões de acerto/falta, taxas de evicção, uso de memória
4. **Aplicação**: Throughput de requisição, taxas de erro, tempos de resposta
5. **Sistema**: Uso de CPU, consumo de memória, I/O de disco

## 8. Melhores Práticas

### Pooling de Conexões

- Dimensionar os pools com base na carga de trabalho concorrente esperada
- Monitorar o esgotamento do pool e ajustar os tamanhos conforme necessário
- Sempre fechar as conexões corretamente para evitar vazamentos
- Usar validação de conexão para detectar conexões obsoletas

### Cache

- Definir valores apropriados de TTL com base na volatilidade dos dados
- Monitorar as razões de acerto de cache (alvo >80%)
- Considerar o aquecimento de cache para cargas de trabalho previsíveis
- Usar chaves de cache que representem com precisão os dados

### Compressão

- Use gzip para respostas baseadas em texto (JSON, HTML, CSS, JS)
- Considere brotli para melhores taxas de compressão (requer suporte do cliente)
- Evite comprimir dados já comprimidos (imagens, vídeos)
- Equilibre o nível de compressão com o uso de CPU

### Configuração do PM2

- Use modo cluster para aplicações Node.js para utilizar todos os núcleos de CPU
- Defina limites de memória apropriados para evitar kills por OOM
- Configure rotação de logs para evitar problemas de espaço em disco
- Use arquivos de ecossistema para implantação consistente entre ambientes
- Ative recargas sem downtime para atualizações perfeitas

## 9. Solução de Problemas

### Problemas Comuns

1. **Esgotamento do Pool de Conexões**
   - Sintoma: Aumento de latência, erros de timeout
   - Solução: Aumente o tamanho do pool, verifique vazamentos de conexão

2. **Thrashing de Cache**
   - Sintoma: Baixa razão de acerto, alta taxa de evicção
   - Solução: Aumente o tamanho do cache, ajuste o TTL, revise os padrões de acesso

3. **Vazamentos de Memória**
   - Sintoma: Aumento gradual de memória ao longo do tempo
   - Solução: Profile o uso de memória, verifique recursos não fechados

4. **Picos de CPU**
   - Sintoma: Alto uso de CPU durante compressão/descompressão
   - Solução: Ajuste os níveis de compressão, considere processamento assíncrono

### Comandos de Diagnóstico

```bash
# Verifique o status dos processos do PM2
pm2 list

# Monitore o uso de recursos
pm2 monit

# Veja os logs
pm2 logs --lines 100

# Verifique um processo individual
pm2 show <nome_do_app_or_id>

# Recarregue sem downtime
pm2 reload <nome_do_app_or_id>

# Escale para cima/baixo
pm2 scale <nome_do_app> <instâncias>
```

## Conclusão

Essas melhorias de performance e escalabilidade aumentarão significativamente a capacidade do ShadowForge Agent de lidar com cargas de trabalho de produção de forma eficiente. Ao implementar pooling de conexões, caching inteligente, estratégias de compressão e configuração adequada do PM2, o sistema será capaz de:

1. Lidar com aumento de usuários simultâneos e requisições
2. Reduzir latência e melhorar os tempos de resposta
3. Otimizar a utilização de recursos (CPU, memória, rede)
4. Fornecer melhor confiabilidade e tolerância a falhas
5. Permitir escalonamento horizontal para implantações de alta disponibilidade

A implementação segue as melhores práticas da indústria e fornece uma base sólida para escalar o ShadowForge Agent para atender às demandas de nível empresarial.