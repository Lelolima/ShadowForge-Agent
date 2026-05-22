"""
============================================================
 NVIDIA ShadowForge Agent - Interface de Voz Full-Duplex
 Arquivo: speech/voice_interface.py
============================================================
 Integração ASR + TTS com loop de conversação,
 wake word detection e integração com o motor agentic.
============================================================
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from speech.asr import RivaASR
from speech.tts import RivaTTS

logger = logging.getLogger("shadowforge.speech.interface")


class VoiceInterface:
    """Interface de voz full-duplex.

    Integra ASR (Riva/Whisper) com TTS (Riva/pyttsx3)
    para conversação natural com o agente.

    Suporta:
    - Wake word detection ("shadow")
    - Modo always-listening e push-to-talk
    - Interrupção de fala (barge-in)
    - Mapeamento de comandos de voz para ações
    """

    # Comandos de voz mapeados para ações do agente
    MAPEAMENTO_COMANDOS = {
        "reconhece": {"acao": "recon", "parametros": ["alvo"]},
        "escaneia": {"acao": "scan", "parametros": ["alvo"]},
        "explora": {"acao": "exploit", "parametros": ["vulnerabilidade"]},
        "analisa": {"acao": "analyze", "parametros": ["tipo"]},
        "relatório": {"acao": "report", "parametros": []},
        "relatorio": {"acao": "report", "parametros": []},
        "status": {"acao": "status", "parametros": []},
        "parar": {"acao": "abort", "parametros": []},
        "abortar": {"acao": "abort", "parametros": []},
        "ajuda": {"acao": "help", "parametros": []},
        "stealth": {"acao": "mode_stealth", "parametros": []},
        "agressivo": {"acao": "mode_aggressive", "parametros": []},
    }

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._asr = RivaASR(config=config)
        self._tts = RivaTTS(config=config)
        self._running = False
        self._wake_word = "shadow"
        self._always_listening = False
        self._push_to_talk = True
        self._barge_in = True
        self._speaking = False
        self._on_comando: list[Callable] = []

    async def inicializar(self) -> None:
        """Inicializa ASR e TTS."""
        asr_ok = await self._asr.inicializar()
        tts_ok = await self._tts.inicializar()

        if asr_ok:
            logger.info("ASR: Riva ativo")
        else:
            logger.info("ASR: Fallback Whisper")

        if tts_ok:
            logger.info("TTS: Riva ativo")
        else:
            logger.info("TTS: Fallback pyttsx3")

    async def ouvir_comando(self) -> dict[str, Any] | None:
        """Ouve e processa um comando de voz.

        Returns:
            Dicionário com ação e parâmetros ou None
        """
        try:
            import numpy as np  # noqa: F401
            import sounddevice as sd

            # Captura áudio do microfone
            chunk_duration = 3.0  # segundos
            chunk_samples = int(self._asr._sample_rate * chunk_duration)

            audio_data = sd.rec(
                chunk_samples,
                samplerate=self._asr._sample_rate,
                channels=1,
                dtype="int16",
            )
            sd.wait()

            # Transcreve
            audio_bytes = audio_data.tobytes()
            transcricao = await self._asr.transcrever_stream(audio_bytes)

            if transcricao and transcricao.texto.strip():
                logger.info("[Voz] \"%s\" (conf: %.2f, lat: %.0fms)",
                           transcricao.texto, transcricao.confianca, transcricao.latencia_ms)

                # Verifica wake word
                keyword = self._asr.detectar_keyword(transcricao)
                if keyword == self._wake_word or self._always_listening:
                    # Parse comando
                    return self._parsear_comando(transcricao.texto)

            return None

        except ImportError:
            logger.debug("sounddevice não disponível para captura de áudio")
            return None
        except Exception as e:
            logger.debug("Erro no comando de voz: %s", e)
            return None

    def _parsear_comando(self, texto: str) -> dict[str, Any]:
        """Parseia comando de voz em ação + parâmetros."""
        texto_lower = texto.lower()

        # Remove wake word
        texto_limpo = texto_lower.replace(self._wake_word, "").strip()

        # Busca comando no mapeamento
        for keyword, mapeamento in self.MAPEAMENTO_COMANDOS.items():
            if keyword in texto_limpo:
                resultado = {
                    "acao": mapeamento["acao"],
                    "texto_original": texto,
                    "texto_limpo": texto_limpo,
                }

                # Tenta extrair parâmetros (ex: "reconhece 192.168.1.0/24")
                import re
                ip_match = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?", texto_limpo)
                if ip_match:
                    resultado["alvo"] = ip_match.group()

                return resultado

        # Comando não reconhecido
        return {
            "acao": "desconhecido",
            "texto_original": texto,
            "texto_limpo": texto_limpo,
        }

    async def responder(self, texto: str, prioridade: int = 5) -> None:
        """Responde verbalmente ao operador.

        Args:
            texto: Texto da resposta
            prioridade: Prioridade (0=alerta, 5=normal, 10=info)
        """
        if self._barge_in and self._speaking and prioridade <= 2:
            # Interrompe fala atual se prioridade alta
                logger.info("Barge-in: interrompendo fala atual")

        self._speaking = True
        await self._tts.falar(texto, prioridade)
        self._speaking = False

    async def loop_conversacao(self) -> None:
        """Loop de conversação contínuo."""
        self._running = True

        await self.responder("ShadowForge online. Aguardando comandos.", prioridade=3)

        while self._running:
            try:
                comando = await self.ouvir_comando()
                if comando and comando.get("acao") != "desconhecido":
                    # Notifica callbacks
                    for callback in self._on_comando:
                        try:
                            await callback(comando)
                        except Exception as e:
                            logger.error("Erro no callback: %s", e)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Erro no loop de voz: %s", e)
                await asyncio.sleep(1.0)

    def registrar_callback(self, callback: Callable) -> None:
        """Registra callback para comandos de voz reconhecidos."""
        self._on_comando.append(callback)

    async def finalizar(self) -> None:
        """Encerra interface de voz."""
        self._running = False
        await self._asr.finalizar()
        await self._tts.finalizar()
        logger.info("Interface de voz finalizada")
