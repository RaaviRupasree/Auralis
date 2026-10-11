import aiosqlite
import logging
from contextlib import asynccontextmanager
from app.core.config import settings

logger = logging.getLogger("auralis.db")

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    scenario TEXT DEFAULT 'crisis_negotiation',
    start_time TEXT NOT NULL,
    end_time TEXT,
    total_turns INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    avg_latency_ms REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_turns (
    turn_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    user_transcript TEXT NOT NULL,
    detected_emotion TEXT,
    emotion_confidence REAL,
    ai_response TEXT NOT NULL,
    stt_duration_ms REAL,
    ser_duration_ms REAL,
    llm_ttft_ms REAL,
    llm_total_ms REAL,
    tts_ttfa_ms REAL,
    tts_total_ms REAL,
    total_latency_ms REAL,
    was_interrupted BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_turns_session_id ON conversation_turns(session_id);
"""

async def init_db():
    """Initialize database tables and indexes."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()
    logger.info("Database initialized successfully at %s", settings.DB_PATH)

@asynccontextmanager
async def get_db_connection():
    """Context manager for acquiring SQLite database connection."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
