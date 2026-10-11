"""
Auralis - Voice-to-Voice Emotion Engine
Backend Application Entry Point
"""
import os
import sys
import uvicorn

# Ensure the backend directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
