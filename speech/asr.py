"""
============================================================
 NVIDIA ShadowForge Agent - ASR com Riva
 Arquivo: speech/asr.py
============================================================
 Speech-to-Text streaming com NVIDIA Riva via gRPC.
 Fallback para Whisper local se Riva indisponível.
============================================================
"""

from __future__ import annotations

import asyncio
import logging
import queue
import time
from collections.abc import Callable
from typing import Any

from core.config import ShadowForgeConfig

logger = logging.getLogger("shadowforge.speech.asr")


class TranscricaoASR:
    """Resultado de uma transcrição ASR."""

    def __init__(self, texto: str, confianca: float = 0.0,
                 is_final: bool = True, latencia_ms: float = 0.0) -> None:
        self.texto = texto
        self.confianca = confianca
        self.is_final = is_final
        self.latencia_ms = latencia_ms
        self.timestamp = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0


class RivaASR:
    """ASR streaming com NVIDIA Riva.

    Conecta ao Riva server via gRPC para transcrição
    em tempo real com latência < 250ms. Suporta VAD,
    pontuação automática e keyword detection.

    Se Riva estiver indisponível, faz fallback para
    Whisper local via openai-whisper.
    """

    def __init__(self, config: ShadowForgeConfig | None = None) -> None:
        self._config = config
        self._servidor = "localhost:50051"
        self._idioma = "pt-BR"
        self._sample_rate = 16000
        self._enable_punctuation = True
        self._enable_vad = True
        self._vad_sensibilidade = 0.5
        self._max_latencia_ms = 250
        self._running = False
        self._grpc_channel = None
        self._stub = None
        self._fila_audio: queue.Queue = queue.Queue()
        self._callbacks_transcricao: list[Callable] = []
        self._keywords = ["shadow", "forge", "recon", "exploit", "scan", "abort"]

        if config and hasattr(config, "nvidia"):
            riva_cfg = getattr(config.nvidia, "riva", None)
            if riva_cfg:
                self._servidor = getattr(riva_cfg, "servidor", self._servidor)
                if hasattr(riva_cfg, "asr"):
                    asr_cfg = riva_cfg.asr
                    self._idioma = getattr(asr_cfg, "idioma", self._idioma)
                    self._sample_rate = getattr(asr_cfg, "sample_rate", self._sample_rate)
                    self._enable_punctuation = getattr(asr_cfg, "enable_automatic_punctuation", True)
                    self._enable_vad = getattr(asr_cfg, "enable_vad", True)
                    self._vad_sensibilidade = getattr(asr_cfg, "vad_sensibilidade", 0.5)

    async def inicializar(self) -> bool:
        """Inicializa conexão com Riva server.

        Returns:
            True se conectou com sucesso
        """
        try:
            import grpc
            import nvidia.riva.proto.riva_asr_pb2 as rasr  # noqa: F401
            import nvidia.riva.proto.riva_asr_pb2_grpc as rasr_grpc
            import nvidia.riva.proto.riva_audio_pb2 as ra  # noqa: F401

            self._grpc_channel = grpc.insecure_channel(self._servidor)
            self._stub = rasr_grpc.RivaSpeechRecognitionStub(self._grpc_channel)

            # Testa conexão
            try:
                grpc.channel_ready_future(self._grpc_channel).result(timeout=5)
                logger.info("Conexão Riva ASR estabelecida: %s", self._servidor)
                return True
            except grpc.FutureTimeoutError:
                logger.warning("Riva server não disponível, usando Whisper fallback")
                self._stub = None
                return False

        except ImportError:
            logger.warning("Riva gRPC não disponível, usando Whisper fallback")
            self._stub = None
            return False

    async def transcrever_stream(self, audio_chunk: bytes) -> TranscricaoASR | None:
        """Transcreve chunk de áudio via stream.

        Args:
            audio_chunk: Chunk de áudio PCM 16-bit

        Returns:
            TranscricaoASR ou None
        """
        import time
        inicio = time.time()

        if self._stub:
            return await self._transcrever_riva(audio_chunk, inicio)
        else:
            return await self._transcrever_whisper(audio_chunk, inicio)

    async def _transcrever_riva(self, audio_chunk: bytes, inicio: float) -> TranscricaoASR | None:
        """Transcrição via Riva gRPC."""
        try:
            import nvidia.riva.proto.riva_asr_pb2 as rasr  # noqa: F401

            config = rasr.RecognitionConfig(
                encoding=rasr.RecognitionConfig.LINEAR_PCM,
                sample_rate_hertz=self._sample_rate,
                language_code=self._idioma,
                max_alternatives=1,
                enable_automatic_punctuation=self._enable_punctuation,
                enable_vad=self._enable_vad,
            )

            request = rasr.StreamingRecognizeRequest(
                audio=audio_chunk,
                config=config,
            )

            responses = self._stub.StreamingRecognize(iter([request]))

            for response in responses:
                if response.results:
                    result = response.results[0]
                    if result.alternatives:
                        alt = result.alternatives[0]
                        latencia = (time.time() - inicio) * 1000

                        return TranscricaoASR(
                            texto=alt.transcript,
                            confianca=alt.confidence,
                            is_final=result.is_final,
                            latencia_ms=latencia,
                        )

        except Exception as e:
            logger.error("Erro no Riva ASR: %s", e)
            return await self._transcrever_whisper(audio_chunk, inicio)

        return None

    async def _transcrever_whisper(self, audio_chunk: bytes, inicio: float) -> TranscricaoASR | None:
        """Fallback: transcrição via Whisper local."""
        try:
            import numpy as np
            import whisper

            if not hasattr(self, "_whisper_model"):
                self._whisper_model = whisper.load_model("base")

            # Converte bytes para array audio
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0

            resultado = self._whisper_model.transcribe(
                audio_array,
                language="pt" if "pt" in self._idioma else "en",
            )

            latencia = (time.time() - inicio) * 1000  # noqa: F821

            return TranscricaoASR(
                texto=resultado.get("text", ""),
                confianca=0.85,  # Whisper não fornece confiança
                is_final=True,
                latencia_ms=latencia,
            )

        except ImportError:
            logger.warning("Whisper não disponível")
            return None
        except Exception as e:
            logger.error("Erro no Whisper: %s", e)
            return None

    def detectar_keyword(self, transcricao: TranscricaoASR) -> str | None:
        """Verifica se uma keyword hacker foi detectada.

        Returns:
            Keyword detectada ou None
        """
        texto_lower = transcricao.texto.lower()
        for kw in self._keywords:
            if kw in texto_lower:
                return kw
        return None

    def adicionar_callback(self, callback: Callable) -> None:
        """Adiciona callback para transcrições."""
        self._callbacks_transcricao.append(callback)

    async def finalizar(self) -> None:
        """Fecha conexão Riva."""
        self._running = False
        if self._grpc_channel:
            self._grpc_channel.close()
            logger.info("Riva ASR desconectado")
