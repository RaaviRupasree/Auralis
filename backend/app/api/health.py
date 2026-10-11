from fastapi import APIRouter
from app.services.stt_service import stt_service
from app.services.emotion_service import emotion_service
from app.services.llm_service import llm_service
from app.services.tts_service import tts_service
from app.core.config import settings
from app.schemas.api_schemas import ModelStatusResponse

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@router.get("/health/models", response_model=ModelStatusResponse)
async def model_status():
    llm_connected = await llm_service.check_health()
    return ModelStatusResponse(
        whisper_ready=stt_service.is_ready,
        whisper_model=settings.WHISPER_MODEL_SIZE,
        ser_ready=emotion_service.is_ready,
        ser_model=settings.SER_MODEL_TYPE,
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else settings.OPENAI_MODEL,
        llm_connected=llm_connected,
        tts_engine=settings.TTS_ENGINE,
        tts_voice=settings.TTS_VOICE,
        tts_ready=tts_service.is_ready
    )
