import logging
import os
from threading import Lock

import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

_model = None
_model_lock = Lock()


def get_whisper_model():
    global _model

    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info(
                    "Loading Faster-Whisper model %s on %s (%s)",
                    WHISPER_MODEL,
                    WHISPER_DEVICE,
                    WHISPER_COMPUTE_TYPE,
                )
                _model = WhisperModel(
                    WHISPER_MODEL,
                    device=WHISPER_DEVICE,
                    compute_type=WHISPER_COMPUTE_TYPE,
                )

    return _model


def transcribe_samples(audio_samples):
    if audio_samples.size == 0:
        return ""

    model = get_whisper_model()
    segments, _ = model.transcribe(audio_samples, beam_size=1)
    return " ".join(segment.text.strip() for segment in segments).strip()