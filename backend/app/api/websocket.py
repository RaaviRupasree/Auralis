import json
import logging
import asyncio
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.audio_pipeline import pipeline_manager
from app.utils.audio_utils import pcm_to_float32, resample_linear

logger = logging.getLogger("auralis.websocket")

router = APIRouter()

@router.websocket("/ws/audio/{session_id}")
async def websocket_audio_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info("WebSocket client connected for session: %s", session_id)

    async def send_event(data: dict):
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.debug("Failed to send WebSocket event: %s", str(e))

    pipeline = pipeline_manager.get_or_create_session(session_id, callback=send_event)

    try:
        while True:
            message = await websocket.receive()
            
            # Binary frame = Audio chunk from microphone
            if "bytes" in message and message["bytes"]:
                raw_bytes = message["bytes"]
                # Client sends 16-bit PCM at 16kHz
                audio_float32 = pcm_to_float32(raw_bytes)
                if len(audio_float32) > 0:
                    await pipeline.handle_audio_chunk(audio_float32)

            # Text frame = Control messages (interrupt, ping, config)
            elif "text" in message and message["text"]:
                try:
                    payload = json.loads(message["text"])
                    msg_type = payload.get("type")
                    
                    if msg_type == "interrupt":
                        logger.info("Client requested immediate interruption.")
                        await pipeline.interrupt_ai()
                    elif msg_type == "ping":
                        await websocket.send_text(json.dumps({"type": "pong", "time": payload.get("time")}))
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected for session: %s", session_id)
    except Exception as e:
        logger.error("WebSocket exception for session %s: %s", session_id, str(e))
    finally:
        pipeline_manager.remove_session(session_id)
