"""
============================================================
 NVIDIA ShadowForge Agent - Riva Client
 Arquivo: models/riva_client.py
============================================================
 Client para NVIDIA Riva Speech Services via gRPC
 com ASR streaming, TTS, punctuation e diarization.
============================================================
"""

from __future__ import annotations

import logging

logger = logging.getLogger("shadowforge.models.riva")


class RivaClient:
    """Client NVIDIA Riva para ASR/TTS via gRPC.

    Conecta ao Riva Speech Server para inferência
    de baixa latência de ASR e TTS.
    """

    def __init__(self, servidor: str = "localhost:50051") -> None:
        self._servidor = servidor
        self._channel = None
        self._asr_stub = None
        self._tts_stub = None
        self._connected = False

    async def conectar(self) -> bool:
        """Estabelece conexão gRPC com Riva server.

        M-10 FIX: Usa asyncio.to_thread() para evitar bloqueio síncrono
        do event loop por até 10 segundos.
        """
        try:
            import asyncio as _asyncio
            import grpc

            self._channel = grpc.insecure_channel(self._servidor)

            # M-10 FIX: Executar verificação bloqueante em thread separada
            await _asyncio.to_thread(
                grpc.channel_ready_future(self._channel).result, 10
            )
            self._connected = True

            # Inicializa stubs
            try:
                import nvidia.riva.proto.riva_asr_pb2_grpc as asr_grpc
                import nvidia.riva.proto.riva_tts_pb2_grpc as tts_grpc
                self._asr_stub = asr_grpc.RivaSpeechRecognitionStub(self._channel)
                self._tts_stub = tts_grpc.RivaSpeechSynthesisStub(self._channel)
            except ImportError:
                logger.warning("Stubs gRPC Riva não disponíveis")

            logger.info("Riva client conectado: %s", self._servidor)
            return True

        except ImportError:
            logger.warning("grpcio não disponível")
            return False
        except Exception as e:
            logger.warning("Riva server indisponível: %s", e)
            return False

    async def desconectar(self) -> None:
        """Fecha conexão gRPC."""
        if self._channel:
            self._channel.close()
            self._connected = False
            logger.info("Riva client desconectado")

    @property
    def conectado(self) -> bool:
        return self._connected
