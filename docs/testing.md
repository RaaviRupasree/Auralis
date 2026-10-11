# Auralis Testing & Quality Assurance Guide

This document details the automated test suite, verification methodology, and manual testing procedures.

---

## 1. Automated Test Suite

Auralis contains a comprehensive suite of unit and integration tests powered by `pytest`.

### Running All Tests
```bash
python -m pytest backend/tests -v
```

### Verified Test Cases (12/12 Passing)

| Test Module | Test Name | Purpose | Result |
|---|---|---|---|
| `test_api_integration.py` | `test_health_endpoints` | Verifies `/api/health` and `/api/health/models` endpoints | ✅ PASS |
| `test_api_integration.py` | `test_session_crud_and_analytics` | Verifies session creation, detail retrieval, termination, and metrics | ✅ PASS |
| `test_api_integration.py` | `test_config_endpoint` | Verifies retrieval and dynamic parameter updates | ✅ PASS |
| `test_audio_utils.py` | `test_pcm_conversions` | Verifies lossless 16-bit PCM to float32 conversions | ✅ PASS |
| `test_audio_utils.py` | `test_resample_linear` | Verifies 48kHz to 16kHz linear interpolation resampling | ✅ PASS |
| `test_audio_utils.py` | `test_calculate_energy_and_db` | Verifies RMS and dBFS mathematical accuracy | ✅ PASS |
| `test_audio_utils.py` | `test_wav_pack_and_parse` | Verifies WAV file packing and byte parsing | ✅ PASS |
| `test_emotion_service.py` | `test_extract_acoustic_features` | Verifies $F_0$, ZCR, and spectral centroid extraction | ✅ PASS |
| `test_emotion_service.py` | `test_predict_emotion_categories_and_confidence`| Verifies emotion category validation and bounded confidence | ✅ PASS |
| `test_emotion_service.py` | `test_empty_audio_handling` | Verifies graceful fallback on empty or sub-frame audio | ✅ PASS |
| `test_vad_service.py` | `test_vad_silence_detection` | Verifies silence rejection and non-triggering | ✅ PASS |
| `test_vad_service.py` | `test_vad_speech_onset_and_eou` | Verifies speech onset confirmation and EOU hang-time | ✅ PASS |

---

## 2. End-to-End WebSocket Stream Testing

Run the automated audio transport test against the live running server:
```bash
$env:PYTHONPATH="backend"
python backend/tests/test_e2e_audio_stream.py
```

This verifies:
1. REST API handshake and session creation in SQLite.
2. Binary WebSocket connection to `/ws/audio/{session_id}`.
3. Ingestion of 2048-sample 16kHz PCM chunks.
4. Voice Activity Detection event emission (`vad_active`).
5. Database turn persistence and latency records.

---

## 3. Frontend Quality Checks

Run the TypeScript type checker and Vite production bundle generator:
```bash
cd frontend
npm run build
```
- Validates 0 TypeScript errors (`tsc --noEmit`).
- Validates 0 linting or build syntax warnings.
- Compiles `dist/index.html` and bundled assets.

---

## 4. Manual Verification Steps (Microphone & Audio Flow)

1. Open `http://127.0.0.1:8080` in Chrome, Edge, Firefox, or Safari.
2. In the top navigation, click **Start Voice Session** or navigate to **Live Session** on the sidebar.
3. Click the **Start Voice Session** button.
4. Allow microphone access when prompted by the browser.
5. The status pill will transition to **LISTENING**. Speak into the microphone:
   > *"Jordan, I understand this is scary, but everyone wants you to come out safely."*
6. Watch the **Real-Time Waveform** canvas animate with cyan bars as you speak.
7. Upon pausing for ~600ms, notice:
   - State switches to **PROCESSING**, then **GENERATING**.
   - Your speech transcript appears under "Trainee (Transcribed)".
   - The **Detected Acoustic Emotion** badge displays your vocal tone (e.g. `Calm / De-escalated`, `Anxious`, etc.) along with the confidence score.
   - The **Measured Telemetry & Latency** card shows the real duration for STT, SER, LLM TTFT, and TTS TTFA.
8. When Jordan begins speaking (green waveform, status **SPEAKING**), speak into your microphone or click the **Barge-In (Interrupt)** button:
   - Notice that Jordan's voice stops immediately and the status returns cleanly to **LISTENING**.
9. Click **End Session**. Navigate to **History** to review the archived session turns, or **Analytics** to view aggregate latency trends.
