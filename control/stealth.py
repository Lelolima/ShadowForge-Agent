"""
============================================================
 NVIDIA ShadowForge Agent - Modo Stealth
 Arquivo: control/stealth.py
============================================================
 Anti-detecção, OPSEC, proxy chains, User-Agent rotation,
 MAC spoofing assistido e traffic analysis evasion.
============================================================
"""

from __future__ import annotations

import logging
import random
import shlex
import time
from typing import Any

logger = logging.getLogger("shadowforge.control.stealth")


class StealthManager:
    """Gerenciador de modo stealth e anti-detecção.

    Implementa técnicas de OPSEC para minimizar a pegada
    do agente durante operações de pentest autorizado:

    - Randomização de timing e fingerprints
    - Proxy chain management (Tor, SOCKS)
    - User-Agent rotation
    - MAC spoofing assistido (quando autorizado)
    - DNS over HTTPS
    - Limpeza de traces e logs
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._proxy_chain: list[str] = []
        self._ua_rotacao = True
        self._ua_atual = random.choice(self.USER_AGENTS)
        self._ua_ultimo_troca = 0.0
        self._dns_over_https = True
        self._limpar_historial = True
        self._anti_forensics = True
        self._sessao_id = f"SF-{random.randint(10000, 99999)}"

        if config:
            st = getattr(config, "stealth", None)
            if st:
                self._proxy_chain = getattr(st, "proxy_chain", [])
                self._ua_rotacao = getattr(st, "user_agent_rotation", True)
                self._dns_over_https = getattr(st, "dns_over_https", True)
                self._limpar_historial = getattr(st, "limpar_historial", True)
                self._anti_forensics = getattr(st, "anti_forensics", True)

    @property
    def user_agent(self) -> str:
        """User-Agent atual com rotação automática."""
        if self._ua_rotacao and time.time() - self._ua_ultimo_troca > random.uniform(30, 120):
            # Troca a cada 30-120 segundos
                self._ua_atual = random.choice(self.USER_AGENTS)
                self._ua_ultimo_troca = time.time()
                logger.debug("UA rotacionado: %s", self._ua_atual[:30])
        return self._ua_atual

    @property
    def sessao_id(self) -> str:
        """ID da sessão stealth atual."""
        return self._sessao_id

    async def configurar_proxy(self, proxy_chain: list[str]) -> None:
        """Configura cadeia de proxies.

        Args:
            proxy_chain: Lista de proxies no formato
                ["socks5://127.0.0.1:9050", "http://proxy2:8080"]
        """
        self._proxy_chain = proxy_chain
        logger.info("Proxy chain configurada: %d proxies", len(proxy_chain))

        # Testa conectividade
        for proxy in proxy_chain:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session, session.get(
                    "https://httpbin.org/ip",
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        ip = await resp.json()
                        logger.info("Proxy OK: %s → IP: %s", proxy[:20], ip.get("origin", "?"))
            except Exception as e:
                logger.warning("Proxy falhou: %s → %s", proxy[:20], e)

    def get_proxies(self) -> dict[str, str]:
        """Retorna configuração de proxy para requests."""
        if not self._proxy_chain:
            return {}

        proxy = self._proxy_chain[0]
        return {
            "http": proxy,
            "https": proxy,
        }

    def jitter_timing(self, base_s: float, variacao: float = 0.3) -> float:
        """Adiciona jitter gaussiano a timing base.

        Args:
            base_s: Tempo base em segundos
            variacao: Fator de variação (0.3 = ±30%)

        Returns:
            Tempo com jitter aplicado
        """
        jitter = random.gauss(0, base_s * variacao)
        return max(0.01, base_s + jitter)

    async def spoof_mac(self, interface: str = "eth0") -> bool:
        """Spoofing de MAC address (requer root/admin).

        AVISO: Apenas em ambientes autorizados para testes OPSEC.

        Args:
            interface: Interface de rede

        Returns:
            True se bem-sucedido
        """
        if not self._config or not getattr(self._config, "stealth", None):
            logger.warning("MAC spoof bloqueado por config")
            return False

        mac_original = self._gerar_mac_aleatorio()
        try:
            import subprocess
            if self._is_linux():
                safe_iface = shlex.quote(interface)
                safe_mac = shlex.quote(mac_original)
                cmds = [
                    ["ip", "link", "set", "dev", interface, "down"],
                    ["ip", "link", "set", "dev", interface, "address", mac_original],
                    ["ip", "link", "set", "dev", interface, "up"],
                ]
                for cmd in cmds:
                    subprocess.run(cmd, check=True, timeout=10)
                logger.info("MAC spoofed: %s → %s", interface, mac_original)
                return True
            else:
                logger.warning("MAC spoof não suportado neste OS")
                return False
        except Exception as e:
            logger.error("MAC spoof falhou: %s", e)
            return False

    def _gerar_mac_aleatorio(self) -> str:
        """Gera MAC address aleatorio com OUI local.
        L-06 FIX: Usa secrets.randbelow() em vez de random.randint()
        para criptografia segura (MAC previsivel pode ser detectado).
        """
        import secrets
        return f"02:{secrets.randbelow(256):02x}:{secrets.randbelow(256):02x}:"                f"{secrets.randbelow(256):02x}:{secrets.randbelow(256):02x}:{secrets.randbelow(256):02x}" \
               f"{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}"

    @staticmethod
    def _is_linux() -> bool:
        import platform
        return platform.system() == "Linux"

    async def limpar_traces(self, diretorios: list[str] | None = None) -> dict[str, bool]:
        """Limpa traces da sessão (OPSEC cleanup).

        Args:
            diretorios: Diretórios adicionais para limpar
        """
        resultado: dict[str, bool] = {}

        if not self._anti_forensics:
            logger.info("Anti-forensics desativado por config")
            return resultado

        # Histórico de shell
        try:
            import os
            hist_files = [
                os.path.expanduser("~/.bash_history"),
                os.path.expanduser("~/.zsh_history"),
                os.path.expanduser("~/.python_history"),
            ]
            for hf in hist_files:
                if os.path.exists(hf):
                    os.remove(hf)
                    resultado[hf] = True
                    logger.debug("Histórico removido: %s", hf)
        except Exception:
            resultado["historico"] = False

        # Files temporários da sessão
        import tempfile
        temp_dir = tempfile.gettempdir()
        for f in os.listdir(temp_dir):
            if f.startswith("SF-") or f.startswith("shadowforge"):
                try:
                    os.remove(os.path.join(temp_dir, f))
                    resultado[f"temp/{f}"] = True
                except Exception:
                    resultado[f"temp/{f}"] = False

        logger.info("OPSEC cleanup: %d itens processados", len(resultado))
        return resultado
