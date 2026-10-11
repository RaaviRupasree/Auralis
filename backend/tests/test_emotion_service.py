import numpy as np
import pytest
from app.services.emotion_service import emotion_service, EMOTION_CATEGORIES

def test_extract_acoustic_features():
    sr = 16000
    t = np.linspace(0, 1.0, sr, dtype=np.float32)
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

def test_specific_acoustic_profiles():
    sr = 16000
    t = np.linspace(0, 1.0, sr, dtype=np.float32)

    # 1. High energy, high pitch -> anger
    anger_audio = 0.15 * np.sin(2 * np.pi * 240 * t)
    label_anger, _, _ = emotion_service.predict_emotion(anger_audio, sr)
    assert label_anger in ["anger", "fear_panic"]

    # 2. Low energy, low flat pitch -> sadness
    sad_audio = 0.015 * np.sin(2 * np.pi * 105 * t)
    label_sad, _, _ = emotion_service.predict_emotion(sad_audio, sr)
    assert label_sad in ["sadness", "neutral"]

    # 3. Steady, moderate pitch, calm energy -> calm
    calm_audio = 0.035 * np.sin(2 * np.pi * 140 * t)
    label_calm, _, _ = emotion_service.predict_emotion(calm_audio, sr)
    assert label_calm in ["calm", "neutral"]
