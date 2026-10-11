from dataclasses import dataclass

import numpy as np
from faster_whisper.vad import get_vad_model

SAMPLE_RATE = 16000
FRAME_SAMPLE_COUNT = 512
CONTEXT_SAMPLE_COUNT = 64
END_SILENCE_SAMPLE_COUNT = SAMPLE_RATE * 800 // 1000
SPEECH_PADDING_SAMPLE_COUNT = SAMPLE_RATE * 150 // 1000
SPEECH_THRESHOLD = 0.5
SILENCE_THRESHOLD = 0.35


@dataclass
class VADFrame:
    samples: np.ndarray
    speech_active: bool
    speech_started: bool
    speech_ended: bool
    silence_sample_count: int


class StreamingSileroVAD:
    def __init__(self, model=None):
        self._model = model or get_vad_model()
        self._pending_samples = np.empty(0, dtype=np.float32)
        self._context = np.zeros((1, CONTEXT_SAMPLE_COUNT), dtype=np.float32)
        self._hidden_state = np.zeros((1, 1, 128), dtype=np.float32)
        self._cell_state = np.zeros((1, 1, 128), dtype=np.float32)
        self._speech_active = False
        self._silence_sample_count = 0

    @property
    def silence_sample_count(self):
        return self._silence_sample_count

    def process(self, samples):
        samples = np.asarray(samples, dtype=np.float32).reshape(-1)
        if self._pending_samples.size:
            samples = np.concatenate((self._pending_samples, samples))

        frame_count = samples.size // FRAME_SAMPLE_COUNT
        usable_sample_count = frame_count * FRAME_SAMPLE_COUNT
        self._pending_samples = samples[usable_sample_count:]
        frames = []

        for start in range(0, usable_sample_count, FRAME_SAMPLE_COUNT):
            frame = samples[start : start + FRAME_SAMPLE_COUNT]
            model_input = np.concatenate((self._context, frame.reshape(1, -1)), axis=1)
            probabilities, self._hidden_state, self._cell_state = (
                self._model.session.run(
                    None,
                    {
                        "input": model_input,
                        "h": self._hidden_state,
                        "c": self._cell_state,
                    },
                )
            )
            probability = float(np.asarray(probabilities).reshape(-1)[0])
            speech_started = (
                not self._speech_active and probability >= SPEECH_THRESHOLD
            )
            if speech_started:
                self._speech_active = True

            if self._speech_active:
                if probability < SILENCE_THRESHOLD:
                    self._silence_sample_count += FRAME_SAMPLE_COUNT
                else:
                    self._silence_sample_count = 0

            speech_ended = (
                self._speech_active
                and self._silence_sample_count >= END_SILENCE_SAMPLE_COUNT
            )
            frames.append(
                VADFrame(
                    samples=frame.copy(),
                    speech_active=self._speech_active,
                    speech_started=speech_started,
                    speech_ended=speech_ended,
                    silence_sample_count=self._silence_sample_count,
                )
            )

            self._context = frame[-CONTEXT_SAMPLE_COUNT:].reshape(1, -1).copy()
            if speech_ended:
                self._speech_active = False
                self._silence_sample_count = 0
                self._context.fill(0)
                self._hidden_state.fill(0)
                self._cell_state.fill(0)

        return frames
