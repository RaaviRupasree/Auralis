# Auralis - Real-Time Voice-to-Voice Emotion Engine

This workspace is being built one step at a time. Week 1 creates the voice-to-text foundation only: React in the browser sends microphone audio over WebRTC to a Python backend, which will transcribe it with Faster-Whisper. Emotion detection and all later-week features are out of scope for this setup.

## Step 1: Project setup

### 1. Check the prerequisites

Open a PowerShell terminal and check that Python 3.10 or newer and Node.js with npm are installed:

```powershell
python --version
node --version
npm --version
```

Expected output is a Python version such as `Python 3.10.x` or newer, followed by Node.js and npm version numbers. If a command is not recognized, install that tool and open a new terminal before continuing.

### 2. Open the project folder

In PowerShell:

```powershell
cd "<workspace-folder>\auralis"
```

Replace `<workspace-folder>` with the folder containing this project. In VS Code, you can also open the `auralis` folder directly.

### 3. Check the scaffold

Run:

```powershell
tree /F
```

The folders and starter files should be present. The backend entry point, Python dependencies, and React scripts/dependencies will be filled in during their corresponding steps so each part can be explained and tested before moving on.

## Folder guide

- `backend/` will contain the FastAPI application and Python dependencies.
- `backend/audio/` is reserved for audio-processing helpers; microphone audio will arrive over WebRTC, not through an upload form.
- `backend/models/` is reserved for local model assets or configuration. Faster-Whisper may download its selected model the first time it runs.
- `backend/services/` will contain the separate speech-to-text service.
- `backend/utils/` is reserved for small backend utilities.
- `frontend/` will contain the React application.
- `frontend/src/` will contain the React interface and WebRTC client code.
- `frontend/public/` will contain static frontend assets.

There is no app to launch in Step 1. Continue only after checking the prerequisites and folder structure; the next step will add the backend foundation.
