"""
============================================================
NVIDIA ShadowForge Agent - Recon Scanner
Arquivo: hacker_tools/recon/scanner.py
============================================================
Reconhecimento automatizado com Nmap, service enumeration,
web crawling com visão e DNS enumeration.
VERIFICAÇÃO DE AUTORIZAÇÃO antes de cada scan.
============================================================
"""

from __future__ import annotations

import ipaddress
import logging
import re
import shlex
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("shadowforge.hacker_tools.recon.scanner")

# M-09 FIX: Redes internas bloqueadas para prevenir SSRF
_SSRF_BLOCKED_NETWORKS = [
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / AWS metadata
    ipaddress.ip_network("127.0.0.0/8"),     # Loopback
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
]


@dataclass
class ResultadoPorta:
    """Resultado de scan de Uma porta."""
    porta: int = 0
    protocolo: str = "tcp"
    estado: str = "open"
    servico: str = ""
    versao: str = ""
    script_output: str = ""
    cpe: str = ""


@dataclass
class ResultadoHost:
    """Resultado de scan de um host."""
    endereco: str = ""
    hostname: str = ""
    portas: list[ResultadoPorta] = field(default_factory=list)
    os_detectado: str = ""
    os_confianca: float = 0.0
    mac_address: str = ""
    latencia_ms: float = 0.0

    @property
    def portas_abertas(self) -> list[ResultadoPorta]:
        return [p for p in self.portas if p.estado == "open"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "endereco": self.endereco,
            "hostname": self.hostname,
            "os": self.os_detectado,
            "portas_abertas": [
                {"porta": p.porta, "servico": p.servico, "versao": p.versao}
                for p in self.portas_abertas
            ],
        }


class ReconScanner:
    """Reconhecimento automatizado para pentest autorizado.

    Wraps Nmap com parsing de XML output, suporte a
    múltiplos tipos de scan e verificação de autorização.
    """

    TIPOS_SCAN = {
        "syn": "-sS",
        "tcp_connect": "-sT",
        "udp": "-sU",
        "ack": "-sA",
        "fin": "-sF",
        "null": "-sN",
        "xmas": "-sX",
    }

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._nmap_path = "nmap"
        self._argumentos_default = "-sV -sC --version-intensity 5"
        self._max_threads = 10
        self._timeout_s = 600
        self._autorizado = False
        self._alvo_autorizado: str | None = None

        if config:
            ft = getattr(config, "hacker_ferramentas", None)
            if ft and hasattr(ft, "nmap"):
                nmap_cfg = ft.nmap
                self._nmap_path = getattr(nmap_cfg, "caminho", "nmap")
                self._argumentos_default = getattr(nmap_cfg, "argumentos_default", self._argumentos_default)
                self._max_threads = getattr(nmap_cfg, "max_threads", 10)
                self._timeout_s = getattr(nmap_cfg, "timeout_s", 600)

    @staticmethod
    def _is_private_ip(alvo: str) -> bool:
        """M-13 FIX: Verifica se o IP é privado usando ipaddress (RFC 1918 correto).

        Antes usava prefixos de string que eram imprecisos
        (ex: '172.2' matchava 172.200.x.x que é público).
        """
        try:
            # Tenta como IP único
            ip = ipaddress.ip_address(alvo.split("/")[0])
            return ip.is_private
        except ValueError:
            # Tenta como rede (CIDR)
            try:
                network = ipaddress.ip_network(alvo, strict=False)
                return network.is_private
            except ValueError:
                return False

    def verificar_autorizacao(self, alvo: str) -> tuple[bool, str]:
        """Verifica se o alvo está autorizado para scanning.

        Returns:
            Tupla (autorizado, motivo)
        """
        # Verifica blacklist básica
        blacklist = [
            "0.0.0.0", "127.0.0.1", "localhost",
            "224.0.0.0", "255.255.255.255",
        ]

        if alvo in blacklist:
            return False, f"Alvo {alvo} está na blacklist - não escanear"

        # M-16 FIX: IPs privados requerem confirmação explícita (não auto-autorizam)
        if self._is_private_ip(alvo):
            if self._autorizado and self._alvo_autorizado == alvo:
                return True, "Alvo privado previamente autorizado nesta sessão"
            logger.info("[RECON] Range privado detectado: %s — requer autorização explícita", alvo)
            return False, f"Range privado detectado: {alvo} — requisite autorização explícita do operador"

        # Para IPs públicos, exige confirmação explícita
        if self._alvo_autorizado and alvo == self._alvo_autorizado:
            return True, "Alvo previamente autorizado nesta sessão"

        logger.warning("ALVO NÃO VERIFICADO: %s — Requer autorização explícita!", alvo)
        return False, "ALVO PÚBLICO NÃO AUTORIZADO — Requer confirmação explícita do operador"

    async def executar_full_recon(
        self,
        alvo: str,
        tipo_scan: str = "syn",
        argumentos_extra: str = "",
        simulate: bool = False,
    ) -> dict[str, Any]:
        """Executa reconhecimento completo do alvo.

        Args:
            alvo: IP, range ou hostname
            tipo_scan: Tipo de scan Nmap
            argumentos_extra: Args adicionais
            simulate: Se True, simula sem executar

        Returns:
            Dicionário com resultados estruturados
        """
        # Verifica autorização
        autorizado, motivo = self.verificar_autorizacao(alvo)
        if not autorizado:
            return {"erro": motivo, "autorizado": False}

        logger.info("[RECON] Iniciando full recon: %s | Simulate: %s", alvo, simulate)

        if simulate:
            return self._simular_recon(alvo)

        resultado = {
            "alvo": alvo,
            "autorizado": True,
            "hosts": [],
            "erros": [],
        }

        # 1. Port Scan
        try:
            hosts = await self.port_scan(alvo, tipo_scan, argumentos_extra)
            resultado["hosts"] = [h.to_dict() for h in hosts]
        except Exception as e:
            resultado["erros"].append(f"Port scan falhou: {e}")

        # 2. DNS Enum (se hostname)
        if not alvo.replace(".", "").replace("/", "").isdigit():
            try:
                dns = await self.dns_enumeration(alvo)
                resultado["dns"] = dns
            except Exception as e:
                resultado["erros"].append(f"DNS enum falhou: {e}")

        # 3. Web Fingerprint (para portas 80/443/8080/8443)
        portas_web = [80, 443, 8080, 8443, 8000, 8888]
        for host_dict in resultado["hosts"]:
            for porta_info in host_dict.get("portas_abertas", []):
                if porta_info["porta"] in portas_web:
                    proto = "https" if porta_info["porta"] in (443, 8443) else "http"
                    url = f"{proto}://{host_dict['endereco']}:{porta_info['porta']}"
                    try:
                        web_fp = await self.web_fingerprint(url)
                        resultado.setdefault("web_fingerprints", []).append(web_fp)
                    except Exception:
                        pass

        return resultado

    async def port_scan(
        self, alvo: str, tipo: str = "syn", argumentos_extra: str = ""
    ) -> list[ResultadoHost]:
        """Executa port scan com Nmap.

        Args:
            alvo: IP/range/hostname
            tipo: Tipo de scan (syn, tcp_connect, udp, etc.)
            argumentos_extra: Argumentos adicionais

        Returns:
            Lista de ResultadoHost
        """
        flag_scan = self.TIPOS_SCAN.get(tipo, "-sS")

        # Monta comando
        cmd_parts = [
            self._nmap_path,
            flag_scan,
            self._argumentos_default,
            "-oX", "-",  # XML output para stdout
            "--max-retries", "3",
            "--host-timeout", f"{self._timeout_s // 2}s",
        ]

        if argumentos_extra:
            # C-01 FIX: whitelist de flags Nmap permitidas
            flags_permitidas = {
                "-p", "-T", "--min-rate", "--max-rate", "-Pn", "-O",
                "-sV", "-sC", "-A", "-6", "--version-intensity",
                "--script", "--open", "--top-ports", "-f",
            }
            tokens = shlex.split(argumentos_extra)
            tokens_seguros = []
            for token in tokens:
                if token.startswith("-") and token.split("=")[0] not in flags_permitidas:
                    logger.warning("[NMAP] Flag não permitida ignorada: %s", token)
                    continue
                tokens_seguros.append(shlex.quote(token))
            cmd_parts.extend(tokens_seguros)

        cmd_parts.append(shlex.quote(alvo))
        comando = " ".join(cmd_parts)

        logger.info("[NMAP] %s", comando)

        # Executa via python-nmap ou shell
        try:
            import nmap
            nm = nmap.PortScanner()
            nm.scan(alvo, arguments=" ".join(cmd_parts[1:-1]))

            hosts = []
            for host in nm.all_hosts():
                rh = ResultadoHost(endereco=host)
                rh.hostname = nm[host].hostname() or ""
                rh.os_detectado = ""

                # OS detection
                if "osmatch" in nm[host]:
                    os_matches = nm[host]["osmatch"]
                    if os_matches:
                        rh.os_detectado = os_matches[0].get("name", "")
                        rh.os_confianca = os_matches[0].get("accuracy", 0) / 100.0

                # Portas
                for proto in nm[host].all_protocols():
                    for porta, info in nm[host][proto].items():
                        rp = ResultadoPorta(
                            porta=porta,
                            protocolo=proto,
                            estado=info.get("state", "unknown"),
                            servico=info.get("name", ""),
                            versao=info.get("version", ""),
                        )
                        rh.portas.append(rp)

                hosts.append(rh)

            return hosts

        except ImportError:
            # Fallback: executa Nmap via shell e parse XML
            return await self._nmap_shell_fallback(comando)

    async def _nmap_shell_fallback(self, comando: str) -> list[ResultadoHost]:
        """Fallback: executa Nmap via shell e parseia XML output."""
        from control.shell import StealthShell
        shell = StealthShell()

        resultado = await shell.executar(comando, timeout=self._timeout_s)
        if not resultado.sucesso:
            logger.error("Nmap falhou: %s", resultado.stderr)
            return []

        return self._parsear_nmap_xml(resultado.stdout)

    def _parsear_nmap_xml(self, xml_output: str) -> list[ResultadoHost]:
        """Parseia output XML do Nmap."""
        hosts = []
        try:
            root = ET.fromstring(xml_output)
            for host_elem in root.findall(".//host"):
                if host_elem.get("status", {}).get("state") != "up":
                    continue

                rh = ResultadoHost()

                # Endereço
                addr_elem = host_elem.find("address[@addrtype='ipv4']")
                if addr_elem is not None:
                    rh.endereco = addr_elem.get("addr", "")

                # Hostname
                hostnames = host_elem.find("hostnames")
                if hostnames is not None:
                    hn = hostnames.find("hostname")
                    if hn is not None:
                        rh.hostname = hn.get("name", "")

                # OS
                os_elem = host_elem.find("os")
                if os_elem is not None:
                    osmatch = os_elem.find("osmatch")
                    if osmatch is not None:
                        rh.os_detectado = osmatch.get("name", "")
                        rh.os_confianca = float(osmatch.get("accuracy", "0")) / 100.0

                # Portas
                ports_elem = host_elem.find("ports")
                if ports_elem is not None:
                    for port_elem in ports_elem.findall("port"):
                        state = port_elem.find("state")
                        service = port_elem.find("service")

                        rp = ResultadoPorta(
                            porta=int(port_elem.get("portid", "0")),
                            protocolo=port_elem.get("protocol", "tcp"),
                            estado=state.get("state", "unknown") if state is not None else "unknown",
                            servico=service.get("name", "") if service is not None else "",
                            versao=service.get("version", "") if service is not None else "",
                        )
                        rh.portas.append(rp)

                hosts.append(rh)

        except ET.ParseError as e:
            logger.error("Erro parsing XML Nmap: %s", e)

        return hosts

    async def dns_enumeration(self, dominio: str) -> dict[str, Any]:
        """Enumeration DNS para subdomínios e records."""
        from control.shell import StealthShell
        shell = StealthShell()

        resultado_dns: dict[str, Any] = {
            "dominio": dominio,
            "records": {},
            "subdominios": [],
        }

        # DNS lookup básico
        safe_dominio = shlex.quote(dominio)
        res = await shell.executar(f"nslookup {safe_dominio}", timeout=15)
        if res.sucesso:
            ips = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", res.stdout)
            resultado_dns["records"]["A"] = list(set(ips))

        # MX records
        res = await shell.executar(f"nslookup -type=MX {safe_dominio}", timeout=15)
        if res.sucesso:
            resultado_dns["records"]["MX"] = res.stdout.strip()

        # TXT records
        res = await shell.executar(f"nslookup -type=TXT {safe_dominio}", timeout=15)
        if res.sucesso:
            resultado_dns["records"]["TXT"] = res.stdout.strip()

        # Reverse DNS
        for ip in resultado_dns["records"].get("A", [])[:3]:
            safe_ip = shlex.quote(ip)
            res = await shell.executar(f"nslookup {safe_ip}", timeout=10)
            if res.sucesso and "name =" in res.stdout:
                match = re.search(r"name = (.+)", res.stdout)
                if match:
                    resultado_dns["records"]["PTR"] = match.group(1).strip(".")

        return resultado_dns

    async def web_fingerprint(self, url: str) -> dict[str, Any]:
        """Fingerprinting de serviço web.

        M-09 FIX: Valida URL contra SSRF (metadata endpoints, redes internas).
        """
        # M-09 FIX: Verificar se o host da URL não é um endpoint de metadata/internal
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.hostname
            if hostname:
                try:
                    ip = ipaddress.ip_address(hostname)
                    for blocked_net in _SSRF_BLOCKED_NETWORKS:
                        if ip in blocked_net:
                            logger.warning("[SSRF] URL bloqueada: %s (host em rede bloqueada: %s)", url, blocked_net)
                            return {"url": url, "erro": f"Host em rede bloqueada (SSRF protection): {blocked_net}"}
                except ValueError:
                    pass  # hostname não é IP direto (pode ser DNS), permitir
        except Exception:
            pass

        resultado: dict[str, Any] = {"url": url, "tecnologias": [], "headers": {}}

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session, session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=15),
                ssl=False,
            ) as resp:
                resultado["status_code"] = resp.status
                resultado["headers"] = dict(resp.headers)

                # Tecnologia detection por headers
                server = resp.headers.get("Server", "")
                if server:
                    resultado["tecnologias"].append(f"Server: {server}")

                powered = resp.headers.get("X-Powered-By", "")
                if powered:
                    resultado["tecnologias"].append(f"X-Powered-By: {powered}")

                # Body analysis (primeiros 5KB)
                body = await resp.text()
                body_sample = body[:5000]

                # WordPress
                if "wp-content" in body_sample or "wp-includes" in body_sample:
                    resultado["tecnologias"].append("WordPress")

                # Django
                if "csrfmiddlewaretoken" in body_sample:
                    resultado["tecnologias"].append("Django")

                # ASP.NET
                if "__VIEWSTATE" in body_sample:
                    resultado["tecnologias"].append("ASP.NET")

                # React
                if "data-reactroot" in body_sample or "_next" in body_sample:
                    resultado["tecnologias"].append("React/Next.js")

        except ImportError:
            resultado["erro"] = "aiohttp não disponível"
        except Exception as e:
            resultado["erro"] = str(e)

        return resultado

    def _simular_recon(self, alvo: str) -> dict[str, Any]:
        """Simula reconhecimento (modo simulação)."""
        return {
            "alvo": alvo,
            "autorizado": True,
            "simulado": True,
            "hosts": [{
                "endereco": alvo.split("/")[0] if "/" in alvo else alvo,
                "hostname": "simulated.target.local",
                "os": "Linux Ubuntu 22.04",
                "portas_abertas": [
                    {"porta": 22, "servico": "ssh", "versao": "OpenSSH 8.9"},
                    {"porta": 80, "servico": "http", "versao": "Apache 2.4.54"},
                    {"porta": 443, "servico": "https", "versao": "nginx 1.22"},
                    {"porta": 3306, "servico": "mysql", "versao": "MySQL 5.7.38"},
                    {"porta": 8080, "servico": "http-proxy", "versao": "Tomcat 9.0"},
                ],
            }],
            "dns": {"A": [alvo.split("/")[0]] if "/" in alvo else [alvo]},
            "web_fingerprints": [{"url": f"http://{alvo}", "tecnologias": ["WordPress 6.2", "PHP 8.1"]}],
        }
