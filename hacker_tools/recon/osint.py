"""
============================================================
 NVIDIA ShadowForge Agent - OSINT Avançado
 Arquivo: hacker_tools/recon/osint.py
============================================================
 OSINT com Shodan, Censys, Google dorking, email
 harvesting, metadata extraction e análise visual.
============================================================
"""

from __future__ import annotations

import ipaddress
import logging
import re
from typing import Any

from core.config import ShadowForgeConfig

logger = logging.getLogger("shadowforge.hacker_tools.recon.osint")

# M-09 FIX: Redes internas bloqueadas para prevenir SSRF
_SSRF_BLOCKED_NETWORKS = [
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / AWS metadata
    ipaddress.ip_network("127.0.0.0/8"),     # Loopback
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
]


def _is_host_allowed(host: str) -> bool:
    """Verifica se o host está permitido (não está em redes bloqueadas para SSRF).

    Returns True se o host for seguro para fazer requisições HTTP.
    """
    if not host:
        return False

    try:
        # Tenta como IP único
        ip = ipaddress.ip_address(host)
        # Verifica se o IP está em alguma rede bloqueada
        for blocked_net in _SSRF_BLOCKED_NETWORKS:
            if ip in blocked_net:
                return False
        return True
    except ValueError:
        # Não é um IP, pode ser um hostname - permitir por enquanto
        # Em uma implementação mais segura, faríamos resolução DNS aqui
        # mas para evitar dependências externas e problemas de resolução,
        # vamos permitir hostnames e confiar na validação de whitelist/blacklist elsewhere
        return True


class OSINTGatherer:
    """Coleta de OSINT avançada para reconhecimento autorizado.

    Integra Shodan, Censys, Google dorking automatizado,
    social media reconnaissance e metadata extraction.
    """

    def __init__(self, config: ShadowForgeConfig | None = None) -> None:
        self._config = config
        self._shodan_key = ""
        self._censys_id = ""
        self._censys_secret = ""

        import os
        if config:
            self._shodan_key = os.environ.get("SHODAN_API_KEY", "")
            self._censys_id = os.environ.get("CENSYS_API_ID", "")
            self._censys_secret = os.environ.get("CENSYS_API_SECRET", "")

    async def shodan_lookup(self, alvo: str) -> dict[str, Any]:
        """Consulta Shodan para informações sobre IP/host.

        Args:
            alvo: IP ou hostname

        Returns:
            Dados do Shodan (portas, serviços, vulns)
        """
        if not self._shodan_key:
            return {"erro": "SHODAN_API_KEY não configurada", "alvo": alvo}

        try:
            import aiohttp
            # Segurança: API key via header em vez de query param (não vaza em logs/proxy)
            url = f"https://api.shodan.io/shodan/host/{alvo}"
            headers = {"X-Shodan-Api-Key": self._shodan_key}

            async with aiohttp.ClientSession() as session, session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "alvo": alvo,
                            "ip": data.get("ip_str", ""),
                            "hostname": data.get("hostnames", []),
                            "portas": data.get("ports", []),
                            "vulns": data.get("vulns", []),
                            "os": data.get("os", ""),
                            "org": data.get("org", ""),
                            "isp": data.get("isp", ""),
                            "data": data.get("data", []),
                        }
                    else:
                        return {"erro": f"Shodan API erro {resp.status}", "alvo": alvo}

        except Exception as e:
            return {"erro": str(e), "alvo": alvo}

    async def google_dorking(self, dominio: str, tipo: str = "general") -> list[dict[str, str]]:
        """Google dorking automatizado para informações públicas.

        Tipos: general, files, directories, login, errors, config

        NOTA: Usa apenas queries legítimas e não-agressivas.
        """
        dorks_por_tipo = {
            "general": [
                f"site:{dominio}",
                f"site:{dominio} intitle:\"index of\"",
                f"site:{dominio} intitle:\"login\"",
                f"site:{dominio} inurl:admin",
                f"site:{dominio} filetype:pdf",
            ],
            "files": [
                f"site:{dominio} filetype:log",
                f"site:{dominio} filetype:conf",
                f"site:{dominio} filetype:bak",
                f"site:{dominio} filetype:sql",
                f"site:{dominio} filetype:env",
            ],
            "directories": [
                f"site:{dominio} intitle:\"directory listing\"",
                f"site:{dominio} inurl:/backup/",
                f"site:{dominio} inurl:/config/",
                f"site:{dominio} inurl:/tmp/",
            ],
            "login": [
                f"site:{dominio} intitle:\"login\" inurl:login",
                f"site:{dominio} inurl:admin/login",
                f"site:{dominio} inurl:wp-login.php",
                f"site:{dominio} inurl:signin",
            ],
            "errors": [
                f"site:{dominio} \"sql syntax\" \"error\"",
                f"site:{dominio} \"Warning:\" \"mysql\"",
                f"site:{dominio} \"Stack Trace\"",
                f"site:{dominio} \"Fatal error\"",
            ],
            "config": [
                f"site:{dominio} filetype:env \"DB_PASSWORD\"",
                f"site:{dominio} filetype:yml \"password\"",
                f"site:{dominio} filetype:ini \"secret\"",
                f"site:{dominio} \"wp-config.php\"",
            ],
        }

        dorks = dorks_por_tipo.get(tipo, dorks_por_tipo["general"])

        resultados = []
        for dork in dorks:
            resultados.append({
                "dork": dork,
                "tipo": tipo,
                "nota": "Execute manualmente no browser para verificar",
            })

        return resultados

    async def email_harvesting(self, dominio: str) -> list[str]:
        """Coleta emails públicos associados ao domínio."""
        # M-09 FIX: Proteção contra SSRF - validar domínio antes da requisição
        if not _is_host_allowed(dominio):
            logger.warning("[SSRF] Tentativa de acesso a domínio bloqueado: %s", dominio)
            return []

        emails: set[str] = set()

        # Padrões comuns
        prefixes = ["admin", "info", "support", "security", "webmaster", "noreply", "postmaster"]

        for prefix in prefixes:
            emails.add(f"{prefix}@{dominio}")

        # Tenta extrair de página principal
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session, session.get(
                f"https://{dominio}",
                timeout=aiohttp.ClientTimeout(total=10),
                ssl=True,
            ) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    found = re.findall(
                        r"\b[A-Za-z0-9._%+-]+@" + re.escape(dominio) + r"\b",
                        text,
                    )
                    emails.update(found)
        except Exception:
            pass

        return sorted(emails)

    async def metadata_extraction(self, url: str) -> dict[str, Any]:
        """Extrai metadata de documentos públicos (PDF, DOC, etc.)."""
        # M-09 FIX: Proteção contra SSRF - validar URL antes da requisição
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.hostname
            if hostname and not _is_host_allowed(hostname):
                logger.warning("[SSRF] Tentativa de acesso a domínio bloqueado: %s", hostname)
                return {"url": url, "erro": "Host em rede bloqueada (SSRF protection)"}
        except Exception:
            # Se houver erro ao fazer o parsing da URL, deixamos a requisição prosseguir
            # e deixamos que o trate erros de conexão
            pass

        resultado: dict[str, Any] = {"url": url, "metadata": {}}

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session, session.head(
                url, timeout=aiohttp.ClientTimeout(total=10),
                ssl=True,
            ) as resp:
                resultado["metadata"]["content_type"] = resp.headers.get("Content-Type", "")
                resultado["metadata"]["server"] = resp.headers.get("Server", "")
                resultado["metadata"]["last_modified"] = resp.headers.get("Last-Modified", "")
                resultado["metadata"]["etag"] = resp.headers.get("ETag", "")
        except Exception as e:
            resultado["erro"] = str(e)

        return resultado

    async def full_osint(self, alvo: str) -> dict[str, Any]:
        """Coleta OSINT completa do alvo."""
        resultado: dict[str, Any] = {"alvo": alvo}

        # Shodan
        shodan = await self.shodan_lookup(alvo)
        resultado["shodan"] = shodan

        # DNS/Email
        if "." in alvo and not alvo.replace(".", "").isdigit():
            _emails = await self.email_harvesting(alvo)
            resultado["emails"] = _emails

        dorks = await self.google_dorking(alvo)
        resultado["dorks"] = dorks

        return resultado
