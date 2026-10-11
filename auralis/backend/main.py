import logging
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.webrtc_service import (
	close_peer_connections,
	create_answer,
	get_transcription,
)


@asynccontextmanager
async def lifespan(app):
	yield
	await close_peer_connections()


# Create the API application used by Uvicorn.
app = FastAPI(lifespan=lifespan)
logger = logging.getLogger(__name__)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
	allow_methods=["GET", "POST"],
	allow_headers=["Content-Type"],
)


class OfferRequest(BaseModel):
	sdp: str
	type: Literal["offer"]


@app.get("/")
def read_root():
	# Provide a simple confirmation that the backend is running.
	return {"message": "Auralis backend is running"}


@app.get("/health")
def health_check():
	# Let tools check that the API is responding.
	return {"status": "ok"}


@app.post("/offer")
async def submit_offer(offer: OfferRequest):
	try:
		return await create_answer(offer.sdp, offer.type)
	except Exception as error:
		logger.exception("Could not complete WebRTC offer")
		raise HTTPException(
			status_code=400,
			detail="Could not complete the WebRTC offer.",
		) from error


@app.get("/transcripts/{session_id}")
def read_transcript(session_id: str):
	transcription = get_transcription(session_id)
	if transcription is None:
		raise HTTPException(status_code=404, detail="Transcript session not found.")
	return transcription