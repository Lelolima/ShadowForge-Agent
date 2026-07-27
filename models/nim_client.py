"""
============================================================
NVIDIA ShadowForge Agent - NIM Client
Arquivo: models/nim_client.py
============================================================
Client para NVIDIA Inference Manager (NIM) com streaming,
multi-GPU, rate limiting, quantizacao e fallback.
============================================================
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from core.config import ShadowForgeConfig

import aiohttp

logger = logging.getLogger("shadowforge.models.nim")


class NIMClient:
    """Client para inferencia via NVIDIA NIM.

    Suporta modelos Nemotron, Llama, Mistral e outros
    disponiveis via NIM com streaming de respostas,
    multi-GPU load balancing, rate limiting e fallback.

    Quando a API key retorna 403 (modelos nao ativados),
    o client opera em modo simulacao com mensagens inteligentes.
    Para ativar modelos: acesse https://build.nvidia.com/
    e clique "Try" no modelo desejado, depois "Get API Key".
    """

    # Modelos ordenados por preferencia para tentar
    MODELOS_FALLBACK = [
        "meta/llama-3.3-70b-instruct",
        "meta/llama-3.2-90b-vision-instruct",
        "meta/llama-3.1-8b-instruct",
        "meta/llama-3.2-11b-vision-instruct",
        "meta/llama-3.2-3b-instruct",
        "google/gemma-2-2b-it",
    ]

    def __init__(self, config: ShadowForgeConfig | None = None) -> None:
        import os
        self._api_key = ""
        self._base_url = "https://integrate.api.nvidia.com/v1"
        self._org_id = ""
        self._timeout = 120
        self._max_retries = 2
        self._retry_delay = 1.0
        self._modelo_ativo: str | None = None
        self._modelos_verificados: bool = False
        self._modelos_disponiveis: list[str] = []

        if config:
            self._api_key = getattr(config, "api_key", "") or ""
            self._base_url = getattr(config, "base_url", self._base_url)
            self._org_id = getattr(config, "org_id", "")

            # Resolve env vars
            if self._api_key.startswith("${"):
                var = self._api_key[2:-1]
                self._api_key = os.environ.get(var, "")

            # Tambem checa env direto se config nao forneceu
            if not self._api_key:
                self._api_key = os.environ.get("NVIDIA_API_KEY", "")

        # Verifica se API key esta configurada
        self._disponivel = bool(self._api_key and not self._api_key.startswith("nvapi-xxxxx"))
        if self._disponivel:
            logger.info("NVIDIA API Key configurada (%d chars)", len(self._api_key))
        else:
            logger.warning("NVIDIA API Key nao configurada - NIM operando em modo simulacao")

        self._session: aiohttp.ClientSession | None = None
        self._request_count = 0
        self._last_request_time = 0.0

    def disponivel(self) -> bool:
        """Retorna True se API key valida esta configurada."""
        return self._disponivel

    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtem sessao HTTP reutilizavel."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self._timeout),
            )
        return self._session

    async def chamada(
        self,
        modelo: str,
        prompt: str,
        temperatura: float = 0.5,
        max_tokens: int = 2048,
        top_p: float = 0.95,
        system_prompt: str | None = None,
    ) -> str:
        """Chamada sincrona ao NIM."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": modelo,
            "messages": messages,
            "temperature": temperatura,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": False,
        }

        return await self._executar_requisicao(payload)

    async def chamada_stream(
        self,
        modelo: str,
        prompt: str,
        temperatura: float = 0.5,
        max_tokens: int = 2048,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Chamada com streaming ao NIM. Yields tokens parciais."""
        if not self._disponivel:
            logger.debug("NIM simulacao: chamada_stream para %s", modelo)
            yield "[NIM SIMULACAO] API key nao configurada. Configure NVIDIA_API_KEY no .env"
            return

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": modelo,
            "messages": messages,
            "temperature": temperatura,
            "max_tokens": max_tokens,
            "stream": True,
        }

        session = await self._get_session()
        url = f"{self._base_url}/chat/completions"

        for attempt in range(self._max_retries):
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        async for line in resp.content:
                            line_str = line.decode("utf-8").strip()
                            if line_str.startswith("data: "):
                                data = line_str[6:]
                                if data == "[DONE]":
                                    return
                                try:
                                    chunk = json.loads(data)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                                except json.JSONDecodeError:
                                    continue
                    elif resp.status == 429:
                        wait = self._retry_delay * (2 ** attempt)
                        logger.warning("Rate limited, aguardando %.1fs", wait)
                        await asyncio.sleep(wait)
                    else:
                        error_text = await resp.text()
                        logger.error("NIM erro %d: %s", resp.status, error_text[:200])
                        raise RuntimeError(f"NIM API erro {resp.status}")
            except aiohttp.ClientError as e:
                logger.error("Erro de conexao NIM: %s", e)
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))

    async def chamada_multimodal(
        self,
        modelo: str,
        texto: str,
        imagem_base64: str,
        temperatura: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Chamada multimodal (texto + imagem) ao NIM."""
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": texto},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{imagem_base64}",
                    },
                },
            ],
        }]

        payload = {
            "model": modelo,
            "messages": messages,
            "temperature": temperatura,
            "max_tokens": max_tokens,
            "stream": False,
        }

        return await self._executar_requisicao(payload)

    async def _procurar_modelo_ativo(self) -> str | None:
        """Busca rapidamente um modelo funcional para a API key atual."""
        if self._modelo_ativo:
            return self._modelo_ativo

        if not self._disponivel:
            return None

        session = await self._get_session()

        for modelo in self.MODELOS_FALLBACK:
            try:
                payload = {
                    "model": modelo,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 3,
                    "temperature": 0.1,
                }
                async with session.post(
                    f"{self._base_url}/chat/completions", json=payload
                ) as resp:
                    if resp.status == 200:
                        self._modelo_ativo = modelo
                        self._modelos_disponiveis.append(modelo)
                        logger.info("Modelo NIM ativo: %s", modelo)
                        return modelo
                    elif resp.status == 403:
                        logger.debug("Modelo %s: 403", modelo)
                    else:
                        logger.debug("Modelo %s: erro %d", modelo, resp.status)
            except Exception as e:
                logger.debug("Modelo %s: excecao %s", modelo, str(e)[:60])

        logger.warning("Nenhum modelo NIM respondeu - modo simulacao")
        return None

    async def _executar_requisicao(self, payload: dict) -> str:
        """Executa requisicao ao NIM com retry e fallback inteligente."""
        modelo_original = payload.get("model", "unknown")

        if not self._disponivel:
            logger.debug("NIM simulacao: requisicao para %s", modelo_original)
            return self._resposta_simulada(modelo_original, payload)

        # Sempre usa modelo ativo se conhecido, senao tenta buscar
        if self._modelo_ativo:
            payload["model"] = self._modelo_ativo
        else:
            ativo = await self._procurar_modelo_ativo()
            if ativo:
                payload["model"] = ativo
            else:
                return self._resposta_simulada(modelo_original, payload)

        session = await self._get_session()
        url = f"{self._base_url}/chat/completions"

        for attempt in range(self._max_retries):
            try:
                elapsed = time.time() - self._last_request_time
                if elapsed < 0.1:
                    await asyncio.sleep(0.1 - elapsed)

                async with session.post(url, json=payload) as resp:
                    self._last_request_time = time.time()
                    self._request_count += 1

                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

                    elif resp.status == 429:
                        wait = self._retry_delay * (2 ** attempt)
                        logger.warning("Rate limited, aguardando %.1fs", wait)
                        await asyncio.sleep(wait)
                        continue

                    elif resp.status in (403, 404):
                        logger.warning("Modelo %s: erro %d, tentando fallback", payload["model"], resp.status)
                        if payload["model"] in self._modelos_disponiveis:
                            self._modelos_disponiveis.remove(payload["model"])
                        self._modelo_ativo = None
                        ativo = await self._procurar_modelo_ativo()
                        if ativo:
                            payload["model"] = ativo
                            continue
                        return self._resposta_simulada(modelo_original, payload)

                    else:
                        error_text = await resp.text()
                        logger.error("NIM erro %d: %s", resp.status, error_text[:200])
                        return self._resposta_simulada(modelo_original, payload)

            except aiohttp.ClientError as e:
                logger.error("Conexao NIM falhou (tentativa %d): %s", attempt + 1, e)
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))
                    continue
                return self._resposta_simulada(modelo_original, payload)

        return self._resposta_simulada(payload.get("model", "unknown"), payload)

    def _resposta_simulada(self, modelo: str, payload: dict) -> str:
        """Gera resposta simulada inteligente baseada no contexto da requisicao."""
        messages = payload.get("messages", [])
        user_msg = ""
        for m in messages:
            if m.get("role") == "user":
                content = m.get("content", "")
                if isinstance(content, str):
                    user_msg = content[:100]
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            user_msg = part.get("text", "")[:100]
                            break

        # Respostas contextuais simuladas por tipo de tarefa
        msg_lower = user_msg.lower() if user_msg else ""

        if any(w in msg_lower for w in ["recon", "scan", "porta", "port"]):
            return (f"[SIMULACAO NIM] Reconhecimento simulado - Modelo: {modelo}\n"
                    "Portas comuns detectadas: 22(SSH), 80(HTTP), 443(HTTPS), 3306(MySQL), 8080(Proxy)\n"
                    "Servicos: OpenSSH 8.9, Apache 2.4.54, MySQL 8.0\n"
                    "Para IA real, ative modelos em https://build.nvidia.com/")

        elif any(w in msg_lower for w in ["vuln", "exploit", "cve", "ataque"]):
            return (f"[SIMULACAO NIM] Analise de vulnerabilidade simulada - Modelo: {modelo}\n"
                    "Vulnerabilidades potenciais: CVE-2023-XXXX (SQL Injection), CVE-2023-YYYY (XSS)\n"
                    "Severidade: Media-Alta | CVSS: 6.5-8.2\n"
                    "Para IA real, ative modelos em https://build.nvidia.com/")

        elif any(w in msg_lower for w in ["report", "relatorio", "resumo"]):
            return (f"[SIMULACAO NIM] Relatorio simulado - Modelo: {modelo}\n"
                    "Campanha de pentest executada em modo simulacao.\n"
                    "Kill chain completa: RECON > SCAN > ENUM > EXPLOIT > POST > REPORT\n"
                    "Para IA real, ative modelos em https://build.nvidia.com/")

        elif any(w in msg_lower for w in ["analise", "analyze", "image", "imagem", "screenshot"]):
            return (f"[SIMULACAO NIM] Analise visual simulada - Modelo: {modelo}\n"
                    "Interface detectada: formulario de login, campos de input, botao submit\n"
                    "Elementos interativos: 3 botoes, 2 inputs, 1 dropdown\n"
                    "Para IA real, ative modelos em https://build.nvidia.com/")

        else:
            # M-11 FIX: Usar f-string consistentemente (como os outros ramos)
            prompt_preview = user_msg[:50] if user_msg else "N/A"
            return (f"[SIMULACAO NIM] Modelo: {modelo}\n"
                    f"Prompt: {prompt_preview}\n"
                    "Resposta gerada em modo simulacao.\n"
                    "Para IA real, ative modelos em https://build.nvidia.com/")

    async def verificar_saude(self) -> dict[str, Any]:
        """Verifica saude do NIM e retorna detalhes."""
        resultado = {
            "api_key_configurada": self._disponivel,
            "endpoint_acessivel": False,
            "modelo_ativo": self._modelo_ativo,
            "modelos_disponiveis": list(self._modelos_disponiveis),
            "status": "desconhecido",
        }

        if not self._disponivel:
            resultado["status"] = "sem_api_key"
            return resultado

        try:
            session = await self._get_session()
            url = f"{self._base_url}/models"
            async with session.get(url) as resp:
                resultado["endpoint_acessivel"] = resp.status == 200

            ativo = await self._procurar_modelo_ativo()
            if ativo:
                resultado["status"] = "online"
                resultado["modelo_ativo"] = self._modelo_ativo
                resultado["modelos_disponiveis"] = list(self._modelos_disponiveis)
            else:
                resultado["status"] = "sem_modelos_disponiveis"
        except Exception as e:
            resultado["status"] = f"conexao_falhou: {str(e)[:60]}"

        return resultado

    async def fechar(self) -> None:
        """Fecha sessao HTTP."""
        if self._session and not self._session.closed:
            await self._session.close()
