import asyncio
import logging
import uuid

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError
from av import AudioResampler
import numpy as np

from services.whisper_service import transcribe_samples

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
peer_connections = set()
audio_tasks = set()
transcriptions = {}
transcription_lock = asyncio.Lock()
SAMPLE_RATE = 16000
BUFFER_DURATION_SECONDS = 3
BUFFER_SAMPLE_COUNT = SAMPLE_RATE * BUFFER_DURATION_SECONDS
MINIMUM_TAIL_SAMPLE_COUNT = SAMPLE_RATE // 2


async def _transcribe_buffer(session_id, audio_samples):
    try:
        async with transcription_lock:
            text = await asyncio.to_thread(transcribe_samples, audio_samples)
    except Exception:
        logger.exception("Faster-Whisper transcription failed")
        return

    if text:
        current_text = transcriptions.get(session_id, "")
        transcriptions[session_id] = " ".join(
            part for part in (current_text, text) if part
        )
        print(f"Transcript: {text}", flush=True)


def _queue_transcription(session_id, audio_samples):
    task = asyncio.create_task(_transcribe_buffer(session_id, audio_samples))
    audio_tasks.add(task)
    task.add_done_callback(audio_tasks.discard)


async def _receive_audio(track, session_id):
    resampler = AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
    audio_buffer = []
    buffered_sample_count = 0

    try:
        while True:
            frame = await track.recv()
            for resampled_frame in resampler.resample(frame):
                samples = (
                    resampled_frame.to_ndarray()
                    .reshape(-1)
                    .astype(np.float32)
                    / 32768.0
                )
                if samples.size == 0:
                    continue

                audio_buffer.append(samples)
                buffered_sample_count += samples.size

                if buffered_sample_count >= BUFFER_SAMPLE_COUNT:
                    _queue_transcription(
                        session_id,
                        np.concatenate(audio_buffer),
                    )
                    audio_buffer = []
                    buffered_sample_count = 0
    except MediaStreamError:
        logger.info("Audio track ended")
    except Exception:
        logger.exception("Could not process incoming audio")
    finally:
        if buffered_sample_count >= MINIMUM_TAIL_SAMPLE_COUNT:
            _queue_transcription(session_id, np.concatenate(audio_buffer))


async def create_answer(sdp, offer_type):
    peer_connection = RTCPeerConnection()
    session_id = str(uuid.uuid4())
    peer_connections.add(peer_connection)
    transcriptions[session_id] = ""

    @peer_connection.on("track")
    def on_track(track):
        if track.kind != "audio":
            return

        print("Audio track received", flush=True)
        task = asyncio.create_task(_receive_audio(track, session_id))
        audio_tasks.add(task)
        task.add_done_callback(audio_tasks.discard)

    @peer_connection.on("connectionstatechange")
    async def on_connection_state_change():
        state = peer_connection.connectionState
        logger.info("WebRTC connection state: %s", state)
        if state in {"failed", "closed"}:
            peer_connections.discard(peer_connection)
        if state == "failed":
            await peer_connection.close()

    try:
        offer = RTCSessionDescription(sdp=sdp, type=offer_type)
        await peer_connection.setRemoteDescription(offer)
        answer = await peer_connection.createAnswer()
        await peer_connection.setLocalDescription(answer)
    except Exception:
        peer_connections.discard(peer_connection)
        transcriptions.pop(session_id, None)
        await peer_connection.close()
        raise

    return {
        "sdp": peer_connection.localDescription.sdp,
        "type": peer_connection.localDescription.type,
        "session_id": session_id,
    }


def get_transcription(session_id):
    return transcriptions.get(session_id)


async def close_peer_connections():
    connections = list(peer_connections)
    await asyncio.gather(
        *(connection.close() for connection in connections),
        return_exceptions=True,
    )
    peer_connections.clear()

    if audio_tasks:
        await asyncio.gather(*list(audio_tasks), return_exceptions=True)