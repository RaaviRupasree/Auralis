import numpy as np
import pytest
from app.utils.audio_utils import (
    pcm_to_float32,
    float32_to_pcm,
    resample_linear,
    calculate_energy,
    calculate_db,
    create_wav_bytes,
    parse_wav_bytes
)

def test_pcm_conversions():
    # Create test sine wave
    sample_rate = 16000
    t = np.linspace(0, 1.0, sample_rate, dtype=np.float32)
    original = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    
    # Float32 -> PCM bytes -> Float32
    pcm = float32_to_pcm(original)
    assert isinstance(pcm, bytes)
    assert len(pcm) == sample_rate * 2  # 2 bytes per 16-bit sample
    
    recovered = pcm_to_float32(pcm)
    assert len(recovered) == len(original)
    assert np.allclose(original, recovered, atol=1e-3)

def test_resample_linear():
    orig_sr = 48000
    target_sr = 16000
    orig_samples = np.ones(orig_sr, dtype=np.float32)
    
    resampled = resample_linear(orig_samples, orig_sr, target_sr)
    assert len(resampled) == target_sr
    assert np.allclose(resampled, 1.0, atol=1e-3)

def test_calculate_energy_and_db():
    silence = np.zeros(1600, dtype=np.float32)
    assert calculate_energy(silence) == 0.0
    assert calculate_db(silence) == -100.0
    
    signal = np.ones(1600, dtype=np.float32) * 0.5
    assert np.isclose(calculate_energy(signal), 0.5)
    db = calculate_db(signal)
    assert -7.0 < db < -5.0  # 20 * log10(0.5) = -6.02 dB

def test_wav_pack_and_parse():
    sample_rate = 16000
    original = np.random.uniform(-0.5, 0.5, sample_rate).astype(np.float32)
    wav_bytes = create_wav_bytes(original, sample_rate)
    
    recovered, sr = parse_wav_bytes(wav_bytes)
    assert sr == sample_rate
    assert len(recovered) == len(original)
    assert np.allclose(original, recovered, atol=1e-3)
