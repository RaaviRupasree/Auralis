import numpy as np
import pytest
from app.services.vad_service import VADService

def test_vad_silence_detection():
    vad = VADService(sample_rate=16000, energy_threshold=0.02, silence_duration_ms=300)
    
    # 480 samples = 30ms frame
    silence_frame = np.zeros(480, dtype=np.float32)
    is_speaking, completed, audio = vad.process_chunk(silence_frame)
    
    assert not is_speaking
    assert not completed
    assert audio is None

def test_vad_speech_onset_and_eou():
    vad = VADService(sample_rate=16000, energy_threshold=0.02, silence_duration_ms=90)
    
    speech_frame = np.ones(480, dtype=np.float32) * 0.1  # Loud tone
    silence_frame = np.zeros(480, dtype=np.float32)      # Silence
    
    # Send speech frames (onset requires 2 frames)
    vad.process_chunk(speech_frame)
    is_speaking, completed, _ = vad.process_chunk(speech_frame)
    assert is_speaking is True
    assert completed is False
    
    # Send silence frames to trigger EOU (90ms = 3 frames of 30ms)
    vad.process_chunk(silence_frame)
    vad.process_chunk(silence_frame)
    is_speaking, completed, utterance = vad.process_chunk(silence_frame)
    
    assert completed is True
    assert utterance is not None
    assert len(utterance) > 0
