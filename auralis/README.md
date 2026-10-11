# Auralis

Auralis is a Real-Time Voice-to-Voice Emotion Engine.

## Week 1

- React frontend
- Python backend
- WebRTC audio communication
- Faster-Whisper speech-to-text

## Week 2 - Step 1: Silero VAD

Silero VAD from Faster-Whisper detects speech in the 16 kHz WebRTC audio stream.
The backend retains a short pre-roll, waits for 800 ms of silence to end a
speech segment, and sends only completed speech segments to Faster-Whisper.
The existing transcript endpoint reports whether the backend is listening,
has detected speech, or is processing a transcript.

## Technology Stack

- React
- JavaScript
- Python
- FastAPI
- aiortc
- Faster-Whisper
- Transformers and PyTorch for Wav2Vec2 emotion classification
- Ollama for local Llama inference

## Backend

The backend API uses FastAPI, and Uvicorn runs the development server.

On Windows PowerShell, activate the backend environment and start the server:

```powershell
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload
```

- Health check: http://127.0.0.1:8000/health
- API documentation: http://127.0.0.1:8000/docs

## WebRTC Audio Foundation

Auralis now has a basic WebRTC connection between the React frontend and Python backend.

Flow:

Browser Microphone → React → WebRTC → aiortc → FastAPI Backend

Silero VAD now detects speech on the incoming stream, and completed speech
segments are passed to Faster-Whisper. Wav2Vec2 classifies each completed
segment in parallel with transcription. Predictions include the label and
confidence returned by the model.

## Speech-to-Text

Auralis uses Faster-Whisper to convert incoming microphone audio into text.

The Week 1 audio flow was:

Browser Microphone → WebRTC → aiortc → Audio Buffer → Faster-Whisper → Transcript

The default model is `tiny` with CPU `int8` settings. The model downloads to the local cache on first transcription; model files are not stored in this repository. Configure `WHISPER_MODEL`, `WHISPER_DEVICE`, and `WHISPER_COMPUTE_TYPE` with environment variables if needed.

The default emotion checkpoint is `superb/wav2vec2-base-superb-er`. It is
downloaded to the local Hugging Face cache on the first completed speech
segment. Set `EMOTION_MODEL` to use a different compatible audio-classification
checkpoint.

## Week 2 – LLM Context Engine

After VAD completes a speech segment, Auralis transcribes it and classifies its
acoustic emotion. The transcript, emotion label, and confidence are then sent
to a local Ollama chat server. Empty transcripts are skipped. The LLM is not
called while speech is still being captured.

The default local model is `llama3.2:1b`, selected as a lightweight Llama model
for development. Install Ollama for Windows from
[ollama.com/download/windows](https://ollama.com/download/windows), then open a
new terminal and verify it:

```powershell
ollama --version
ollama pull llama3.2:1b
ollama list
```

Ollama normally runs as a local service after installation. If needed, start
the server with `ollama serve`. Configure the model in the backend environment
before starting FastAPI:

```powershell
$env:OLLAMA_MODEL = "llama3.2:1b"
uvicorn main:app --reload
```

`OLLAMA_HOST` defaults to `http://localhost:11434`, and
`OLLAMA_TIMEOUT_SECONDS` defaults to `60`. Set `OLLAMA_MODEL` to the exact tag
shown by `ollama list` when using another installed Llama-family model. No
Python Ollama package is required; the backend uses Ollama's local HTTP API.

The model receives a crisis-negotiation training persona and the structured
transcript, emotion, and confidence context. It is instructed to remain calm,
acknowledge emotion without treating the acoustic label as certain, avoid
escalation, keep replies concise, and not claim to be a real emergency service.
Each completed frontend segment displays the transcript, emotion, confidence,
and generated text response.

LLM request latency is measured with `time.perf_counter()` and returned with
each completed segment in `llm_latency_ms`. It is also logged in milliseconds.
Latency was not measured in this development environment because Ollama is not
installed here; first-run model loading and local machine performance will
affect timings. The backend reports an actionable error when Ollama or the
configured model is unavailable without interrupting WebRTC or discarding the
transcript and emotion result.

## Current Audio Pipeline

Browser Microphone → React → WebRTC → aiortc → Silero VAD → Completed Speech Segment → Faster-Whisper + Wav2Vec2 → Transcript + Emotion → Ollama + Llama → Response Text

### Completed

- Project setup
- FastAPI backend
- WebRTC audio foundation
- Faster-Whisper STT
- Basic latency measurement
- Silero voice activity detection and speech-end segmentation
- Wav2Vec2 acoustic emotion predictions for completed speech segments
- Local Ollama Llama context responses for completed speech segments

### Next

Continue with the next planned step only when ready.