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