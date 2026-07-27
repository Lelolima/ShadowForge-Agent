"""
============================================================
 NVIDIA ShadowForge Agent - Utilitários de Áudio
 Arquivo: speech/audio_utils.py
============================================================
 Configuração de microfone/speaker, normalização,
 noise reduction, resampling e wrappers de áudio.
============================================================
"""

from __future__ import annotations

import logging
import wave

import numpy as np

logger = logging.getLogger("shadowforge.speech.audio_utils")


class AudioConfig:
    """Configuração de dispositivo de áudio."""

    def __init__(
        self,
        sample_rate: int = 16000,
        canais: int = 1,
        chunk_size: int = 1024,
        formato: str = "int16",
    ) -> None:
        self.sample_rate = sample_rate
        self.canais = canais
        self.chunk_size = chunk_size
        self.formato = formato
        self.dispositivo_entrada: int | None = None
        self.dispositivo_saida: int | None = None

    @property
    def bytes_por_amostra(self) -> int:
        """Bytes por sample baseado no formato."""
        tamanhos = {"int16": 2, "int32": 4, "float32": 4, "float64": 8}
        return tamanhos.get(self.formato, 2)

    @property
    def dtype_numpy(self) -> str:
        """Tipo numpy correspondente ao formato."""
        mapa = {"int16": np.int16, "int32": np.int32, "float32": np.float32, "float64": np.float64}
        return mapa.get(self.formato, np.int16)


def normalizar_audio(audio: np.ndarray, target_db: float = -3.0) -> np.ndarray:
    """Normaliza nível de áudio para target dB.

    Args:
        audio: Array numpy do áudio
        target_db: Nível alvo em dB (-3.0 = rock solid)

    Returns:
        Áudio normalizado
    """
    if audio.size == 0:
        return audio

    # Calcula RMS atual
    rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))

    if rms < 1e-10:
        return audio  # Silêncio, não normaliza

    # Target RMS para o dB desejado
    target_rms = 10 ** (target_db / 20.0) * (32768 if audio.dtype == np.int16 else 1.0)
    ganho = target_rms / rms

    # Aplica ganho com clipping protection
    audio_float = audio.astype(np.float64) * ganho

    # Clip ao range válido
    if audio.dtype == np.int16:
        audio_float = np.clip(audio_float, -32768, 32767)
        return audio_float.astype(np.int16)
    elif audio.dtype == np.int32:
        audio_float = np.clip(audio_float, -2147483648, 2147483647)
        return audio_float.astype(np.int32)
    else:
        return audio_float.astype(audio.dtype)


def reduzir_ruido(
    audio: np.ndarray,
    sample_rate: int = 16000,
    forca: float = 0.7,
) -> np.ndarray:
    """Redução de ruído simples via spectral gating.

    Args:
        audio: Array de áudio
        sample_rate: Sample rate
        forca: Força da redução (0.0-1.0)

    Returns:
        Áudio com ruído reduzido
    """
    try:
        import noisereduce as nr
        return nr.reduce_noise(
            y=audio.astype(np.float32),
            sr=sample_rate,
            prop_decrease=forca,
        ).astype(audio.dtype)
    except ImportError:
        logger.debug("noisereduce não disponível, pulando redução de ruído")
        return audio


def resample(
    audio: np.ndarray,
    orig_rate: int,
    target_rate: int,
) -> np.ndarray:
    """Resample áudio para nova sample rate.

    Args:
        audio: Array de áudio
        orig_rate: Sample rate original
        target_rate: Sample rate alvo

    Returns:
        Áudio resampled
    """
    if orig_rate == target_rate:
        return audio

    try:
        from scipy.signal import resample as scipy_resample
        num_amostras = int(len(audio) * target_rate / orig_rate)
        return scipy_resample(audio, num_amostras).astype(audio.dtype)
    except ImportError:
        # Fallback: interpolação linear simples
        duracao = len(audio) / orig_rate
        num_amostras = int(duracao * target_rate)
        indices = np.linspace(0, len(audio) - 1, num_amostras)
        return np.interp(indices, np.arange(len(audio)), audio.astype(np.float64)).astype(audio.dtype)


def salvar_wav(
    audio: np.ndarray,
    caminho: str,
    sample_rate: int = 22050,
    canais: int = 1,
) -> None:
    """Salva array numpy como arquivo WAV.

    Args:
        audio: Array de áudio (int16)
        caminho: Caminho do arquivo
        sample_rate: Sample rate
        canais: Número de canais
    """
    with wave.open(caminho, "wb") as wf:
        wf.setnchannels(canais)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())


def carregar_wav(caminho: str) -> tuple[np.ndarray, int]:
    """Carrega arquivo WAV para array numpy.

    Returns:
        Tuplo (array_audio, sample_rate)
    """
    with wave.open(caminho, "rb") as wf:
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        audio_bytes = wf.readframes(n_frames)
        audio = np.frombuffer(audio_bytes, dtype=np.int16)
    return audio, sample_rate


async def capturar_microfone(
    duracao_s: float = 5.0,
    sample_rate: int = 16000,
    canais: int = 1,
) -> np.ndarray:
    """Captura áudio do microfone por duração especificada.

    Args:
        duracao_s: Duração em segundos
        sample_rate: Sample rate
        canais: Canais

    Returns:
        Array numpy do áudio capturado (int16)
    """
    try:
        import sounddevice as sd

        n_amostras = int(duracao_s * sample_rate)
        audio = sd.rec(
            n_amostras,
            samplerate=sample_rate,
            channels=canais,
            dtype="int16",
        )
        sd.wait()

        if canais == 1 and audio.ndim > 1:
            audio = audio.flatten()

        return audio

    except ImportError:
        logger.warning("sounddevice não disponível para captura de áudio")
        return np.array([], dtype=np.int16)
    except Exception as e:
        logger.error("Erro na captura de microfone: %s", e)
        return np.array([], dtype=np.int16)


async def reproduzir_audio(
    audio: np.ndarray,
    sample_rate: int = 22050,
) -> None:
    """Reproduz array de áudio no speaker.

    Args:
        audio: Array numpy (int16)
        sample_rate: Sample rate
    """
    try:
        import sounddevice as sd
        sd.play(audio, samplerate=sample_rate)
        sd.wait()
    except ImportError:
        logger.warning("sounddevice não disponível para reprodução")
    except Exception as e:
        logger.error("Erro na reprodução: %s", e)


def detectar_silencio(
    audio: np.ndarray,
    threshold_db: float = -40.0,
    frame_duracao_s: float = 0.03,
    sample_rate: int = 16000,
) -> list[tuple[int, int]]:
    """Detecta segmentos de silêncio no áudio.

    Args:
        audio: Array de áudio
        threshold_db: Threshold em dB para considerar silêncio
        frame_duracao_s: Duração de cada frame de análise
        sample_rate: Sample rate

    Returns:
        Lista de (inicio_amostra, fim_amostra) dos segmentos silenciosos
    """
    frame_size = int(frame_duracao_s * sample_rate)
    threshold_linear = 10 ** (threshold_db / 20.0) * 32768

    silencios = []
    em_silencio = False
    inicio_silencio = 0

    for i in range(0, len(audio) - frame_size, frame_size):
        frame = audio[i:i + frame_size]
        rms = np.sqrt(np.mean(frame.astype(np.float64) ** 2))

        if rms < threshold_linear and not em_silencio:
            em_silencio = True
            inicio_silencio = i
        elif rms >= threshold_linear and em_silencio:
            em_silencio = False
            silencios.append((inicio_silencio, i))

    if em_silencio:
        silencios.append((inicio_silencio, len(audio)))

    return silencios
