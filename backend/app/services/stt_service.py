import time
import logging
import numpy as np
from typing import Tuple, Optional
from faster_whisper import WhisperModel
from app.core.config import settings

logger = logging.getLogger("auralis.stt")

class STTService:
    def __init__(self):
        self.model: Optional[WhisperModel] = None
        self._is_loaded = False
        
    def load_model(self):
        """Lazy load Faster-Whisper model with CPU optimizations."""
        if self._is_loaded:
            return
        try:
            logger.info(
                "Loading Faster-Whisper model: %s on %s (%s)",
                settings.WHISPER_MODEL_SIZE,
                settings.WHISPER_DEVICE,
                settings.WHISPER_COMPUTE_TYPE
            )
            self.model = WhisperModel(
                settings.WHISPER_MODEL_SIZE,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
                cpu_threads=4,
                num_workers=1
            )
            self._is_loaded = True
            logger.info("Faster-Whisper model loaded successfully.")
        except Exception as e:
            logger.error("Failed to load Faster-Whisper model: %s", str(e), exc_info=True)
            self._is_loaded = False
            raise

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Tuple[str, float]:
        """
        Transcribe 16kHz float32 audio numpy array.
        Returns: (transcript_text, duration_in_ms)
        """
        if not self._is_loaded:
            self.load_model()
            
        if len(audio_data) < sample_rate * 0.2:  # Less than 200ms
            return "", 0.0
            
        start_time = time.perf_counter()
        
        try:
            # Faster-whisper accepts 1D float32 numpy array sampled at 16kHz
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=1,
                language="en",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400)
            )
            
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text.strip())
                
            full_text = " ".join(transcript_parts).strip()
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            
            logger.info("Transcribed (%d samples, %.1f ms): '%s'", len(audio_data), duration_ms, full_text)
            return full_text, duration_ms
        except Exception as e:
            logger.error("Transcription error: %s", str(e))
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return "", duration_ms

    @property
    def is_ready(self) -> bool:
        return self._is_loaded and self.model is not None

stt_service = STTService()
