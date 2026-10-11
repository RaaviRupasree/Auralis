from collections import Counter
from fastapi import APIRouter
from app.core.database import get_db_connection
from app.schemas.api_schemas import AnalyticsResponse

router = APIRouter()

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics():
    async with get_db_connection() as db:
        # Session stats
        cursor_sessions = await db.execute("SELECT COUNT(*) AS total FROM sessions")
        sess_row = await cursor_sessions.fetchone()
        total_sessions = sess_row["total"] if sess_row else 0

        # Turn stats
        cursor_turns = await db.execute(
            """
            SELECT 
                COUNT(*) as total_turns,
                AVG(total_latency_ms) as avg_latency,
                AVG(stt_duration_ms) as avg_stt,
                AVG(ser_duration_ms) as avg_ser,
                AVG(llm_ttft_ms) as avg_llm_ttft,
                AVG(tts_ttfa_ms) as avg_tts_ttfa,
                SUM(was_interrupted) as total_interruptions
            FROM conversation_turns
            """
        )
        stats = await cursor_turns.fetchone()

        # Emotion distribution
        cursor_emotions = await db.execute(
            "SELECT detected_emotion, COUNT(*) as cnt FROM conversation_turns WHERE detected_emotion IS NOT NULL GROUP BY detected_emotion"
        )
        emotion_rows = await cursor_emotions.fetchall()

    emotion_dist = {row["detected_emotion"]: row["cnt"] for row in emotion_rows}

    return AnalyticsResponse(
        total_sessions=total_sessions,
        total_turns=stats["total_turns"] or 0,
        avg_latency_ms=round(stats["avg_latency"] or 0.0, 1),
        avg_stt_ms=round(stats["avg_stt"] or 0.0, 1),
        avg_ser_ms=round(stats["avg_ser"] or 0.0, 1),
        avg_llm_ttft_ms=round(stats["avg_llm_ttft"] or 0.0, 1),
        avg_tts_ttfa_ms=round(stats["avg_tts_ttfa"] or 0.0, 1),
        emotion_distribution=emotion_dist,
        interruption_count=stats["total_interruptions"] or 0
    )
