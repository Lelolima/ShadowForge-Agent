"""
============================================================
NVIDIA ShadowForge Agent - Shell Stealth
Arquivo: control/shell.py
============================================================
Execução de comandos shell com streaming de output,
timeout automático, histórico OPSEC e suporte Win/Linux.
============================================================
"""

from __future__ import annotations

import asyncio
import logging
import platform
import shlex
import time
from collections.abc import AsyncIterator
from typing import Any

logger = logging.getLogger("shadowforge.control.shell")

# H-04 FIX: Variáveis de ambiente permitidas para override (whitelist)
_ENV_VAR_WHITELIST = frozenset({
    "PATH", "HOME", "TEMP", "TMP", "LANG", "LC_ALL", "LC_CTYPE",
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy",
    "PYTHONIOENCODING", "NMAP_ARGS", "NIKTO_ARGS",
})


def _safe_quote(text: str, is_windows: bool = False) -> str:
    """Escaping seguro de argumentos shell — POSIX e Windows.

    H-05 FIX: No Windows, dobrar aspas internas (duas aspas) em vez de barra invertida.
    """
    if not text:
        return '""'
    if is_windows:
        # Windows CMD: dobrar aspas internas para escape correto
        if '"' in text:
            return '"' + text.replace('"', '""') + '"'
        # Caracteres perigosos no cmd do Windows
        dangerous = set(' &|<>()^%!"')
        if any(c in dangerous for c in text):
            return '"' + text + '"'
        return text
    return shlex.quote(text)


class ResultadoComando:
    """Resultado de execução de comando shell."""

    def __init__(self, comando: str, returncode: int = -1,
                 stdout: str = "", stderr: str = "", timeout: bool = False) -> None:
        self.comando = comando
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.timeout = timeout
        self.duracao_s: float = 0.0

    @property
    def sucesso(self) -> bool:
        return self.returncode == 0 and not self.timeout

    def __repr__(self) -> str:
        status = "OK" if self.sucesso else "FALHA"
        return f"[{status}] {self.comando[:50]} (rc={self.returncode}, {self.duracao_s:.1f}s)"


class StealthShell:
    """Execução stealth de comandos shell.

    Suporta Windows (PowerShell, CMD) e Linux (Bash, Zsh).
    Streaming de stdout/stderr em tempo real, timeout
    automático, e histórico OPSEC para audit trail.
    """

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._timeout_default = 300
        self._stream_output = True
        self._historico: list[ResultadoComando] = []
        self._is_windows = platform.system() == "Windows"

        if config:
            ctrl = getattr(config, "controle", None)
            if ctrl and hasattr(ctrl, "shell"):
                shell_cfg = ctrl.shell
                self._timeout_default = getattr(shell_cfg, "timeout_default_s", 300)

    async def executar(
        self,
        comando: str,
        timeout: int | None = None,
        shell: str | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> ResultadoComando:
        """Executa comando shell com timeout e output streaming.

        Args:
            comando: Comando para executar
            timeout: Timeout em segundos (None = default 300s)
            shell: Shell específico (None = auto-detect)
            cwd: Diretório de trabalho
            env: Variáveis de ambiente adicionais (validadas contra whitelist)

        Returns:
            ResultadoComando com stdout, stderr e código de retorno
        """
        inicio = time.time()

        timeout_s = timeout or self._timeout_default
        resultado = ResultadoComando(comando=comando)

        # Seleciona shell
        if shell is None:
            if self._is_windows:
                executable = "powershell.exe" if "|" in comando or ";" in comando else None
            else:
                executable = "/bin/bash"
        else:
            executable = shell

        try:
            # H-04 FIX: Validar variáveis de ambiente contra whitelist
            import os
            proc_env = os.environ.copy()
            if env:
                for key, value in env.items():
                    if key in _ENV_VAR_WHITELIST:
                        proc_env[key] = value
                    else:
                        logger.warning(
                            "Variável de ambiente '%s' não permitida (não está na whitelist). "
                            "Use apenas variáveisapproved para evitar isolamento de processo.",
                            key,
                        )

            # Cria processo
            proc = await asyncio.create_subprocess_shell(
                comando,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=proc_env,
                executable=executable,
            )

            # Executa com timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout_s,
                )

                resultado.stdout = stdout_bytes.decode("utf-8", errors="replace")
                resultado.stderr = stderr_bytes.decode("utf-8", errors="replace")
                resultado.returncode = proc.returncode or 0

            except asyncio.TimeoutError:
                proc.kill()
                resultado.timeout = True
                resultado.stderr = f"Timeout após {timeout_s}s"
                logger.warning("Comando timeout: %s (%ds)", comando[:50], timeout_s)

        except FileNotFoundError as e:
            resultado.stderr = f"Comando não encontrado: {e}"
            resultado.returncode = 127
        except Exception as e:
            resultado.stderr = f"Erro: {e}"
            resultado.returncode = -1

        resultado.duracao_s = time.time() - inicio

        # Registra no histórico OPSEC
        self._historico.append(resultado)
        if len(self._historico) > 1000:
            self._historico = self._historico[-500:]

        return resultado

    async def executar_stream(self, comando: str, timeout: int | None = None) -> AsyncIterator[str]:
        """Executa comando com streaming linha-a-linha.

        H-08 FIX: Aplica timeout global (acumulado) em vez de por-linha,
        evitando que o processo rode indefinidamente produzindo linhas lentas.

        Yields cada linha de stdout conforme é produzida.
        """
        proc = await asyncio.create_subprocess_shell(
            comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        timeout_s = timeout or self._timeout_default
        deadline = time.time() + timeout_s

        try:
            while True:
                # Calcula tempo restante até o deadline global
                remaining = deadline - time.time()
                if remaining <= 0:
                    proc.kill()
                    yield f"[TIMEOUT após {timeout_s}s (global)]"
                    break

                linha = await asyncio.wait_for(
                    proc.stdout.readline(),  # type: ignore
                    timeout=max(1.0, remaining),  # Pelo menos 1s, mas respeita deadline
                )
                if not linha:
                    break
                yield linha.decode("utf-8", errors="replace").rstrip()
        except asyncio.TimeoutError:
            proc.kill()
            yield f"[TIMEOUT após {timeout_s}s (global)]"

    async def executar_nmap(self, alvo: str, argumentos: str = "-sV -sC") -> ResultadoComando:
        """Executa Nmap com argumentos padrão."""
        safe_alvo = _safe_quote(alvo, self._is_windows)
        safe_args = _safe_quote(argumentos, self._is_windows)
        cmd = f"nmap {safe_args} {safe_alvo}"
        return await self.executar(cmd, timeout=600)

    async def executar_nikto(self, alvo: str) -> ResultadoComando:
        """Executa Nikto contra URL alvo."""
        safe_alvo = _safe_quote(alvo, self._is_windows)
        cmd = f"nikto -h {safe_alvo}"
        return await self.executar(cmd, timeout=1800)

    async def executar_sqlmap(self, url: str, opcoes: str = "--batch --random-agent") -> ResultadoComando:
        """Executa SQLMap com opções éticas (batch mode)."""
        safe_url = _safe_quote(url, self._is_windows)
        safe_opcoes = _safe_quote(opcoes, self._is_windows)
        cmd = f"sqlmap -u {safe_url} {safe_opcoes}"
        return await self.executar(cmd, timeout=1800)

    async def listar_processos(self) -> list[dict[str, str]]:
        """Lista processos em execução."""
        import psutil
        processos = []
        for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent"]):
            try:
                info = proc.info  # type: ignore
                processos.append({
                    "pid": str(info.get("pid", "")),
                    "nome": str(info.get("name", "")),
                    "usuario": str(info.get("username", "")),
                    "cpu": str(info.get("cpu_percent", "")),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processos[:50]  # Limita a 50

    @property
    def historico(self) -> list[ResultadoComando]:
        """Histórico de comandos executados (OPSEC audit)."""
        return self._historico[-100:]

    async def ping(self, host: str) -> bool:
        """Verifica se host está acessível."""
        param = "-n" if self._is_windows else "-c"
        resultado = await self.executar(f"ping {param} 1 -W 3 {host}", timeout=10)
        return resultado.sucesso
