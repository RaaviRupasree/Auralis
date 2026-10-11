from fastapi import APIRouter
from app.core.config import settings
from app.schemas.api_schemas import ConfigUpdateRequest

router = APIRouter()

@router.get("/config")
async def get_config():
    # Mask API key for security
    masked_key = ""
    if settings.OPENAI_API_KEY:
        masked_key = settings.OPENAI_API_KEY[:4] + "..." + settings.OPENAI_API_KEY[-4:] if len(settings.OPENAI_API_KEY) > 8 else "***"
        
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
        "openai_model": settings.OPENAI_MODEL,
        "has_openai_key": bool(settings.OPENAI_API_KEY),
        "openai_key_preview": masked_key,
        "tts_engine": settings.TTS_ENGINE,
        "tts_voice": settings.TTS_VOICE,
        "vad_energy_threshold": settings.VAD_ENERGY_THRESHOLD,
        "vad_silence_duration_ms": settings.VAD_SILENCE_DURATION_MS,
        "whisper_model_size": settings.WHISPER_MODEL_SIZE,
        "whisper_device": settings.WHISPER_DEVICE
    }

@router.post("/config")
async def update_config(req: ConfigUpdateRequest):
    if req.llm_provider is not None:
        settings.LLM_PROVIDER = req.llm_provider
    if req.ollama_base_url is not None:
        settings.OLLAMA_BASE_URL = req.ollama_base_url
    if req.ollama_model is not None:
        settings.OLLAMA_MODEL = req.ollama_model
    if req.openai_api_key is not None and req.openai_api_key.strip():
        settings.OPENAI_API_KEY = req.openai_api_key.strip()
    if req.openai_model is not None:
        settings.OPENAI_MODEL = req.openai_model
    if req.tts_voice is not None:
        settings.TTS_VOICE = req.tts_voice
    if req.vad_energy_threshold is not None:
        settings.VAD_ENERGY_THRESHOLD = req.vad_energy_threshold
    if req.vad_silence_duration_ms is not None:
        settings.VAD_SILENCE_DURATION_MS = req.vad_silence_duration_ms

    return {"status": "updated", "config": await get_config()}
