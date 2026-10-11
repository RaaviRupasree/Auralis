import numpy as np
from typing import Optional, Tuple
from app.core.config import settings

class VADService:
    """
    Voice Activity Detector with pre-speech buffering, speech onset confirmation,
    and adaptive silence hang-time to prevent clipped words or jittery responses.
    """
    def __init__(
        self,
        sample_rate: int = 16000,
        energy_threshold: float = settings.VAD_ENERGY_THRESHOLD,
        silence_duration_ms: int = settings.VAD_SILENCE_DURATION_MS
    ):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_duration_ms = silence_duration_ms
        
        self.frame_ms = 30
        self.frame_size = int(sample_rate * (self.frame_ms / 1000.0))  # 480 samples
        self.silence_frames_needed = int(self.silence_duration_ms / self.frame_ms)
        self.onset_frames_needed = 2  # 60ms of speech confirms onset
        
        # Internal state
        self.is_speaking = False
        self.consecutive_speech_frames = 0
        self.consecutive_silence_frames = 0
        
        # Audio ring buffers
        self.pre_speech_buffer = []  # Keeps 250ms of audio before onset
        self.pre_speech_frames_max = int(250 / self.frame_ms)
        self.current_utterance = []

    def reset(self):
        """Reset VAD internal state."""
        self.is_speaking = False
        self.consecutive_speech_frames = 0
        self.consecutive_silence_frames = 0
        self.pre_speech_buffer.clear()
        self.current_utterance.clear()

    def process_chunk(self, audio_chunk: np.ndarray) -> Tuple[bool, bool, Optional[np.ndarray]]:
        """
        Process an incoming audio chunk.
        Returns:
            (is_active_speech, utterance_completed, complete_audio_utterance)
        """
        if len(audio_chunk) == 0:
            return self.is_speaking, False, None

        # Calculate chunk RMS energy
        rms = float(np.sqrt(np.mean(audio_chunk ** 2)))
        is_speech_frame = rms > self.energy_threshold

        utterance_completed = False
        completed_audio = None

        if is_speech_frame:
            self.consecutive_silence_frames = 0
            self.consecutive_speech_frames += 1

            if not self.is_speaking:
                if self.consecutive_speech_frames >= self.onset_frames_needed:
                    self.is_speaking = True
                    # Prepend pre-speech buffer so initial consonants are intact
                    for pre_f in self.pre_speech_buffer:
                        self.current_utterance.append(pre_f)
                    self.pre_speech_buffer.clear()
                    self.current_utterance.append(audio_chunk)
                else:
                    self._add_to_pre_buffer(audio_chunk)
            else:
                self.current_utterance.append(audio_chunk)
        else:
            self.consecutive_speech_frames = 0
            if self.is_speaking:
                self.consecutive_silence_frames += 1
                self.current_utterance.append(audio_chunk)

                if self.consecutive_silence_frames >= self.silence_frames_needed:
                    # End of utterance detected!
                    self.is_speaking = False
                    self.consecutive_silence_frames = 0
                    utterance_completed = True
                    if self.current_utterance:
                        completed_audio = np.concatenate(self.current_utterance)
                    self.current_utterance.clear()
            else:
                self._add_to_pre_buffer(audio_chunk)

        return self.is_speaking, utterance_completed, completed_audio

    def _add_to_pre_buffer(self, chunk: np.ndarray):
        self.pre_speech_buffer.append(chunk)
        if len(self.pre_speech_buffer) > self.pre_speech_frames_max:
            self.pre_speech_buffer.pop(0)
