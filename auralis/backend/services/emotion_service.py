import logging
import os
from dataclasses import dataclass
from threading import Lock

import numpy as np

from services.vad_service import SAMPLE_RATE

logger = logging.getLogger(__name__)

EMOTION_MODEL = os.getenv(
    "EMOTION_MODEL",
    "superb/wav2vec2-base-superb-er",
)

_pipeline = None
_pipeline_lock = Lock()
_inference_lock = Lock()


@dataclass(frozen=True)
class EmotionPrediction:
    label: str
    confidence: float


def get_emotion_pipeline():
    global _pipeline

    if _pipeline is None:
        with _pipeline_lock:
            if _pipeline is None:
                from transformers import pipeline

                logger.info("Loading Wav2Vec2 emotion model %s", EMOTION_MODEL)
                _pipeline = pipeline(
                    "audio-classification",
                    model=EMOTION_MODEL,
                    device=-1,
                )

    return _pipeline


def classify_emotion(audio_samples: np.ndarray) -> EmotionPrediction:
    if audio_samples.size == 0:
        raise ValueError("Cannot classify an empty speech segment.")

    classifier = get_emotion_pipeline()
    with _inference_lock:
        predictions = classifier(
            {
                "raw": np.asarray(audio_samples, dtype=np.float32),
                "sampling_rate": SAMPLE_RATE,
            }
        )

    if not predictions:
        raise RuntimeError("The emotion model returned no predictions.")

    prediction = max(predictions, key=lambda item: item["score"])
    return EmotionPrediction(
        label=str(prediction["label"]),
        confidence=float(prediction["score"]),
    )
