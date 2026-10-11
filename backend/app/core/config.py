import os
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    # App
    PROJECT_NAME: str = "Auralis"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
        ).split(",")
    ]
    
    # Faster-Whisper
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "tiny.en")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    
    # SER (Speech Emotion Recognition)
    SER_MODEL_TYPE: str = os.getenv("SER_MODEL_TYPE", "acoustic_prosody")
    SER_CONFIDENCE_THRESHOLD: float = float(os.getenv("SER_CONFIDENCE_THRESHOLD", "0.35"))
    
    # VAD (Voice Activity Detection)
    VAD_ENERGY_THRESHOLD: float = float(os.getenv("VAD_ENERGY_THRESHOLD", "0.012"))
    VAD_SILENCE_DURATION_MS: int = int(os.getenv("VAD_SILENCE_DURATION_MS", "600"))
    AUDIO_SAMPLE_RATE: int = 16000
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # ollama, openai, fallback
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.6"))
    
    # TTS Settings
    TTS_ENGINE: str = os.getenv("TTS_ENGINE", "edge-tts")
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-ChristopherNeural")
    TTS_RATE: str = os.getenv("TTS_RATE", "+0%")
    TTS_PITCH: str = os.getenv("TTS_PITCH", "+0Hz")
    
    # Storage
    DB_PATH: str = os.getenv("DB_PATH", "auralis.db")
    SAVE_RAW_AUDIO: bool = os.getenv("SAVE_RAW_AUDIO", "false").lower() == "true"

settings = Settings()
