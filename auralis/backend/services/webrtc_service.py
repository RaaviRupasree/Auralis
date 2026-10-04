import asyncio
import logging
import uuid

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError
from av import AudioResampler
import numpy as np

from services.whisper_service import transcribe_samples
from utils.latency import elapsed_seconds, start_timer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
peer_connections = set()
audio_tasks = set()
transcriptions = {}
transcription_statuses = {}
pending_transcriptions = {}
transcription_lock = asyncio.Lock()
SAMPLE_RATE = 16000
BUFFER_DURATION_SECONDS = 3
BUFFER_SAMPLE_COUNT = SAMPLE_RATE * BUFFER_DURATION_SECONDS
MINIMUM_TAIL_SAMPLE_COUNT = SAMPLE_RATE // 2
SILENCE_RMS_THRESHOLD = 0.003


def _has_audio_energy(audio_samples):
    if audio_samples.size == 0:
        return False

    rms = float(np.sqrt(np.mean(np.square(audio_samples))))
    return rms >= SILENCE_RMS_THRESHOLD


async def _transcribe_buffer(session_id, audio_samples, audio_started_at):
    try:
        async with transcription_lock:
            text = await asyncio.to_thread(transcribe_samples, audio_samples)
        if text:
            current_text = transcriptions.get(session_id, "")
            transcriptions[session_id] = " ".join(
                part for part in (current_text, text) if part
            )
            latency = elapsed_seconds(audio_started_at)
            print(f"Transcript: {text}", flush=True)
            print(f"Transcription latency: {latency:.2f} seconds", flush=True)
    except Exception:
        logger.exception("Faster-Whisper transcription failed")
        transcription_statuses[session_id] = "error"
    finally:
        remaining = pending_transcriptions.get(session_id, 1) - 1
        if remaining > 0:
            pending_transcriptions[session_id] = remaining
            transcription_statuses[session_id] = "processing"
        else:
            pending_transcriptions.pop(session_id, None)
            if transcription_statuses.get(session_id) != "error":
                transcription_statuses[session_id] = "ready"


def _queue_transcription(session_id, audio_samples, audio_started_at):
    if not _has_audio_energy(audio_samples):
        return

    pending_transcriptions[session_id] = (
        pending_transcriptions.get(session_id, 0) + 1
    )
    transcription_statuses[session_id] = "processing"
    task = asyncio.create_task(
        _transcribe_buffer(session_id, audio_samples, audio_started_at)
    )
    audio_tasks.add(task)
    task.add_done_callback(audio_tasks.discard)


async def _receive_audio(track, session_id):
    resampler = AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
    audio_buffer = []
    buffered_sample_count = 0
    audio_started_at = None

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

                if buffered_sample_count == 0:
                    audio_started_at = start_timer()
                audio_buffer.append(samples)
                buffered_sample_count += samples.size

                if buffered_sample_count >= BUFFER_SAMPLE_COUNT:
                    _queue_transcription(
                        session_id,
                        np.concatenate(audio_buffer),
                        audio_started_at,
                    )
                    audio_buffer = []
                    buffered_sample_count = 0
                    audio_started_at = None
    except MediaStreamError:
        logger.info("Audio track ended")
    except Exception:
        logger.exception("Could not process incoming audio")
    finally:
        if buffered_sample_count >= MINIMUM_TAIL_SAMPLE_COUNT:
            _queue_transcription(
                session_id,
                np.concatenate(audio_buffer),
                audio_started_at or start_timer(),
            )


async def create_answer(sdp, offer_type):
    peer_connection = RTCPeerConnection()
    session_id = str(uuid.uuid4())
    peer_connections.add(peer_connection)
    transcriptions[session_id] = ""
    transcription_statuses[session_id] = "ready"

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
        transcription_statuses.pop(session_id, None)
        pending_transcriptions.pop(session_id, None)
        await peer_connection.close()
        raise

    return {
        "sdp": peer_connection.localDescription.sdp,
        "type": peer_connection.localDescription.type,
        "session_id": session_id,
    }


def get_transcription(session_id):
    if session_id not in transcriptions:
        return None
    return {
        "transcript": transcriptions[session_id],
        "status": transcription_statuses.get(session_id, "ready"),
    }


async def close_peer_connections():
    connections = list(peer_connections)
    await asyncio.gather(
        *(connection.close() for connection in connections),
        return_exceptions=True,
    )
    peer_connections.clear()

    if audio_tasks:
        await asyncio.gather(*list(audio_tasks), return_exceptions=True)