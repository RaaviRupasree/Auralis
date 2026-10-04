# Auralis

Auralis is a Real-Time Voice-to-Voice Emotion Engine.

## Week 1

- React frontend
- Python backend
- WebRTC audio communication
- Faster-Whisper speech-to-text

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

STT and emotion detection will be added in later steps.

## Speech-to-Text

Auralis uses Faster-Whisper to convert incoming microphone audio into text.

Flow:

Browser Microphone → WebRTC → aiortc → Audio Buffer → Faster-Whisper → Transcript

The default model is `tiny` with CPU `int8` settings. The model downloads to the local cache on first transcription; model files are not stored in this repository. Configure `WHISPER_MODEL`, `WHISPER_DEVICE`, and `WHISPER_COMPUTE_TYPE` with environment variables if needed.