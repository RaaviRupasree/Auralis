import asyncio
import logging
import uuid
from collections import deque

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError
from av import AudioResampler
import numpy as np

from services.emotion_service import classify_emotion
from services.llm_service import LLMServiceError, generate_response
from services.vad_service import (
    SAMPLE_RATE,
    SPEECH_PADDING_SAMPLE_COUNT,
    StreamingSileroVAD,
)
from services.whisper_service import transcribe_samples
from utils.latency import elapsed_seconds, start_timer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
peer_connections = set()
audio_tasks = set()
transcriptions = {}
transcription_statuses = {}
segment_results = {}
capture_statuses = {}
pending_transcriptions = {}
transcription_lock = asyncio.Lock()
SILENCE_RMS_THRESHOLD = 0.003
PRE_ROLL_FRAME_COUNT = 6


def _has_audio_energy(audio_samples):
    if audio_samples.size == 0:
        return False

    rms = float(np.sqrt(np.mean(np.square(audio_samples))))
    return rms >= SILENCE_RMS_THRESHOLD


async def _analyze_segment(
    session_id,
    result_index,
    audio_samples,
    audio_started_at,
):
    async def transcribe():
        try:
            async with transcription_lock:
                return await asyncio.to_thread(transcribe_samples, audio_samples)
        except Exception:
            logger.exception("Faster-Whisper transcription failed")
            return None

    async def detect_emotion():
        try:
            return await asyncio.to_thread(classify_emotion, audio_samples)
        except Exception:
            logger.exception("Wav2Vec2 emotion detection failed")
            return None

    try:
        logger.info("Transcribing completed speech segment...")
        text, emotion = await asyncio.gather(transcribe(), detect_emotion())
        result = segment_results[session_id][result_index]
        if text is None:
            result["transcript_status"] = "error"
            transcription_statuses[session_id] = "error"
        else:
            result["transcript"] = text
            result["transcript_status"] = "ready"
            if text:
                current_text = transcriptions.get(session_id, "")
                transcriptions[session_id] = " ".join(
                    part for part in (current_text, text) if part
                )
                latency = elapsed_seconds(audio_started_at)
                logger.info("Transcript: %s", text)
                logger.info("Transcription latency: %.2f seconds", latency)

        if emotion is None:
            result["emotion_status"] = "error"
        else:
            result["emotion"] = {
                "label": emotion.label,
                "confidence": emotion.confidence,
            }
            result["emotion_status"] = "ready"
            logger.info(
                "Wav2Vec2 emotion: %s (confidence %.2f)",
                emotion.label,
                emotion.confidence,
            )

        if text is None or not text.strip():
            result["response_status"] = "skipped"
        else:
            result["response_status"] = "processing"
            try:
                llm_result = await asyncio.to_thread(
                    generate_response,
                    text,
                    emotion.label if emotion is not None else "unknown",
                    emotion.confidence if emotion is not None else 0.0,
                )
            except LLMServiceError as error:
                result["response_status"] = "error"
                result["response_error"] = str(error)
                logger.error("LLM context response failed: %s", error)
            except Exception:
                result["response_status"] = "error"
                result["response_error"] = "Could not generate an LLM response."
                logger.exception("Unexpected LLM context response failure")
            else:
                result["response"] = llm_result.text
                result["llm_latency_ms"] = llm_result.latency_ms
                result["response_status"] = "ready"
    finally:
        remaining = pending_transcriptions.get(session_id, 1) - 1
        if remaining > 0:
            pending_transcriptions[session_id] = remaining
            transcription_statuses[session_id] = (
                "error"
                if any(
                    item["transcript_status"] == "error"
                    for item in segment_results.get(session_id, [])
                )
                else "processing"
            )
        else:
            pending_transcriptions.pop(session_id, None)
            if transcription_statuses.get(session_id) != "error":
                transcription_statuses[session_id] = capture_statuses.get(
                    session_id, "listening"
                )


def _queue_transcription(session_id, audio_samples, audio_started_at):
    if not _has_audio_energy(audio_samples):
        return

    pending_transcriptions[session_id] = (
        pending_transcriptions.get(session_id, 0) + 1
    )
    result_index = len(segment_results[session_id])
    segment_results[session_id].append(
        {
            "transcript": "",
            "transcript_status": "processing",
            "emotion": None,
            "emotion_status": "processing",
            "response": "",
            "response_status": "processing",
            "response_error": None,
            "llm_latency_ms": None,
        }
    )
    transcription_statuses[session_id] = "processing"
    task = asyncio.create_task(
        _analyze_segment(
            session_id,
            result_index,
            audio_samples,
            audio_started_at,
        )
    )
    audio_tasks.add(task)
    task.add_done_callback(audio_tasks.discard)


async def _receive_audio(track, session_id):
    resampler = AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
    vad = StreamingSileroVAD()
    pre_roll = deque(maxlen=PRE_ROLL_FRAME_COUNT)
    audio_buffer = []
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

                for vad_frame in vad.process(samples):
                    if vad_frame.speech_started:
                        audio_buffer = list(pre_roll)
                        audio_started_at = start_timer()
                        capture_statuses[session_id] = "speech_detected"
                        if pending_transcriptions.get(session_id, 0) == 0:
                            transcription_statuses[session_id] = "speech_detected"

                    if vad_frame.speech_active or audio_buffer:
                        audio_buffer.append(vad_frame.samples)

                    if (
                        not vad_frame.speech_active
                        and not vad_frame.speech_started
                        and not audio_buffer
                    ):
                        pre_roll.append(vad_frame.samples)

                    if vad_frame.speech_ended:
                        segment = np.concatenate(audio_buffer)
                        logger.info("Speech ended; processing completed segment")
                        trailing_silence = max(
                            0,
                            vad_frame.silence_sample_count
                            - SPEECH_PADDING_SAMPLE_COUNT,
                        )
                        if trailing_silence:
                            segment = segment[:-trailing_silence]
                        _queue_transcription(
                            session_id,
                            segment,
                            audio_started_at or start_timer(),
                        )
                        logger.info("Silero VAD detected end of speech")
                        audio_buffer = []
                        audio_started_at = None
                        capture_statuses[session_id] = "listening"
                        if pending_transcriptions.get(session_id, 0) == 0:
                            transcription_statuses[session_id] = "listening"
    except MediaStreamError:
        logger.info("Audio track ended")
    except Exception:
        logger.exception("Could not process incoming audio")
    finally:
        if audio_buffer:
            segment = np.concatenate(audio_buffer)
            trailing_silence = max(
                0, vad.silence_sample_count - SPEECH_PADDING_SAMPLE_COUNT
            )
            if trailing_silence:
                segment = segment[:-trailing_silence]
            _queue_transcription(
                session_id,
                segment,
                audio_started_at or start_timer(),
            )


async def create_answer(sdp, offer_type):
    peer_connection = RTCPeerConnection()
    session_id = str(uuid.uuid4())
    peer_connections.add(peer_connection)
    transcriptions[session_id] = ""
    segment_results[session_id] = []
    capture_statuses[session_id] = "listening"
    transcription_statuses[session_id] = "listening"

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
        segment_results.pop(session_id, None)
        transcription_statuses.pop(session_id, None)
        capture_statuses.pop(session_id, None)
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
        "status": transcription_statuses.get(session_id, "listening"),
        "segments": [dict(item) for item in segment_results[session_id]],
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

    transcriptions.clear()
    segment_results.clear()
    transcription_statuses.clear()
    capture_statuses.clear()
    pending_transcriptions.clear()