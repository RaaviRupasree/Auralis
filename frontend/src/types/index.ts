export type SessionState =
  | 'idle'
  | 'connecting'
  | 'listening'
  | 'listening_active'
  | 'processing'
  | 'generating'
  | 'speaking'
  | 'interrupted'
  | 'disconnected'
  | 'error';

export type EmotionType =
  | 'calm'
  | 'anxious'
  | 'agitated'
  | 'distressed'
  | 'angry'
  | 'neutral';

export interface LatencyBreakdown {
  stt_duration_ms: number;
  ser_duration_ms: number;
  llm_ttft_ms: number;
  llm_total_ms: number;
  tts_ttfa_ms: number;
  tts_total_ms: number;
  total_latency_ms: number;
}

export interface ConversationTurn {
  turn_id?: string;
  turn_index: number;
  user_transcript: string;
  detected_emotion?: EmotionType;
  emotion_confidence?: number;
  ai_response: string;
  metrics: LatencyBreakdown;
  was_interrupted?: boolean;
  created_at?: string;
}

export interface SessionSummary {
  session_id: string;
  scenario: string;
  start_time: string;
  end_time?: string;
  total_turns: number;
  status: string;
  avg_latency_ms: number;
  created_at: string;
}

export interface SessionDetail {
  session: SessionSummary;
  turns: ConversationTurn[];
}

export interface AnalyticsData {
  total_sessions: number;
  total_turns: number;
  avg_latency_ms: number;
  avg_stt_ms: number;
  avg_ser_ms: number;
  avg_llm_ttft_ms: number;
  avg_tts_ttfa_ms: number;
  emotion_distribution: Record<string, number>;
  interruption_count: number;
}

export interface ModelStatus {
  whisper_ready: boolean;
  whisper_model: string;
  ser_ready: boolean;
  ser_model: string;
  llm_provider: string;
  llm_model: string;
  llm_connected: boolean;
  tts_engine: string;
  tts_voice: string;
  tts_ready: boolean;
}

export interface AppConfig {
  llm_provider: string;
  ollama_base_url: string;
  ollama_model: string;
  openai_model: string;
  openai_api_key?: string;
  has_openai_key: boolean;
  openai_key_preview: string;
  tts_engine: string;
  tts_voice: string;
  vad_energy_threshold: number;
  vad_silence_duration_ms: number;
  whisper_model_size: string;
  whisper_device: string;
}
