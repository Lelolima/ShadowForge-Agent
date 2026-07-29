"""
============================================================
 NVIDIA ShadowForge Agent - Compreensão Visual
 Arquivo: vision/understanding.py
============================================================
 Análise semântica de tela usando Nemotron 3 Nano Omni.
 Compreende desktop, janelas, terminais, código, UIs.
============================================================
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

from core.config import ShadowForgeConfig

logger = logging.getLogger("shadowforge.vision.understanding")


class ScreenUnderstanding:
    """Compreensão visual de tela com Nemotron multimodal.

    Analisa screenshots de desktop, terminais, browsers e
    ferramentas de segurança para tomada de decisão autônoma.
    Usa Nemotron 3 Nano Omni via NIM para inferência otimizada.
    """

    def __init__(self, config: ShadowForgeConfig | None = None) -> None:
        self._config = config
        self._nim_client = None
        self._modelo = "nvidia/nemotron-3-nano-omni-vl"
        self._temperatura = 0.3
        self._max_tokens = 2048

        if config and hasattr(config, "nvidia"):
            modelos = getattr(config.nvidia, "modelos", None)
            if modelos and hasattr(modelos, "visao"):
                self._modelo = modelos.visao.modelo
                self._temperatura = modelos.visao.temperatura
                self._max_tokens = modelos.visao.max_tokens

    async def _get_nim_client(self) -> Any:
        """Obtém client NIM lazy."""
        if self._nim_client is None:
            try:
                from models.nim_client import NIMClient
                self._nim_client = NIMClient(config=self._config.nvidia if self._config else None)
                if not self._nim_client.disponivel():
                    logger.debug("NIM sem API key - usando analise fallback")
                    return None
            except ImportError:
                logger.warning("NIMClient não disponível, modo fallback")
        return self._nim_client

    async def analisar(self, frame_data: Any, prompt_extra: str = "") -> dict[str, Any]:
        """Analisa um screenshot da tela.

        Args:
            frame_data: FrameData do vision.screen
            prompt_extra: Prompt adicional para contexto específico

        Returns:
            Dicionário com análise semântica da tela
        """
        nim = await self._get_nim_client()

        # Prepara imagem
        if hasattr(frame_data, "to_bytes"):
            img_bytes = frame_data.to_bytes("JPEG", qualidade=85)
        elif isinstance(frame_data, bytes):
            img_bytes = frame_data
        else:
            return {"erro": "formato de imagem não suportado"}

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        # Prompt de análise visual tática
        prompt = self._construir_prompt_analise(prompt_extra)

        if nim:
            try:
                resposta = await nim.chamada_multimodal(
                    modelo=self._modelo,
                    texto=prompt,
                    imagem_base64=img_b64,
                    temperatura=self._temperatura,
                    max_tokens=self._max_tokens,
                )
                return self._parsear_resposta(resposta)
            except Exception as e:
                logger.error("Erro na chamada NIM: %s", e)

        # Fallback: análise heurística
        return await self._analise_fallback(frame_data)

    async def identificar_elementos_interativos(self, frame_data: Any) -> list[dict[str, Any]]:
        """Identifica elementos UI clicáveis na tela.

        Returns:
            Lista de elementos com tipo, posição (bbox) e descrição
        """
        prompt = (
            "Analise esta captura de tela e identifique TODOS os elementos interativos: "
            "botões, links, campos de input, dropdowns, menus, checkboxes, etc. "
            "Para cada elemento, forneça: tipo, posição aproximada (x%, y%), "
            "texto/label e se parece clicável. "
            "Responda em JSON com chave 'elementos' contendo uma lista."
        )

        resultado = await self.analisar(frame_data, prompt)

        elementos = resultado.get("elementos", [])
        if not elementos and "resposta" in resultado:
            # Tenta extrair do texto da resposta
            try:
                texto = resultado["resposta"]
                if "{" in texto:
                    json_str = texto[texto.index("{"):]
                    parsed = json.loads(json_str)
                    elementos = parsed.get("elementos", [])
            except (json.JSONDecodeError, ValueError):
                pass

        return elementos

    async def detectar_ferramenta_seguranca(self, frame_data: Any) -> str | None:
        """Detecta se uma ferramenta de segurança está visível na tela.

        Returns:
            Nome da ferramenta detectada ou None
        """
        ferramentas = [
            "burp suite", "metasploit", "nmap", "wireshark",
            "sqlmap", "nikto", "hydra", "john the ripper",
            "ghidra", "ida pro", "x64dbg", "ollydbg",
            "terminal", "powershell", "cmd", "bash",
            "browser", "vscode", "sublime text",
        ]

        resultado = await self.analisar(
            frame_data,
            f"Esta captura mostra alguma ferramenta de segurança/pentest? "
            f"Responda apenas o nome da ferramenta ou 'nenhuma'. "
            f"Ferramentas conhecidas: {', '.join(ferramentas)}"
        )

        resposta = resultado.get("resposta", "").lower()
        for ft in ferramentas:
            if ft in resposta:
                return ft
        return None

    async def ler_codigo_tela(self, frame_data: Any) -> dict[str, Any]:
        """Lê e interpreta código-fonte exibido na tela."""
        resultado = await self.analisar(
            frame_data,
            "Analise o código exibido nesta tela. Identifique: linguagem de programação, "
            "trechos de código visíveis, potenciais vulnerabilidades de segurança, "
            "e qualquer informação sensível (tokens, senhas, keys). "
            "Responda em JSON com chaves: linguagem, codigo, vulnerabilidades, sensivel"
        )
        return resultado

    def _construir_prompt_analise(self, extra: str = "") -> str:
        """Constrói prompt tático para análise visual."""
        prompt = (
            "Você é o sistema de visão do SH4D0WF0RG3, um agente autônomo de pentest. "
            "Analise esta captura de tela detalhadamente:\n\n"
            "1. TIPO: Que tipo de interface é? (desktop, terminal, browser, IDE, ferramenta de segurança)\n"
            "2. CONTEÚDO: O que está visível? (código, output, formulários, dados)\n"
            "3. INTERATIVO: Quais elementos são clicáveis?\n"
            "4. RELEVANTE: Informações relevantes para pentest (IPs, URLs, erros, dados sensíveis)\n"
            "5. AÇÃO: Qual ação o agente deveria tomar? (clicar, digitar, scroll, aguardar)\n\n"
        )
        if extra:
            prompt += f"CONTEXTO ADICIONAL: {extra}\n\n"
        prompt += "Responda em JSON com chaves: tipo, conteudo, interativo, relevante, acao_sugerida"
        return prompt

    def _parsear_resposta(self, resposta: str) -> dict[str, Any]:
        """Parseia resposta do LLM em estrutura."""
        try:
            if "{" in resposta and "}" in resposta:
                json_str = resposta[resposta.index("{"):resposta.rindex("}") + 1]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass

        return {"resposta": resposta, "parseado": False}

    async def _analise_fallback(self, frame_data: Any) -> dict[str, Any]:
        """Análise heurística sem modelo de IA."""
        resultado = {
            "tipo": "desconhecido",
            "conteudo": "Análise sem modelo - NIM indisponível",
            "interativo": [],
            "relevante": [],
            "acao_sugerida": "aguardar",
        }

        # Usa OCR como fallback
        try:
            from vision.ocr import OCRExtractor
            ocr = OCRExtractor()
            if hasattr(frame_data, "imagem"):
                texto = await ocr.extrair(frame_data)
                if texto:
                    resultado["conteudo"] = texto[:500]
                    # Detecta IPs
                    import re
                    ips = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", texto)
                    if ips:
                        resultado["relevante"] = [{"tipo": "ip", "valor": ip} for ip in ips[:5]]
        except Exception as e:
            logger.debug("OCR fallback failed: %s", e)
            pass

        return resultado
