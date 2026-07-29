"""
============================================================
 NVIDIA ShadowForge Agent - OCR Semântico
 Arquivo: vision/ocr.py
============================================================
 Extração de texto com Tesseract + Nemotron, parsing
 de IPs, URLs, hashes, tokens e dados sensíveis.
============================================================
"""

from __future__ import annotations

import base64
import logging
import re
import base64
from typing import Any

from core.config import ShadowForgeConfig

logger = logging.getLogger("shadowforge.vision.ocr")


class ResultadoOCR:
    """Resultado estruturado do OCR."""

    def __init__(self) -> None:
        self.texto_raw: str = ""
        self.confianca_media: float = 0.0
        self.ips: list[str] = []
        self.urls: list[str] = []
        self.emails: list[str] = []
        self.hashes: list[str] = []
        self.tokens: list[str] = []
        self.numeros_porta: list[str] = []
        self.pares_chave_valor: dict[str, str] = {}
        self.dados_sensiveis: list[dict[str, str]] = []

    @property
    def tem_conteudo(self) -> bool:
        return len(self.texto_raw.strip()) > 0

    def resumo(self) -> str:
        """Resumo conciso dos dados extraídos."""
        partes = []
        if self.ips:
            partes.append(f"IPs: {len(self.ips)}")
        if self.urls:
            partes.append(f"URLs: {len(self.urls)}")
        if self.emails:
            partes.append(f"Emails: {len(self.emails)}")
        if self.hashes:
            partes.append(f"Hashes: {len(self.hashes)}")
        if self.dados_sensiveis:
            partes.append(f"Sensível: {len(self.dados_sensiveis)}")
        return " | ".join(partes) if partes else "Nenhum dado estruturado"

    def to_dict(self) -> dict[str, Any]:
        return {
            "texto_raw": self.texto_raw[:1000],
            "confianca": self.confianca_media,
            "ips": self.ips,
            "urls": self.urls,
            "emails": self.emails,
            "hashes": self.hashes,
            "tokens": self.tokens,
            "dados_sensiveis": self.dados_sensiveis,
            "pares_chave_valor": self.pares_chave_valor,
        }


class OCRExtractor:
    """OCR semântico avançado.

    Combina Tesseract para extração de texto bruto com
    Nemotron para compreensão semântica. Faz parsing
    automático de dados relevantes para pentest.
    """

    # Padrões regex para dados de pentest
    # NOTE: The following regex patterns are used to detect sensitive data in OCR output.
    # They are not hardcoded credentials but detection rules for passwords, tokens, keys, etc.
    PATTERNS = {
        "ip": re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
        "url": re.compile(
            r"https?://[^\s<>\"]+|www\.[^\s<>\"]+",
            re.IGNORECASE,
        ),
        "email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        ),
        "hash_md5": re.compile(r"\b[a-fA-F0-9]{32}\b"),
        "hash_sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
        "hash_sha1": re.compile(r"\b[a-fA-F0-9]{40}\b"),
        "token_jwt": re.compile(
            r"eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+"
        ),
        "token_bearer": re.compile(
            r"(?:Bearer|bearer)\s+[A-Za-z0-9\-._~+/]+=*",
        ),
        "api_key_aws": re.compile(
            r"AKIA[0-9A-Z]{16}"
        ),
        "porta": re.compile(
            r"\bport(?:\s*(?:|=))?\s*(\d{1,5})\b",
            re.IGNORECASE,
        ),
        "chave_valor": re.compile(
            r"([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*([^\s,;]+)"
        ),
        # Pattern to detect visible credentials in OCR text (for security scanning, not hardcoded credentials)
        "senha_visivel": re.compile(
            r"(?:password|passwd|pwd|senha|secret|token|key|api_key)"
            r"\s*[:=]\s*[^\s,;\"]+",
            re.IGNORECASE,
        ),
    }

    def __init__(self, config: ShadowForgeConfig | None = None) -> None:
        self._config = config
        self._idiomas = ["por", "eng"]
        self._psm = 6
        self._confianca_min = 60

    async def extrair(self, frame_data: Any) -> ResultadoOCR:
        """Extrai texto e dados estruturados de um screenshot.

        Args:
            frame_data: FrameData do vision.screen ou PIL Image

        Returns:
            ResultadoOCR com texto bruto e dados parseados
        """
        resultado = ResultadoOCR()

        # Obtém imagem
        imagem = None
        if hasattr(frame_data, "imagem"):
            imagem = frame_data.imagem
        elif hasattr(frame_data, "convert"):
            imagem = frame_data  # Já é PIL Image

        if imagem is None:
            return resultado

        # Tesseract OCR
        texto = self._tesseract_ocr(imagem)
        if texto:
            resultado.texto_raw = texto
            self._parsear_dados(texto, resultado)

        return resultado

    def _tesseract_ocr(self, imagem: Any) -> str:
        """Executa Tesseract OCR na imagem."""
        try:
            import pytesseract
            texto = pytesseract.image_to_string(
                imagem,
                lang="+".join(self._idiomas),
                config=f"--psm {self._psm}",
            )
            return texto.strip()
        except ImportError:
            logger.warning("pytesseract não disponível")
            return ""
        except Exception as e:
            logger.error("Erro no Tesseract: %s", e)
            return ""

    def _parsear_dados(self, texto: str, resultado: ResultadoOCR) -> None:
        """Parseia dados estruturados do texto OCR."""
        # IPs
        resultado.ips = list(set(self.PATTERNS["ip"].findall(texto)))

        # URLs
        resultado.urls = list(set(self.PATTERNS["url"].findall(texto)))

        # Emails
        resultado.emails = list(set(self.PATTERNS["email"].findall(texto)))

        # Hashes
        md5 = self.PATTERNS["hash_md5"].findall(texto)
        sha256 = self.PATTERNS["hash_sha256"].findall(texto)
        sha1 = self.PATTERNS["hash_sha1"].findall(texto)
        resultado.hashes = list(set(md5 + sha256 + sha1))

        # Tokens
        jwt = self.PATTERNS["token_jwt"].findall(texto)
        bearer = self.PATTERNS["token_bearer"].findall(texto)
        resultado.tokens = list(set(jwt + bearer))

        # Pares chave-valor
        for match in self.PATTERNS["chave_valor"].findall(texto):
            resultado.pares_chave_valor[match[0]] = match[1]

        # Dados sensíveis
        for match in self.PATTERNS["senha_visivel"].findall(texto):
            resultado.dados_sensiveis.append({
                "tipo": "credencial_visivel",
                "valor": match,
            })

        # API keys
        aws_keys = self.PATTERNS["api_key_aws"].findall(texto)
        for key in aws_keys:
            resultado.dados_sensiveis.append({
                "tipo": "aws_key",
                "valor": key,
            })

    async def extrair_regiao(
        self, frame_data: Any, x: int, y: int, w: int, h: int
    ) -> ResultadoOCR:
        """Extrai OCR de uma região específica."""
        imagem = None
        if hasattr(frame_data, "imagem"):
            imagem = frame_data.imagem.crop((x, y, x + w, y + h))
        elif hasattr(frame_data, "crop"):
            imagem = frame_data.crop((x, y, x + w, y + h))

        if imagem is None:
            return ResultadoOCR()

        return await self.extrair(imagem)

    async def extrair_terminal_output(self, frame_data: Any) -> dict[str, Any]:
        """Extrai e interpreta output de terminal (Nmap, etc.)."""
        resultado = await self.extrair(frame_data)
        texto = resultado.texto_raw

        estrutura = {
            "tipo_terminal": "desconhecido",
            "dados_estruturados": {},
        }

        # Detecta tipo de output
        if "Nmap scan report" in texto:
            estrutura["tipo_terminal"] = "nmap"
            estrutura["dados_estruturados"] = self._parsear_nmap_output(texto)
        elif "Nikto" in texto:
            estrutura["tipo_terminal"] = "nikto"
        elif "sqlmap" in texto.lower():
            estrutura["tipo_terminal"] = "sqlmap"

        estrutura["ocr"] = resultado.to_dict()
        return estrutura

    def _parsear_nmap_output(self, texto: str) -> dict[str, Any]:
        """Parseia output do Nmap.

        M-04 FIX: Agrupa portas por host em vez de criar um único host.
        Parseia por seção de host ("Nmap scan report for X").
        """
        resultado: dict[str, Any] = {"hosts": []}

        # Padrão para detectar novo host no output
        host_pattern = re.compile(r"Nmap scan report for\s+(.+?)(?:\s|\n)")
        porta_pattern = re.compile(
            r"(\d+)/tcp\s+open\s+(\S+)(?:\s+(.+))?"
        )

        # M-04 FIX: Dividir texto por seções de host
        host_sections = re.split(r"Nmap scan report for\s+", texto)

        for section in host_sections[1:]:  # Pula o texto antes do primeiro host
            # Extrair hostname/IP da seção
            host_match = re.match(r"(\S+)", section)
            host_addr = host_match.group(1) if host_match else "unknown"

            portas = []
            for match in porta_pattern.findall(section):
                portas.append({
                    "porta": int(match[0]),
                    "estado": "open",
                    "servico": match[1],
                    "versao": match[2] if match[2] else "",
                })

            if portas:
                resultado["hosts"].append({"endereco": host_addr, "portas": portas})

        # Fallback: se não encontrou seções de host, agrupa todas as portas
        if not resultado["hosts"]:
            portas = []
            for match in porta_pattern.findall(texto):
                portas.append({
                    "porta": int(match[0]),
                    "estado": "open",
                    "servico": match[1],
                    "versao": match[2] if match[2] else "",
                })
            if portas:
                resultado["hosts"].append({"portas": portas})

        return resultado
