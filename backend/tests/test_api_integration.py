import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db

def run_async(coro):
    return asyncio.run(coro)

def test_health_endpoints():
    async def _test():
        await init_db()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "online"
            assert data["service"] == "Auralis"

            resp_models = await client.get("/api/health/models")
            assert resp_models.status_code == 200
            models_data = resp_models.json()
            assert "whisper_model" in models_data
            assert "ser_ready" in models_data
            assert "tts_ready" in models_data
    run_async(_test())

def test_session_crud_and_analytics():
    async def _test():
        await init_db()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create session
            create_resp = await client.post("/api/sessions", json={"scenario": "crisis_negotiation"})
            assert create_resp.status_code == 200
            sess_data = create_resp.json()
            session_id = sess_data["session_id"]
            assert session_id is not None
            assert sess_data["status"] == "active"

            # Fetch session detail
            detail_resp = await client.get(f"/api/sessions/{session_id}")
            assert detail_resp.status_code == 200
            detail_data = detail_resp.json()
            assert detail_data["session"]["session_id"] == session_id
            assert isinstance(detail_data["turns"], list)

            # Terminate session
            term_resp = await client.post(f"/api/sessions/{session_id}/terminate")
            assert term_resp.status_code == 200
            assert term_resp.json()["status"] == "terminated"

            # Check analytics
            analytics_resp = await client.get("/api/analytics")
            assert analytics_resp.status_code == 200
            analytics_data = analytics_resp.json()
            assert "total_sessions" in analytics_data
            assert analytics_data["total_sessions"] >= 1
    run_async(_test())

def test_config_endpoint():
    async def _test():
        await init_db()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/config")
            assert resp.status_code == 200
            cfg = resp.json()
            assert "llm_provider" in cfg
            assert "tts_voice" in cfg

            # Update config
            upd_resp = await client.post("/api/config", json={"vad_silence_duration_ms": 650})
            assert upd_resp.status_code == 200
            assert upd_resp.json()["config"]["vad_silence_duration_ms"] == 650
    run_async(_test())
