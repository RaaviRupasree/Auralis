import asyncio
import json
import numpy as np
import websockets
import httpx
from app.utils.audio_utils import float32_to_pcm

async def test_full_pipeline_stream():
    base_url = "http://127.0.0.1:8080"
    ws_url = "ws://127.0.0.1:8080"

    print("\n--- 1. Testing REST Endpoints ---")
    async with httpx.AsyncClient() as client:
        # Health
        resp = await client.get(f"{base_url}/api/health")
        assert resp.status_code == 200, f"Health failed: {resp.text}"
        print(f"Health response: {resp.json()}")

        # Models
        resp_models = await client.get(f"{base_url}/api/health/models")
        assert resp_models.status_code == 200
        print(f"Models response: {resp_models.json()}")

        # Create session
        resp_sess = await client.post(f"{base_url}/api/sessions", json={"scenario": "crisis_negotiation"})
        assert resp_sess.status_code == 200
        sess_data = resp_sess.json()
        session_id = sess_data["session_id"]
        print(f"Created session: {session_id}")

    print("\n--- 2. Testing WebSocket Audio Transport & Events ---")
    uri = f"{ws_url}/ws/audio/{session_id}"
    events_received = []

    async with websockets.connect(uri) as ws:
        # Generate 1.2 seconds of speech-like audio (440Hz with harmonics, modulated)
        sr = 16000
        t = np.linspace(0, 1.2, int(sr * 1.2), dtype=np.float32)
        speech_synth = 0.2 * np.sin(2 * np.pi * 220 * t) + 0.1 * np.sin(2 * np.pi * 440 * t)
        silence = np.zeros(int(sr * 0.8), dtype=np.float32)  # 800ms silence to trigger EOU
        
        full_audio = np.concatenate([speech_synth, silence])
        pcm_bytes = float32_to_pcm(full_audio)

        # Send in 2048-sample (~128ms) chunks like client microphone
        chunk_size = 2048 * 2  # 2 bytes per sample
        for i in range(0, len(pcm_bytes), chunk_size):
            chunk = pcm_bytes[i:i+chunk_size]
            await ws.send(chunk)
            await asyncio.sleep(0.02)  # Simulate real-time streaming

        print("Sent audio stream. Waiting for pipeline events...")

        # Collect events for up to 6 seconds
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=4.0)
                event = json.loads(msg)
                events_received.append(event)
                event_type = event.get("type")
                print(f"Received event: {event_type}")

                if event_type == "audio_output":
                    print(f"SUCCESS: Audio output received! TTS TTFA: {event.get('tts_ttfa_ms')}ms, Total: {event.get('total_latency_ms')}ms")
                    break
        except asyncio.TimeoutError:
            print("Finished waiting for events.")

    print(f"\nTotal events collected: {len(events_received)}")
    event_types = [e.get("type") for e in events_received]
    print(f"Event sequence: {event_types}")

    # Verify session in DB
    async with httpx.AsyncClient() as client:
        detail_resp = await client.get(f"{base_url}/api/sessions/{session_id}")
        assert detail_resp.status_code == 200
        print(f"Session detail turns in DB: {len(detail_resp.json()['turns'])}")

    print("\n=== FULL PIPELINE STREAMING TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline_stream())
