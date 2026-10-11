# Auralis Setup & Installation Guide

This guide covers setting up and running Auralis from scratch on Windows, macOS, or Linux.

---

## 1. Prerequisites

- **Python:** 3.10 or 3.11 (Tested with Python 3.10.11)
- **Node.js:** v18+ (Tested with Node v22.23.2)
- **FFmpeg:** Installed and available on system PATH
- **Git:** Installed
- **Optional Local LLM:** [Ollama](https://ollama.com/) for local offline model inference

---

## 2. Quickstart (Unified Production Mode)

The simplest way to run Auralis is via the unified FastAPI server, which serves both the backend API/WebSocket gateways and the pre-built React frontend SPA.

### Step 1: Install Python Dependencies
```bash
cd backend
python -m pip install -r requirements.txt
```

### Step 2: Build the Frontend
```bash
cd ../frontend
npm install
npm run build
```

### Step 3: Run the Application
```bash
cd ..
# PowerShell (Windows)
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080

# Bash (Linux/macOS)
PYTHONPATH=backend python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Open your browser at: **`http://127.0.0.1:8080`**

---

## 3. Development Mode (Hot-Reloading Frontend + Backend)

If you are developing components and want Vite HMR:

### Terminal 1: Backend
```bash
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

Open your browser at: **`http://localhost:5173`** (Vite proxies all `/api` and `/ws` traffic to port 8080).

---

## 4. Ollama Local LLM Configuration (Optional)

By default, Auralis includes an integrated resilient heuristic crisis-negotiation engine that requires zero external models. To use genuine local Llama 3.2:

1. Download and install Ollama from [ollama.com](https://ollama.com).
2. Pull and start Llama 3.2:
   ```bash
   ollama run llama3.2
   ```
3. Auralis will automatically detect Ollama at `http://localhost:11434` and use it for responses.
4. You can also switch providers or adjust models on the **Settings** page in the Auralis UI.

---

## 5. Environment Variables (`.env`)

Configure `.env` in the root folder:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | Port for the backend application server |
| `HOST` | `0.0.0.0` | Bind host address |
| `WHISPER_MODEL_SIZE` | `tiny.en` | Faster-Whisper model (`tiny.en`, `base.en`, `small.en`) |
| `WHISPER_DEVICE` | `cpu` | Inference device (`cpu` or `cuda`) |
| `WHISPER_COMPUTE_TYPE`| `int8` | Model precision (`int8` or `float32`) |
| `LLM_PROVIDER` | `ollama` | Provider: `ollama`, `openai`, or `heuristic_fallback` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.2` | Target local model |
| `OPENAI_API_KEY` | `""` | OpenAI API key (if using OpenAI provider) |
| `TTS_VOICE` | `en-US-ChristopherNeural`| Neural voice style |
| `VAD_ENERGY_THRESHOLD`| `0.015` | Speech detection energy threshold |
| `VAD_SILENCE_DURATION_MS`| `600` | Silence duration required for end-of-utterance |
