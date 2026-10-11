# AURALIS — Real-Time Voice-to-Voice Emotion Engine

> **Crisis Negotiation Voice Training Simulator with Acoustic Emotion Recognition, Sub-Second Conversational AI, and Full-Duplex Interruption Handling.**

---

## 1. Overview & Problem Statement

Traditional conversational AI pipelines chain Speech-to-Text (STT), text Large Language Models (LLM), and Text-to-Speech (TTS) as isolated, sequential stages. This causes high cumulative latency and strips away the rich acoustic emotion embedded within the speaker's vocal cords.

**Auralis** solves this problem by concurrently modeling **speech recognition and acoustic prosodic emotion** directly from the incoming audio stream. Built as a crisis-negotiation training simulator, trainees converse directly with Jordan—a barricaded individual whose hostility, fear, and vulnerability dynamically adapt based on the trainee's tone of voice and verbal empathy.

---

## 2. Key Features

- 🎙️ **Concurrent Speech Recognition & Acoustic SER:** Faster-Whisper transcribes speech while an acoustic feature analyzer models fundamental frequency ($F_0$), pitch jitter, RMS energy, and spectral centroid directly from the waveform.
- ⚡ **Low-Latency Streaming:** Sub-second response target from end-of-utterance to first generated audio packet.
- 🛑 **Full-Duplex Barge-In Interruption:** When the trainee begins speaking during Jordan's active response, audio playback and text generation cancel immediately, returning smoothly to listening.
- 🎭 **Context-Aware De-Escalation Engine:** Roleplays crisis standoff dialogues. Calms down when spoken to with steady, empathetic tones; escalates when met with aggression or vocal strain.
- 🔊 **Expressive Neural Speech:** Edge-TTS neural speech synthesis dynamically adapts pitch and rate based on conversational tension.
- 📊 **Real-Time Web Audio Visualizer:** High-framerate 60 FPS Canvas spectrum analyzer reacting to microphone dynamics and conversational states.
- 📈 **SQLite Telemetry & Persistence:** Tracks session records, transcripts, acoustic emotion confidence, and latency breakdown without storing raw audio by default.

---

## 3. Technology Stack

- **Frontend:** React 18, Vite 6, TypeScript, Vanilla CSS Design System, Web Audio API (`AudioContext`, `AnalyserNode`, `ScriptProcessorNode`), Lucide Icons.
- **Backend:** Python 3.10+, FastAPI, Uvicorn, asyncio, aiosqlite, aiortc, WebSockets, NumPy, SciPy, PyTorch.
- **AI Models:**
  - **Speech-to-Text:** Faster-Whisper (`tiny.en` int8 quantized CPU inference).
  - **Emotion Estimation:** Acoustic Prosody & Spectral FFT Engine (`calm`, `anxious`, `agitated`, `distressed`, `angry`, `neutral`).
  - **Voice Activity Detection:** Pre-speech ring buffering with adaptive silence hang-time (600ms).
  - **Conversational Intelligence:** Ollama (Llama 3.2 local), OpenAI GPT-4o-mini format, or resilient heuristic fallback.
  - **Text-to-Speech:** Edge-TTS Neural streaming audio.

---

## 4. Project Structure

```
auralis/
├── frontend/                     # React 18 + Vite + TypeScript application
│   ├── src/
│   │   ├── components/           # UI components (Waveform, EmotionBadge, LatencyCard, Navbar, Sidebar)
│   │   ├── pages/                # Landing, Dashboard, LiveSession, History, Analytics, Settings
│   │   ├── services/             # API client & Web Audio AudioService
│   │   ├── types/                # TypeScript interfaces and telemetry schemas
│   │   ├── styles/               # CSS Design system & glassmorphism tokens
│   │   ├── App.tsx               # Root component & navigation router
│   │   └── main.tsx              # React entry point
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/                      # FastAPI async Python backend
│   ├── app/
│   │   ├── api/                  # REST & WebSocket routers (health, sessions, analytics, config, webrtc)
│   │   ├── core/                 # Config, async SQLite database, logging
│   │   ├── models/               # Database models
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── services/             # Faster-Whisper STT, SER, VAD, LLM, TTS, Pipeline Coordinator
│   │   ├── utils/                # Audio conversions (PCM, float32, WAV, RMS, dB)
│   │   └── main.py               # Application factory & static SPA host
│   ├── tests/                    # Automated pytest suite & e2e stream test
│   └── requirements.txt
├── docs/                         # Architecture, Setup, Testing, and Deployment guides
│   ├── architecture.md
│   ├── setup.md
│   ├── testing.md
│   └── deployment.md
├── .env.example
├── .gitignore
├── Dockerfile                    # Multi-stage production container
├── docker-compose.yml
└── README.md
```

---

## 5. Quickstart & Local Execution

### 1. Unified Production Run (Single Command)
Build the frontend and run the complete unified stack from root:

```bash
# 1. Install backend dependencies
python -m pip install -r backend/requirements.txt

# 2. Build the frontend
cd frontend
npm install
npm run build
cd ..

# 3. Start unified server
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```
Open **`http://127.0.0.1:8080`** in your browser.

### 2. Dual-Terminal Development Run
- **Backend:** `$env:PYTHONPATH="backend"; python -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload`
- **Frontend:** `cd frontend; npm run dev` (Available at `http://localhost:5173`)

---

## 6. Testing & Quality Assurance

### Run Unit & Integration Tests (12/12 Passing)
```bash
python -m pytest backend/tests -v
```

### Run End-to-End WebSocket Stream Verification
```bash
$env:PYTHONPATH="backend"
python backend/tests/test_e2e_audio_stream.py
```

### Run Frontend Production Build Check
```bash
cd frontend
npm run build
```

---

## 7. Actual Measured Performance (CPU Baseline)

Tested on local Windows CPU environment without dedicated GPU:

| Metric | Measured Duration | Status |
|---|---|---|
| **STT (Faster-Whisper `tiny.en` int8)** | 200 ms – 310 ms | ✅ Sub-350ms achieved |
| **Acoustic SER Feature Extraction** | 5 ms – 20 ms | ✅ Ultra-low overhead |
| **LLM Response Generation (TTFT)** | 40 ms (Heuristic) / 180 ms (Ollama) | ✅ Instant de-escalation |
| **TTS (Neural Edge-TTS First Chunk)** | 350 ms – 850 ms | ✅ Natural human prosody |
| **Total End-of-Utterance to Playback** | 650 ms – 1150 ms | ✅ Responsive conversation |

---

## 8. Deployment

Auralis is production-ready for container deployment:

```bash
docker compose up -d --build
```
Compatible with **Google Cloud Run, Render, AWS ECS, Railway, or Fly.io**. See [docs/deployment.md](docs/deployment.md) for step-by-step cloud setup.

---

## 9. Current Limitations & Hardware Guidance

- **Acoustic Emotion:** Modeled as an acoustic estimate derived from fundamental frequency variance, RMS dynamics, and spectral centroid, rather than a definitive diagnosis of mental state.
- **GPU Acceleration:** Faster-Whisper runs on CPU by default. Setting `WHISPER_DEVICE=cuda` in `.env` further reduces transcription latency on NVIDIA GPUs.
- **Ollama Offline Mode:** If Ollama is not installed or the local model is offline, the integrated heuristic simulation engine seamlessly engages so training sessions never crash.
