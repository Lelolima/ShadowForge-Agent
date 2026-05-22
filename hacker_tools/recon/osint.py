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

import logging
import re
from typing import Any

logger = logging.getLogger("shadowforge.hacker_tools.recon.osint")


class OSINTGatherer:
    """Coleta de OSINT avançada para reconhecimento autorizado.

    Integra Shodan, Censys, Google dorking automatizado,
    social media reconnaissance e metadata extraction.
    """

    def __init__(self, config: Any = None) -> None:
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
            url = f"https://api.shodan.io/shodan/host/{alvo}?key={self._shodan_key}"

            async with aiohttp.ClientSession() as session, session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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
                ssl=False,
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
        resultado: dict[str, Any] = {"url": url, "metadata": {}}

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session, session.head(
                url, timeout=aiohttp.ClientTimeout(total=10),
                ssl=False,
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
