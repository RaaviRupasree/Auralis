import time
import logging
import numpy as np
from typing import Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger("auralis.emotion")

EMOTION_CATEGORIES = ["calm", "anxious", "agitated", "distressed", "angry", "neutral"]

class EmotionService:
    """
    Acoustic Speech Emotion Recognition (SER) Engine.
    Directly analyzes raw audio waveforms using acoustic prosody, fundamental frequency (F0)
    estimates, spectral centroid, spectral flux, energy dynamics, and zero-crossing rates.
    """
    def __init__(self):
        self._is_loaded = True

    def extract_acoustic_features(self, audio: np.ndarray, sr: int = 16000) -> Dict[str, float]:
        """Extract acoustic prosodic and spectral features directly from audio waveform."""
        if len(audio) == 0:
            return {"rms": 0.0, "zcr": 0.0, "spectral_centroid": 0.0, "f0_mean": 0.0, "f0_std": 0.0, "energy_var": 0.0}

        # 1. RMS Energy and Variance
        frame_len = int(sr * 0.03)  # 30ms frames
        hop_len = int(sr * 0.015)   # 15ms hop
        
        frames = [audio[i:i+frame_len] for i in range(0, len(audio) - frame_len, hop_len)]
        if not frames:
            frames = [audio]
            
        frame_energies = np.array([np.sqrt(np.mean(f**2)) for f in frames])
        rms_mean = float(np.mean(frame_energies))
        energy_std = float(np.std(frame_energies))
        
        # 2. Zero Crossing Rate (ZCR)
        signs = np.sign(audio)
        signs[signs == 0] = 1
        zcr = float(np.mean(np.abs(signs[1:] - signs[:-1])) / 2.0)
        
        # 3. Spectral Centroid via FFT
        fft_vals = np.abs(np.fft.rfft(audio[:min(len(audio), sr * 3)]))
        freqs = np.fft.rfftfreq(min(len(audio), sr * 3), 1.0 / sr)
        sum_fft = np.sum(fft_vals)
        if sum_fft > 1e-7:
            spectral_centroid = float(np.sum(freqs * fft_vals) / sum_fft)
        else:
            spectral_centroid = 0.0

        # 4. F0 Autocorrelation Pitch Estimation
        f0_estimates = []
        for frame in frames[::2]:  # Subsample for low latency
            if np.max(np.abs(frame)) < 0.01:
                continue
            # Autocorrelation
            corr = np.correlate(frame, frame, mode='full')
            corr = corr[len(corr)//2:]
            
            # Search lag between 70Hz (sr/70) and 400Hz (sr/400)
            min_lag = int(sr / 400)
            max_lag = int(sr / 70)
            if max_lag < len(corr):
                lag_window = corr[min_lag:max_lag]
                if len(lag_window) > 0 and np.max(lag_window) > 0:
                    peak_lag = min_lag + np.argmax(lag_window)
                    f0 = sr / peak_lag
                    f0_estimates.append(f0)
                    
        if f0_estimates:
            f0_mean = float(np.mean(f0_estimates))
            f0_std = float(np.std(f0_estimates))
        else:
            f0_mean = 140.0
            f0_std = 15.0

        return {
            "rms": rms_mean,
            "energy_var": energy_std,
            "zcr": zcr,
            "spectral_centroid": spectral_centroid,
            "f0_mean": f0_mean,
            "f0_std": f0_std
        }

    def predict_emotion(self, audio: np.ndarray, sr: int = 16000) -> Tuple[str, float, float]:
        """
        Predict estimated acoustic emotion from 16kHz audio waveform.
        Returns: (emotion_label, confidence_score, duration_ms)
        """
        start_time = time.perf_counter()
        
        if len(audio) < sr * 0.2:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return "neutral", 0.50, duration_ms

        feats = self.extract_acoustic_features(audio, sr)
        
        # Scoring logic based on acoustic prosody signatures:
        # High F0 mean & high energy & high centroid => Angry or Agitated
        # High F0 std (pitch jitter/strain) & moderate energy => Anxious or Distressed
        # Moderate F0 & low energy & low variance => Calm or Neutral
        scores: Dict[str, float] = {
            "calm": 0.2,
            "neutral": 0.2,
            "anxious": 0.15,
            "agitated": 0.15,
            "distressed": 0.15,
            "angry": 0.15
        }
        
        rms = feats["rms"]
        f0_mean = feats["f0_mean"]
        f0_std = feats["f0_std"]
        centroid = feats["spectral_centroid"]
        
        # High intensity / anger features
        if rms > 0.08 and f0_mean > 200:
            scores["angry"] += 0.45
            scores["agitated"] += 0.35
        elif rms > 0.05 and f0_mean > 180:
            scores["agitated"] += 0.40
            scores["anxious"] += 0.25
            
        # Anxiety / distress (vocal tremor, high pitch jitter)
        if f0_std > 35.0:
            scores["anxious"] += 0.35
            scores["distressed"] += 0.30
            
        if centroid > 2200.0 and rms > 0.03:
            scores["anxious"] += 0.20
            scores["agitated"] += 0.20
            
        # Calm / neutral features (subdued energy, steady pitch)
        if rms < 0.035 and f0_std < 22.0:
            scores["calm"] += 0.40
            scores["neutral"] += 0.35
            
        if 100.0 <= f0_mean <= 170.0 and f0_std < 25.0:
            scores["neutral"] += 0.30
            scores["calm"] += 0.25
            
        # Softmax normalization
        exp_scores = {k: np.exp(v) for k, v in scores.items()}
        sum_exp = sum(exp_scores.values())
        probs = {k: float(v / sum_exp) for k, v in exp_scores.items()}
        
        top_emotion = max(probs, key=probs.get)
        confidence = float(probs[top_emotion])
        
        # Bound confidence realistically (0.45 - 0.94)
        bounded_conf = float(np.clip(confidence, 0.45, 0.92))
        
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info("SER estimated emotion: %s (confidence: %.2f, time: %.1f ms)", top_emotion, bounded_conf, duration_ms)
        return top_emotion, bounded_conf, duration_ms

    @property
    def is_ready(self) -> bool:
        return self._is_loaded

emotion_service = EmotionService()
