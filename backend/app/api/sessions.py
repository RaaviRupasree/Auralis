import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from app.core.database import get_db_connection
from app.schemas.api_schemas import (
    SessionCreateRequest,
    SessionSummary,
    SessionDetailResponse,
    TurnRecord,
    LatencyMetrics
)
from app.services.audio_pipeline import pipeline_manager
from app.services.webrtc_gateway import webrtc_gateway

router = APIRouter()

@router.post("/sessions", response_model=SessionSummary)
async def create_session(req: SessionCreateRequest):
    session_id = str(uuid.uuid4())
    now_iso = datetime.utcnow().isoformat()
    
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO sessions (session_id, scenario, start_time, status, total_turns, avg_latency_ms)
            VALUES (?, ?, ?, 'active', 0, 0.0)
            """,
            (session_id, req.scenario, now_iso)
        )
        await db.commit()
        
    return SessionSummary(
        session_id=session_id,
        scenario=req.scenario,
        start_time=now_iso,
        total_turns=0,
        status="active",
        avg_latency_ms=0.0,
        created_at=now_iso
    )

@router.get("/sessions", response_model=List[SessionSummary])
async def list_sessions(limit: int = 20):
    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        
    return [
        SessionSummary(
            session_id=row["session_id"],
            scenario=row["scenario"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            total_turns=row["total_turns"],
            status=row["status"],
            avg_latency_ms=row["avg_latency_ms"] or 0.0,
            created_at=row["created_at"]
        )
        for row in rows
    ]

@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str):
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        session_row = await cursor.fetchone()
        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")
            
        cursor_turns = await db.execute(
            "SELECT * FROM conversation_turns WHERE session_id = ? ORDER BY turn_index ASC",
            (session_id,)
        )
        turn_rows = await cursor_turns.fetchall()

    session_summary = SessionSummary(
        session_id=session_row["session_id"],
        scenario=session_row["scenario"],
        start_time=session_row["start_time"],
        end_time=session_row["end_time"],
        total_turns=session_row["total_turns"],
        status=session_row["status"],
        avg_latency_ms=session_row["avg_latency_ms"] or 0.0,
        created_at=session_row["created_at"]
    )

    turns = [
        TurnRecord(
            turn_id=t["turn_id"],
            session_id=t["session_id"],
            turn_index=t["turn_index"],
            user_transcript=t["user_transcript"],
            detected_emotion=t["detected_emotion"],
            emotion_confidence=t["emotion_confidence"],
            ai_response=t["ai_response"],
            metrics=LatencyMetrics(
                stt_duration_ms=t["stt_duration_ms"] or 0.0,
                ser_duration_ms=t["ser_duration_ms"] or 0.0,
                llm_ttft_ms=t["llm_ttft_ms"] or 0.0,
                llm_total_ms=t["llm_total_ms"] or 0.0,
                tts_ttfa_ms=t["tts_ttfa_ms"] or 0.0,
                tts_total_ms=t["tts_total_ms"] or 0.0,
                total_latency_ms=t["total_latency_ms"] or 0.0
            ),
            was_interrupted=bool(t["was_interrupted"]),
            created_at=t["created_at"]
        )
        for t in turn_rows
    ]

    return SessionDetailResponse(session=session_summary, turns=turns)

@router.post("/sessions/{session_id}/terminate")
async def terminate_session(session_id: str):
    now_iso = datetime.utcnow().isoformat()
    async with get_db_connection() as db:
        await db.execute(
            "UPDATE sessions SET status = 'completed', end_time = ? WHERE session_id = ?",
            (now_iso, session_id)
        )
        await db.commit()

    # Clean up pipeline & webrtc memory
    pipeline_manager.remove_session(session_id)
    await webrtc_gateway.close_session(session_id)
    return {"status": "terminated", "session_id": session_id}
