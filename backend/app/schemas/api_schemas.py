from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SessionCreateRequest(BaseModel):
    scenario: str = Field(default="crisis_negotiation", description="Negotiation training scenario")
    user_name: Optional[str] = "Negotiator"

class LatencyMetrics(BaseModel):
    stt_duration_ms: float = 0.0
    ser_duration_ms: float = 0.0
    llm_ttft_ms: float = 0.0
    llm_total_ms: float = 0.0
    tts_ttfa_ms: float = 0.0
    tts_total_ms: float = 0.0
    total_latency_ms: float = 0.0

class TurnRecord(BaseModel):
    turn_id: str
    session_id: str
    turn_index: int
    user_transcript: str
    detected_emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    ai_response: str
    metrics: LatencyMetrics
    was_interrupted: bool = False
    created_at: str

class SessionSummary(BaseModel):
    session_id: str
    scenario: str
    start_time: str
    end_time: Optional[str] = None
    total_turns: int
    status: str
    avg_latency_ms: float = 0.0
    created_at: str

class SessionDetailResponse(BaseModel):
    session: SessionSummary
    turns: List[TurnRecord]

class AnalyticsResponse(BaseModel):
    total_sessions: int
    total_turns: int
    avg_latency_ms: float
    avg_stt_ms: float
    avg_ser_ms: float
    avg_llm_ttft_ms: float
    avg_tts_ttfa_ms: float
    emotion_distribution: Dict[str, int]
    interruption_count: int

class WebRTCOfferRequest(BaseModel):
    sdp: str
    type: str = "offer"
    session_id: Optional[str] = None

class WebRTCAnswerResponse(BaseModel):
    sdp: str
    type: str = "answer"
    session_id: str

class ICECandidateRequest(BaseModel):
    candidate: str
    sdpMid: Optional[str] = None
    sdpMLineIndex: Optional[int] = None
    session_id: str

class ModelStatusResponse(BaseModel):
    whisper_ready: bool
    whisper_model: str
    ser_ready: bool
    ser_model: str
    llm_provider: str
    llm_model: str
    llm_connected: bool
    tts_engine: str
    tts_voice: str
    tts_ready: bool

class ConfigUpdateRequest(BaseModel):
    llm_provider: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    tts_voice: Optional[str] = None
    vad_energy_threshold: Optional[float] = None
    vad_silence_duration_ms: Optional[int] = None
