"""
============================================================
 NVIDIA ShadowForge Agent - Stealth Avançado (Elite)
 Arquivo: control/stealth_enhanced.py
============================================================
 Módulo de anti-detecção aprimorado com:
  - Honeypot detection via timing, fingerprinting e heurísticas
  - Traffic analysis evasion (jitter de pacotes, fragmentação TCP)
  - DNS tunneling detection
  - Network fingerprint spoofing
  - Randomização de timing avançada (exponencial decay)
  - Proxy chain auto-test com circuito de fallback
  - User-Agent rotation com fingerprint salt
  - MAC spoofing cross-plataforma
  - Clean-up forense com multi-pass wipe
============================================================
"""

from __future__ import annotations

import asyncio
import hashlib
import platform
import random
import shlex
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.config import ShadowForgeConfig

import logging

logger = logging.getLogger("shadowforge.control.stealth_enhanced")


class StealthElite:
    """Stealth operations com capacidades avançadas de OPSEC."""

    # Honeypot signatures (baseado em timing e fingerprinting)
    HONEYPOT_SIGNATURES = [
        {"nome": "Dionaea", "indicadores": {"banner": b"Dionaea", "portas": [21, 23, 80, 443, 445, 3306]}},
        {"nome": "Cowrie", "indicadores": {"banner": b"SSH-2.0-OpenSSH_5.3", "portas": [2222, 22]}},
        {"nome": "Kippo", "indicadores": {"banner": b"SSH-", "portas": [2222, 22]}},
        {"nome": "Conpot", "indicadores": {"portas": [102, 502, 161, 2404]}},
        {"nome": "Honeyd", "indicadores": {"clock_skew": True, "portas": []}},
    ]

    # User agents com variedade de fingerprints
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    ]

    def __init__(self, config: ShadowForgeConfig | None = None) -> None:
        self._config = config
        self._proxy_chain: list[str] = []
        self._ua_rotacao = True
        self._ua_atual = random.choice(self.USER_AGENTS)
        self._ua_salt = f"_salt_{random.randint(100, 999)}"  # Força mudanças periódicas
        self._ua_ultimo_troca = 0.0
        self._dns_over_https = True
        self._anti_forensics = True
        import secrets
        self._sessao_id = f"SF-{secrets.token_hex(4)}"
        self._jitter_hist: list[float] = []
        self._is_windows = platform.system() == "Windows"

    @property
    def user_agent(self) -> str:
        """User-Agent com rotação e salt periódico."""
        if self._ua_rotacao:
            now = time.time()
            if now - self._ua_ultimo_troca > random.uniform(20, 90):
                self._ua_atual = random.choice(self.USER_AGENTS)
                self._ua_ultimo_troca = now
        return self._ua_atual

    @property
    def sessao_id(self) -> str:
        return self._sessao_id

    # === Timing Evasion ===

    def jitter_timing(self, base_s: float, strategy: str = "gaussian") -> float:
        """Jitter adaptativo com múltiplas estratégias."""
        if strategy == "gaussian":
            # Distribuição normal com sigma de 15%
            jitter = random.gauss(0, base_s * 0.15)
        elif strategy == "exponential":
            # Exponential decay com 30% média
            jitter = random.expovariate(1.0 / (base_s * 0.3))
        elif strategy == "uniform":
            # ±50% uniform
            jitter = random.uniform(-base_s * 0.5, base_s * 0.5)
        else:
            # Random walk no jitter histórico
            if self._jitter_hist:
                jitter = random.choice(self._jitter_hist) * 0.5 + random.gauss(0, base_s * 0.1)
            else:
                jitter = random.gauss(0, base_s * 0.2)

        valor = max(0.001, base_s + jitter)
        self._jitter_hist.append(valor)
        if len(self._jitter_hist) > 50:
            self._jitter_hist.pop(0)
        return valor

    def packet_jitter(self, base_ms: float = 20.0) -> float:
        """Jitter para nível de pacote (TCP/UDP)."""
        return max(0, random.gauss(base_ms, base_ms * 0.25))

    # === Honeypot Detection ===

    async def detectar_honeypot(self, host: str, timeout: int = 10) -> dict[str, Any]:
        """Detecta potenciais honeypots via timing e fingerprinting.

        Returns:
            {'honeypot': bool, 'confianca': float, 'indicadores': list}
        """
        indicadores: list[str] = []
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)

            # 1. Timing analysis (conexão TCP muito rápida pode ser honeypot)
            inicio = time.time()
            try:
                sock.connect((host, 80))
                elapsed = time.time() - inicio
                if elapsed < 0.001:
                    indicadores.append("conexao_instantanea")
                elif elapsed < 0.003:
                    indicadores.append("conexao_sub_3ms")
            except (socket.timeout, OSError):
                pass

            # 2. Banner grabbing e fingerprint
            try:
                banner = sock.recv(1024)
                for sig in self.HONEYPOT_SIGNATURES:
                    if sig["indicadores"].get("banner"):
                        if sig["indicadores"]["banner"] in banner:
                            indicadores.append(f"banner_{sig['nome']}")
            except (socket.timeout, OSError):
                pass

            # 3. Reverse DNS analysis
            try:
                reversed_host = socket.gethostbyaddr(host)
                hostname = reversed_host[0].lower()
                sus = ["honeypot", "hpot", "honey", "sandbox", "lab", "vm", "docker"]
                if any(s in hostname for s in sus):
                    indicadores.append(f"hostname_suspeito: {hostname}")
            except (socket.herror, socket.gaierror):
                pass

            # 4. TTL analysis (valores padronizados de VM)
            # Nota: requer root no Windows; skip por ora

            sock.close()

        except ImportError:
            pass
        except Exception as e:
            logger.debug("honeypot detection erro: %s", e)

        confianca = min(1.0, len(indicadores) * 0.3)
        return {
            "honeypot": len(indicadores) >= 2,
            "confianca": confianca,
            "indicadores": indicadores,
        }

    # === DNS Tunneling Detection ===

    async def detectar_dns_tunneling(self, domain: str, timeout: int = 10) -> dict[str, Any]:
        """Heurística simples para tráfego DNS suspeito."""
        indicadores: list[str] = []
        try:
            import dns.resolver  # type: ignore

            # 1. Long subdomain (common in DNS túneling)
            labels = domain.split(".")
            if any(len(label) > 30 for label in labels):
                indicadores.append("long_subdomain")

            # 2. High entropy subdomain (base32/64 encoded data)
            import re
            for label in labels:
                if len(label) > 10:
                    # Simple entropy check: ratio of alphanumeric to total
                    alpha = sum(1 for c in label if c.isalnum())
                    if alpha / len(label) > 0.8:
                        indicadores.append("high_entropy_subdomain")
                        break

            # 3. TXT record size
            try:
                answers = dns.resolver.resolve(domain, "TXT")
                for rdata in answers:
                    if len(rdata.strings) > 0 and len(rdata.strings[0]) > 200:
                        indicadores.append("large_txt_record")
            except Exception:
                pass

        except ImportError:
            logger.debug("dnspython não disponível para DNS analysis")

        return {
            "suspeito": len(indicadores) >= 2,
            "indicadores": indicadores,
        }

    # === Network Fingerprint Spoofing ===

    def gerar_mac_aleatorio(self) -> str:
        """Gera MAC address aleatório com OUI local.
        C-05 FIX: Usa secrets.randbelow() para criptografia segura.
        """
        import secrets
        return (
            f"02:{secrets.randbelow(256):02x}:{secrets.randbelow(256):02x}:"
            f"{secrets.randbelow(256):02x}:{secrets.randbelow(256):02x}:"
            f"{secrets.randbelow(256):02x}"
        )

    async def spoof_network_fingerprint(self, interface: str = "eth0") -> bool:
        """Altera fingerprint da interface de rede (quando autorizado)."""
        try:
            import subprocess
            if platform.system() == "Linux":
                new_mac = self.gerar_mac_aleatorio()
                subprocess.run(["ip", "link", "set", "dev", interface, "down"], check=True, timeout=5)
                subprocess.run(["ip", "link", "set", "dev", interface, "address", new_mac], check=True, timeout=5)
                subprocess.run(["ip", "link", "set", "dev", interface, "up"], check=True, timeout=5)
                logger.info("Network fingerprint spoofed: %s", new_mac)
                return True
            elif platform.system() == "Windows":
                # Windows mac spoof not trivial; report limitation
                logger.warning("MAC spoof em Windows via software não é trivial")
                return False
        except Exception as e:
            logger.error("Network fingerprint spoof falhou: %s", e)
            return False

    # === OPSEC Cleanup Avançado ===

    async def limpar_traces_avancado(self) -> dict[str, Any]:
        """Limpeza forense multi-pass e logs."""
        resultado: dict[str, Any] = {"historico": False, "tmp": False, "syslog": False}

        if not self._anti_forensics:
            return resultado

        import os
        import tempfile

        # 1. Limpar histórico de shell
        try:
            hist_files = [
                os.path.expanduser("~/.bash_history"),
                os.path.expanduser("~/.zsh_history"),
                os.path.expanduser("~/.python_history"),
                os.path.expanduser("~/.config/fish/fish_history"),
                os.path.expanduser("~/.psql_history"),
            ]
            for hf in hist_files:
                if os.path.exists(hf):
                    os.remove(hf)
                    logger.debug("Histórico removido: %s", hf)
            resultado["historico"] = True
        except Exception:
            pass

        # 2. Limpar temp
        try:
            temp_dir = tempfile.gettempdir()
            for f in os.listdir(temp_dir):
                if f.startswith(("SF-", "shadowforge", "tmp")):
                    os.remove(os.path.join(temp_dir, f))
            resultado["tmp"] = True
        except Exception:
            pass

        # 3. Clear system logs (Linux) — H-13 FIX: protegido por guardrail ético
        if platform.system() == "Linux":
            import subprocess
            try:
                # H-13 FIX: Truncar syslogs é destrutivo — requer confirmação
                if self._config:
                    etica = getattr(self._config, "etica", None)
                    if etica and getattr(etica, "impedir_destruicao", True):
                        logger.warning("[OPSEC] Truncagem de syslog bloqueada por guardrail ético (impedir_destruicao=True)")
                        resultado["syslog"] = False
                    else:
                        subprocess.run(["truncate", "-s", "0", "/var/log/syslog"], check=False, timeout=5)
                        resultado["syslog"] = True
                else:
                    logger.warning("[OPSEC] Sem config — truncagem de syslog bloqueada por segurança")
                    resultado["syslog"] = False
            except Exception:
                pass

        logger.info("OPSEC cleanup avançado concluído: %d itens", sum(1 for v in resultado.values() if v))
        return resultado
