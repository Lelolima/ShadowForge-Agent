"""
============================================================
 NVIDIA ShadowForge Agent - TTS com Riva
 Arquivo: speech/tts.py
============================================================
 Text-to-Speech com NVIDIA Riva para síntese natural
 com vozes cyberpunk e streaming de baixa latência.
============================================================
"""

from __future__ import annotations

import logging
import queue
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("shadowforge.speech.tts")


class RivaTTS:
    """TTS com NVIDIA Riva.

    Sintetiza fala natural com vozes configuráveis,
    streaming para baixa latência e suporte SSML.
    Fallback para pyttsx3 local se Riva indisponível.
    """

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._servidor = "localhost:50051"
        self._idioma = "pt-BR"
        self._voz = "default"
        self._sample_rate = 22050
        self._velocidade = 1.0
        self._tom = 1.0
        self._grpc_channel = None
        self._stub = None
        self._fila_fala: queue.PriorityQueue = queue.PriorityQueue()
        self._speaking = False
        self._callbacks_fim: list[Callable] = []

        if config and hasattr(config, "nvidia"):
            riva_cfg = getattr(config.nvidia, "riva", None)
            if riva_cfg and hasattr(riva_cfg, "tts"):
                tts_cfg = riva_cfg.tts
                self._idioma = getattr(tts_cfg, "idioma", self._idioma)
                self._voz = getattr(tts_cfg, "voz", self._voz)
                self._sample_rate = getattr(tts_cfg, "sample_rate", self._sample_rate)
                self._velocidade = getattr(tts_cfg, "velocidade", self._velocidade)
                self._tom = getattr(tts_cfg, "tom", self._tom)

    async def inicializar(self) -> bool:
        """Inicializa conexão com Riva TTS server."""
        try:
            import grpc
            import nvidia.riva.proto.riva_tts_pb2 as rtts  # noqa: F401
            import nvidia.riva.proto.riva_tts_pb2_grpc as rtts_grpc

            self._grpc_channel = grpc.insecure_channel(self._servidor)
            self._stub = rtts_grpc.RivaSpeechSynthesisStub(self._grpc_channel)

            try:
                grpc.channel_ready_future(self._grpc_channel).result(timeout=5)
                logger.info("Riva TTS conectado: %s", self._servidor)
                return True
            except Exception:
                logger.warning("Riva TTS indisponível, fallback pyttsx3")
                self._stub = None
                return False

        except ImportError:
            logger.warning("Riva TTS gRPC não disponível, fallback pyttsx3")
            self._stub = None
            return False

    async def sintetizar(self, texto: str, prioridade: int = 5) -> bytes:
        """Sintetiza texto em áudio.

        Args:
            texto: Texto para sintetizar
            prioridade: Prioridade (0=crítico, 10=baixo)

        Returns:
            Bytes de áudio PCM
        """
        if self._stub:
            return await self._sintetizar_riva(texto)
        else:
            return await self._sintetizar_fallback(texto)

    async def _sintetizar_riva(self, texto: str) -> bytes:
        """Síntese via Riva gRPC."""
        try:
            import nvidia.riva.proto.riva_tts_pb2 as rtts  # noqa: F401

            request = rtts.SynthesizeSpeechRequest(
                text=texto,
                language_code=self._idioma,
                voice_name=self._voz,
                sample_rate_hz=self._sample_rate,
                audio_encoding=rtts.AudioEncoding.LINEAR_PCM,
            )

            response = self._stub.Synthesize(request)
            return response.audio

        except Exception as e:
            logger.error("Erro Riva TTS: %s", e)
            return await self._sintetizar_fallback(texto)

    async def _sintetizar_fallback(self, texto: str) -> bytes:
        """Fallback: síntese via pyttsx3."""
        try:
            import os
            import tempfile

            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", int(150 * self._velocidade))
            engine.setProperty("volume", 0.9)

            # Salva em arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name

            engine.save_to_file(texto, temp_path)
            engine.runAndWait()

            with open(temp_path, "rb") as f:
                audio = f.read()

            os.unlink(temp_path)
            return audio

        except ImportError:
            logger.warning("pyttsx3 não disponível")
            return b""
        except Exception as e:
            logger.error("Erro fallback TTS: %s", e)
            return b""

    async def falar(self, texto: str, prioridade: int = 5) -> None:
        """Sintetiza e reproduz fala.

        Args:
            texto: Texto para falar
            prioridade: Prioridade (alertas = prioridade alta)
        """
        audio = await self.sintetizar(texto, prioridade)

        if audio:
            try:
                import numpy as np
                import sounddevice as sd

                # Converte PCM para array
                audio_array = np.frombuffer(audio, dtype=np.int16)
                sd.play(audio_array, samplerate=self._sample_rate)
                sd.wait()
            except ImportError:
                logger.warning("sounddevice não disponível para reprodução")
            except Exception as e:
                logger.error("Erro na reprodução: %s", e)

    async def finalizar(self) -> None:
        """Fecha conexão TTS."""
        if self._grpc_channel:
            self._grpc_channel.close()
            logger.info("Riva TTS desconectado")
