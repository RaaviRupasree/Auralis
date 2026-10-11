import numpy as np
import pytest
from app.services.emotion_service import emotion_service, EMOTION_CATEGORIES

def test_extract_acoustic_features():
    sr = 16000
    t = np.linspace(0, 1.0, sr, dtype=np.float32)
    # 200 Hz tone
    audio = 0.1 * np.sin(2 * np.pi * 200 * t)
    
    feats = emotion_service.extract_acoustic_features(audio, sr)
    assert "rms" in feats
    assert "zcr" in feats
    assert "spectral_centroid" in feats
    assert "f0_mean" in feats
    assert feats["rms"] > 0.05
    assert 180 <= feats["f0_mean"] <= 220

def test_predict_emotion_categories_and_confidence():
    sr = 16000
    audio = np.random.uniform(-0.1, 0.1, sr).astype(np.float32)
    
    label, conf, duration_ms = emotion_service.predict_emotion(audio, sr)
    assert label in EMOTION_CATEGORIES
    assert 0.40 <= conf <= 1.0
    assert duration_ms > 0.0

def test_empty_audio_handling():
    label, conf, duration_ms = emotion_service.predict_emotion(np.array([], dtype=np.float32))
    assert label == "neutral"
    assert conf == 0.50
