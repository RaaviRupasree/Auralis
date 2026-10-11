import io
import wave
import numpy as np
from typing import Tuple

def pcm_to_float32(pcm_bytes: bytes) -> np.ndarray:
    """Convert 16-bit signed PCM audio bytes to float32 numpy array (-1.0 to 1.0)."""
    if not pcm_bytes:
        return np.array([], dtype=np.float32)
    int16_arr = np.frombuffer(pcm_bytes, dtype=np.int16)
    return int16_arr.astype(np.float32) / 32768.0

def float32_to_pcm(audio_arr: np.ndarray) -> bytes:
    """Convert float32 numpy array to 16-bit signed PCM audio bytes."""
    clipped = np.clip(audio_arr, -1.0, 1.0)
    int16_arr = (clipped * 32767.0).astype(np.int16)
    return int16_arr.tobytes()

def resample_linear(audio: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """Resample 1D float32 audio array to target sample rate using linear interpolation."""
    if orig_sr == target_sr or len(audio) == 0:
        return audio
    duration = len(audio) / orig_sr
    target_length = int(duration * target_sr)
    if target_length <= 0:
        return np.array([], dtype=np.float32)
    orig_indices = np.linspace(0, len(audio) - 1, num=len(audio))
    target_indices = np.linspace(0, len(audio) - 1, num=target_length)
    return np.interp(target_indices, orig_indices, audio).astype(np.float32)

def calculate_energy(audio: np.ndarray) -> float:
    """Calculate Root Mean Square (RMS) energy of audio."""
    if len(audio) == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio ** 2)))

def calculate_db(audio: np.ndarray) -> float:
    """Calculate decibel level (dBFS) of audio array."""
    rms = calculate_energy(audio)
    if rms < 1e-7:
        return -100.0
    return float(20.0 * np.log10(rms))

def create_wav_bytes(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
    """Pack float32 audio array into standard 16-bit mono WAV bytes."""
    pcm = float32_to_pcm(audio)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()

def parse_wav_bytes(wav_bytes: bytes) -> Tuple[np.ndarray, int]:
    """Parse WAV bytes into float32 audio array and sample rate."""
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_frames = wf.readframes(n_frames)
        
        if sampwidth == 2:
            int_data = np.frombuffer(raw_frames, dtype=np.int16)
            float_data = int_data.astype(np.float32) / 32768.0
        elif sampwidth == 1:
            uint_data = np.frombuffer(raw_frames, dtype=np.uint8)
            float_data = (uint_data.astype(np.float32) - 128.0) / 128.0
        else:
            int_data = np.frombuffer(raw_frames, dtype=np.int16)
            float_data = int_data.astype(np.float32) / 32768.0
            
        if n_channels > 1:
            float_data = float_data.reshape(-1, n_channels).mean(axis=1)
            
        return float_data, sample_rate
