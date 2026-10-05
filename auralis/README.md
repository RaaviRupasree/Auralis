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
segments are passed to Faster-Whisper. Emotion detection remains for a later
step.

## Speech-to-Text

Auralis uses Faster-Whisper to convert incoming microphone audio into text.

The Week 1 audio flow was:

Browser Microphone → WebRTC → aiortc → Audio Buffer → Faster-Whisper → Transcript

The default model is `tiny` with CPU `int8` settings. The model downloads to the local cache on first transcription; model files are not stored in this repository. Configure `WHISPER_MODEL`, `WHISPER_DEVICE`, and `WHISPER_COMPUTE_TYPE` with environment variables if needed.

## Current Audio Pipeline

Browser Microphone → React → WebRTC → aiortc → Silero VAD → Completed Speech Segment → Faster-Whisper → Transcript

### Completed

- Project setup
- FastAPI backend
- WebRTC audio foundation
- Faster-Whisper STT
- Basic latency measurement
- Silero voice activity detection and speech-end segmentation

### Next

Continue with the next planned step only when ready.