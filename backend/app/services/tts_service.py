import time
import io
import logging
import asyncio
from typing import AsyncGenerator, Tuple, Optional
import edge_tts
from app.core.config import settings

logger = logging.getLogger("auralis.tts")

class TTSService:
    def __init__(self):
        self.default_voice = settings.TTS_VOICE

    def get_voice_for_context(self, emotion: str) -> Tuple[str, str, str]:
        """
        Dynamically adjust neural voice rate and pitch depending on conversational tension.
        For crisis negotiation simulator:
        - If trainee calmed Jordan down -> calmer tone, slower rate (-4%)
        - If agitated -> slightly tense, faster rate (+5%)
        """
        if emotion in ["calm", "neutral"]:
            return self.default_voice, "-3%", "+0Hz"
        elif emotion in ["agitated", "angry"]:
            return self.default_voice, "+6%", "+2Hz"
        elif emotion in ["anxious", "distressed"]:
            return self.default_voice, "+2%", "+1Hz"
        return self.default_voice, "+0%", "+0Hz"

    async def synthesize_stream(
        self,
        text: str,
        emotion: str = "neutral"
    ) -> AsyncGenerator[Tuple[bytes, bool, float], None]:
        """
        Stream audio chunks incrementally as generated.
        Yields: (audio_bytes, is_first_chunk, ttfa_ms)
        """
        start_time = time.perf_counter()
        voice, rate, pitch = self.get_voice_for_context(emotion)
        
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        is_first = True
        ttfa_ms = 0.0

        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data = chunk["data"]
                    if is_first:
                        ttfa_ms = (time.perf_counter() - start_time) * 1000.0
                        logger.info("TTS first chunk received in %.1f ms", ttfa_ms)
                        yield audio_data, True, ttfa_ms
                        is_first = False
                    else:
                        yield audio_data, False, ttfa_ms
        except Exception as e:
            logger.error("TTS streaming error: %s", str(e), exc_info=True)
            raise

    async def synthesize_full(
        self,
        text: str,
        emotion: str = "neutral"
    ) -> Tuple[bytes, float, float]:
        """
        Synthesize full utterance.
        Returns: (complete_audio_bytes, ttfa_ms, total_duration_ms)
        """
        start_time = time.perf_counter()
        audio_chunks = []
        ttfa_ms = 0.0

        async for chunk, is_first, chunk_ttfa in self.synthesize_stream(text, emotion):
            if is_first:
                ttfa_ms = chunk_ttfa
            audio_chunks.append(chunk)

        total_audio = b"".join(audio_chunks)
        total_duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        if ttfa_ms == 0.0:
            ttfa_ms = total_duration_ms
            
        logger.info("TTS completed %d bytes in %.1f ms (TTFA: %.1f ms)", len(total_audio), total_duration_ms, ttfa_ms)
        return total_audio, ttfa_ms, total_duration_ms

    @property
    def is_ready(self) -> bool:
        return True

tts_service = TTSService()
