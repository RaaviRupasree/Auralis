import time
import asyncio
import uuid
import logging
from typing import Optional, Dict, Any, Callable, List
import numpy as np

from app.services.stt_service import stt_service
from app.services.emotion_service import emotion_service
from app.services.vad_service import VADService
from app.services.llm_service import llm_service
from app.services.tts_service import tts_service
from app.core.database import get_db_connection
from app.utils.audio_utils import calculate_energy, calculate_db

logger = logging.getLogger("auralis.pipeline")

class PipelineSession:
    def __init__(self, session_id: str, event_callback: Optional[Callable[[Dict[str, Any]], Any]] = None):
        self.session_id = session_id
        self.event_callback = event_callback
        self.vad = VADService()
        self.conversation_history: List[Dict[str, str]] = []
        self.turn_index = 0
        
        # State tracking: idle, listening, processing, generating, speaking, interrupted, error
        self.state = "listening"
        self.current_task: Optional[asyncio.Task] = None
        self.is_ai_speaking = False
        self.is_interrupted = False

    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit real-time pipeline event to connected frontend."""
        payload = {
            "type": event_type,
            "session_id": self.session_id,
            "timestamp": time.time(),
            **data
        }
        if self.event_callback:
            try:
                if asyncio.iscoroutinefunction(self.event_callback):
                    await self.event_callback(payload)
                else:
                    self.event_callback(payload)
            except Exception as e:
                logger.error("Error in event callback: %s", str(e))

    async def handle_audio_chunk(self, chunk: np.ndarray):
        """
        Ingest incoming microphone audio chunk (float32, 16kHz).
        """
        # Calculate real-time RMS for client visualizer
        rms = calculate_energy(chunk)
        db = calculate_db(chunk)

        # 1. Full-Duplex Interruption Check
        if self.is_ai_speaking and rms > (self.vad.energy_threshold * 1.3):
            logger.info("INTERRUPTION DETECTED! Trainee spoke while AI was speaking.")
            await self.interrupt_ai()

        # 2. VAD processing
        is_speech, utterance_completed, full_utterance = self.vad.process_chunk(chunk)

        # Emit VAD state periodically for frontend indicator
        if is_speech and self.state == "listening":
            self.state = "listening_active"
            await self.emit_event("vad_active", {"is_speaking": True, "db": db})
        elif not is_speech and self.state == "listening_active":
            self.state = "listening"
            await self.emit_event("vad_active", {"is_speaking": False, "db": db})

        # 3. If utterance completed, trigger end-of-utterance processing
        if utterance_completed and full_utterance is not None:
            if len(full_utterance) >= 16000 * 0.3:  # At least 300ms
                self.current_task = asyncio.create_task(self.process_utterance(full_utterance))

    async def interrupt_ai(self):
        """Immediately abort active LLM generation, TTS synthesis, or audio playback."""
        self.is_interrupted = True
        self.is_ai_speaking = False
        self.state = "interrupted"
        
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
            self.current_task = None
            
        await self.emit_event("interrupted", {
            "message": "AI speech interrupted by user speech",
            "turn_index": self.turn_index
        })
        self.vad.reset()
        self.state = "listening"

    async def process_utterance(self, audio: np.ndarray):
        """
        Execute full end-to-end conversation workflow upon end-of-utterance.
        """
        eou_timestamp = time.perf_counter()
        self.turn_index += 1
        turn_id = str(uuid.uuid4())
        self.is_interrupted = False
        
        try:
            self.state = "processing"
            await self.emit_event("state_change", {"state": "processing", "turn_index": self.turn_index})

            # STAGE A: Faster-Whisper Transcription & Acoustic SER (run concurrently for speed)
            stt_task = asyncio.to_thread(stt_service.transcribe, audio)
            ser_task = asyncio.to_thread(emotion_service.predict_emotion, audio)
            
            (transcript, stt_ms), (emotion, confidence, ser_ms) = await asyncio.gather(stt_task, ser_task)
            
            if not transcript or len(transcript.strip()) == 0:
                logger.info("Empty transcript from utterance, returning to listening.")
                self.state = "listening"
                await self.emit_event("state_change", {"state": "listening"})
                return

            await self.emit_event("transcription", {
                "turn_index": self.turn_index,
                "transcript": transcript,
                "stt_duration_ms": stt_ms,
                "detected_emotion": emotion,
                "emotion_confidence": confidence,
                "ser_duration_ms": ser_ms
            })

            # STAGE B: Context-Aware LLM Response Generation
            self.state = "generating"
            await self.emit_event("state_change", {"state": "generating"})
            
            ai_text, llm_ttft_ms, llm_total_ms = await llm_service.generate_response(
                user_transcript=transcript,
                detected_emotion=emotion,
                emotion_confidence=confidence,
                history=self.conversation_history
            )

            await self.emit_event("llm_response", {
                "turn_index": self.turn_index,
                "response_text": ai_text,
                "llm_ttft_ms": llm_ttft_ms,
                "llm_total_ms": llm_total_ms
            })

            # STAGE C: Neural TTS Synthesis and Audio Streaming
            self.state = "speaking"
            self.is_ai_speaking = True
            await self.emit_event("state_change", {"state": "speaking"})

            audio_bytes, tts_ttfa_ms, tts_total_ms = await tts_service.synthesize_full(ai_text, emotion)

            # End of utterance to first audio latency
            total_eou_to_audio_ms = (time.perf_counter() - eou_timestamp) * 1000.0

            # Emit synthesized audio payload
            import base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            await self.emit_event("audio_output", {
                "turn_index": self.turn_index,
                "audio_base64": audio_b64,
                "audio_mime": "audio/mp3",
                "tts_ttfa_ms": tts_ttfa_ms,
                "tts_total_ms": tts_total_ms,
                "total_latency_ms": total_eou_to_audio_ms
            })

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": transcript})
            self.conversation_history.append({"role": "assistant", "content": ai_text})

            # STAGE D: Persist Turn & Latency Measurements to SQLite
            await self._persist_turn(
                turn_id=turn_id,
                turn_index=self.turn_index,
                user_transcript=transcript,
                detected_emotion=emotion,
                emotion_confidence=confidence,
                ai_response=ai_text,
                stt_ms=stt_ms,
                ser_ms=ser_ms,
                llm_ttft_ms=llm_ttft_ms,
                llm_total_ms=llm_total_ms,
                tts_ttfa_ms=tts_ttfa_ms,
                tts_total_ms=tts_total_ms,
                total_latency_ms=total_eou_to_audio_ms,
                was_interrupted=self.is_interrupted
            )

        except asyncio.CancelledError:
            logger.info("Turn %d cancelled due to interruption.", self.turn_index)
            self.is_interrupted = True
        except Exception as e:
            logger.error("Pipeline failure in turn %d: %s", self.turn_index, str(e), exc_info=True)
            self.state = "error"
            await self.emit_event("error", {"error": str(e), "turn_index": self.turn_index})
        finally:
            self.is_ai_speaking = False
            self.state = "listening"
            await self.emit_event("state_change", {"state": "listening"})

    async def _persist_turn(
        self,
        turn_id: str,
        turn_index: int,
        user_transcript: str,
        detected_emotion: str,
        emotion_confidence: float,
        ai_response: str,
        stt_ms: float,
        ser_ms: float,
        llm_ttft_ms: float,
        llm_total_ms: float,
        tts_ttfa_ms: float,
        tts_total_ms: float,
        total_latency_ms: float,
        was_interrupted: bool
    ):
        try:
            async with get_db_connection() as db:
                await db.execute(
                    """
                    INSERT INTO conversation_turns (
                        turn_id, session_id, turn_index, user_transcript, detected_emotion,
                        emotion_confidence, ai_response, stt_duration_ms, ser_duration_ms,
                        llm_ttft_ms, llm_total_ms, tts_ttfa_ms, tts_total_ms, total_latency_ms,
                        was_interrupted
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        turn_id, self.session_id, turn_index, user_transcript, detected_emotion,
                        emotion_confidence, ai_response, stt_ms, ser_ms, llm_ttft_ms,
                        llm_total_ms, tts_ttfa_ms, tts_total_ms, total_latency_ms, 1 if was_interrupted else 0
                    )
                )
                await db.execute(
                    """
                    UPDATE sessions
                    SET total_turns = ?,
                        avg_latency_ms = (SELECT AVG(total_latency_ms) FROM conversation_turns WHERE session_id = ?)
                    WHERE session_id = ?
                    """,
                    (turn_index, self.session_id, self.session_id)
                )
                await db.commit()
        except Exception as e:
            logger.error("Database persistence error: %s", str(e))

class PipelineManager:
    def __init__(self):
        self.active_sessions: Dict[str, PipelineSession] = {}

    def get_or_create_session(self, session_id: str, callback: Optional[Callable] = None) -> PipelineSession:
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = PipelineSession(session_id, callback)
        elif callback:
            self.active_sessions[session_id].event_callback = callback
        return self.active_sessions[session_id]

    def remove_session(self, session_id: str):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

pipeline_manager = PipelineManager()
