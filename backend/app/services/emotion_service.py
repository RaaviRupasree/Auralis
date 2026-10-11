import time
import logging
import numpy as np
from typing import Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger("auralis.emotion")

# Supported practical emotion categories for crisis negotiation simulation
EMOTION_CATEGORIES = ["calm", "anger", "fear_panic", "sadness", "neutral"]

class EmotionService:
    """
    Acoustic Speech Emotion Recognition (SER) Engine.
    Analyzes raw audio waveforms directly using acoustic prosody, fundamental frequency (F0),
    pitch variability/jitter, spectral centroid, zero-crossing rate (ZCR), and RMS dynamics.
    Predictions are explicitly treated as paralinguistic estimates.
    """
    def __init__(self):
        self._is_loaded = True

    def extract_acoustic_features(self, audio: np.ndarray, sr: int = 16000) -> Dict[str, float]:
        """Extract acoustic prosodic and spectral features directly from audio waveform."""
        if len(audio) == 0:
            return {
                "rms": 0.0,
                "zcr": 0.0,
                "spectral_centroid": 0.0,
                "f0_mean": 0.0,
                "f0_std": 0.0,
                "energy_var": 0.0
            }

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
        
        # 3. Spectral Centroid via FFT (brightness / vocal tension)
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
            corr = np.correlate(frame, frame, mode='full')
            corr = corr[len(corr)//2:]
            
            min_lag = int(sr / 400)  # 400Hz ceiling
            max_lag = int(sr / 70)   # 70Hz floor
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
        Supported labels: calm, anger, fear_panic, sadness, neutral
        """
        start_time = time.perf_counter()
        
        if len(audio) < sr * 0.2:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return "neutral", 0.50, duration_ms

        feats = self.extract_acoustic_features(audio, sr)
        rms = feats["rms"]
        f0_mean = feats["f0_mean"]
        f0_std = feats["f0_std"]
        centroid = feats["spectral_centroid"]
        
        scores: Dict[str, float] = {
            "calm": 0.20,
            "anger": 0.20,
            "fear_panic": 0.20,
            "sadness": 0.20,
            "neutral": 0.20
        }

        # 1. Anger: High RMS energy, elevated F0 mean, sharp onset dynamics, high spectral centroid
        if rms > 0.065:
            scores["anger"] += 0.45
            if f0_mean > 185.0:
                scores["anger"] += 0.35
            if centroid > 1800.0:
                scores["anger"] += 0.20

        # 2. Fear/Panic: Elevated F0 mean, extreme pitch jitter/tremor (high f0_std), high centroid
        if f0_std > 30.0:
            scores["fear_panic"] += 0.45
            if f0_mean > 190.0:
                scores["fear_panic"] += 0.35
            if centroid > 2100.0:
                scores["fear_panic"] += 0.25

        # 3. Sadness / Subdued: Low energy, depressed F0 mean, flat pitch trajectory (low f0_std), low centroid
        if rms < 0.028 and f0_mean < 130.0:
            scores["sadness"] += 0.50
            if f0_std < 15.0:
                scores["sadness"] += 0.30
            if centroid < 1400.0:
                scores["sadness"] += 0.20

        # 4. Calm: Subdued energy, steady baseline pitch, controlled modulation
        if 100.0 <= f0_mean <= 165.0 and f0_std < 22.0 and rms < 0.045:
            scores["calm"] += 0.45
            scores["neutral"] += 0.25

        # 5. Baseline / Neutral fallback
        if 0.025 <= rms <= 0.055 and 110.0 <= f0_mean <= 175.0 and f0_std < 25.0:
            scores["neutral"] += 0.35
            scores["calm"] += 0.20

        # Softmax normalization
        exp_scores = {k: np.exp(v) for k, v in scores.items()}
        sum_exp = sum(exp_scores.values())
        probs = {k: float(v / sum_exp) for k, v in exp_scores.items()}
        
        # Sort predictions
        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        top_emotion, top_prob = sorted_probs[0]
        second_prob = sorted_probs[1][1]

        # Uncertainty handling: If close tie (< 0.035 diff) or very low top probability, treat as neutral
        if (top_prob - second_prob < 0.035) or (top_prob < 0.26):
            final_emotion = "neutral"
            bounded_conf = 0.50
        else:
            final_emotion = top_emotion
            bounded_conf = float(np.clip(top_prob, 0.42, 0.92))

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "SER estimated emotion: %s (confidence: %.2f, time: %.1f ms)",
            final_emotion, bounded_conf, duration_ms
        )
        return final_emotion, bounded_conf, duration_ms

    @property
    def is_ready(self) -> bool:
        return self._is_loaded

emotion_service = EmotionService()
