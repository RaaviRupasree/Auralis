import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.database import init_db
from app.api import health, sessions, analytics, config, webrtc, websocket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("auralis.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Auralis Backend...")
    await init_db()
    logger.info("Auralis Backend is ready to serve requests.")
    yield
    logger.info("Auralis Backend shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-Time Voice-to-Voice Emotion Engine — Crisis Negotiation Simulator",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(config.router, prefix="/api", tags=["Configuration"])
app.include_router(webrtc.router, prefix="/api", tags=["WebRTC"])
app.include_router(websocket.router, tags=["WebSocket"])

# Production Static Frontend Mount
dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(dist_path):
    logger.info("Mounting frontend production static files from %s", dist_path)
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API or WS
        if full_path.startswith("api") or full_path.startswith("ws"):
            return None
        file_path = os.path.join(dist_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_path, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "app": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "description": "Crisis Negotiation Real-Time Voice-to-Voice Emotion Engine",
            "docs": "/docs",
            "health": "/api/health"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
