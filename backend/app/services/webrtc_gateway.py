import asyncio
import logging
import uuid
import numpy as np
from typing import Dict, Optional
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaRelay

from app.services.audio_pipeline import pipeline_manager
from app.utils.audio_utils import resample_linear

logger = logging.getLogger("auralis.webrtc")

class AudioReceiverTrack:
    """Consumes audio frames from WebRTC peer connection and feeds pipeline."""
    def __init__(self, track: MediaStreamTrack, session_id: str):
        self.track = track
        self.session_id = session_id
        self._running = True
        self._task = asyncio.create_task(self._process_frames())

    async def _process_frames(self):
        pipeline = pipeline_manager.get_or_create_session(self.session_id)
        logger.info("AudioReceiverTrack started for session: %s", self.session_id)
        try:
            while self._running:
                frame = await self.track.recv()
                # frame is an av.AudioFrame
                ndarray = frame.to_ndarray()
                # Normalize format: if stereo, average to mono
                if ndarray.ndim == 2:
                    if ndarray.shape[0] == 2:  # 2 channels
                        ndarray = ndarray.mean(axis=0)
                    elif ndarray.shape[1] == 2:
                        ndarray = ndarray.mean(axis=1)
                
                # Convert to float32 (-1.0 to 1.0)
                if ndarray.dtype == np.int16:
                    float_arr = ndarray.astype(np.float32) / 32768.0
                else:
                    float_arr = ndarray.astype(np.float32)
                    
                # Resample to 16kHz if needed
                if frame.sample_rate != 16000:
                    float_arr = resample_linear(float_arr, frame.sample_rate, 16000)
                    
                await pipeline.handle_audio_chunk(float_arr)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.info("WebRTC audio track closed or finished: %s", str(e))
        finally:
            logger.info("AudioReceiverTrack ended for session: %s", self.session_id)

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

class WebRTCGateway:
    def __init__(self):
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.tracks: Dict[str, AudioReceiverTrack] = {}

    async def handle_offer(self, sdp: str, offer_type: str, session_id: Optional[str] = None) -> str:
        """Handle WebRTC SDP offer and generate SDP answer."""
        if not session_id:
            session_id = str(uuid.uuid4())

        # Cleanup existing connection if any
        await self.close_session(session_id)

        pc = RTCPeerConnection()
        self.peer_connections[session_id] = pc

        @pc.on("track")
        def on_track(track):
            if track.kind == "audio":
                logger.info("Received WebRTC audio track for session %s", session_id)
                receiver = AudioReceiverTrack(track, session_id)
                self.tracks[session_id] = receiver

        @pc.on("connectionstatechange")
        async def on_state_change():
            logger.info("WebRTC connection state for %s: %s", session_id, pc.connectionState)
            if pc.connectionState in ["failed", "closed"]:
                await self.close_session(session_id)

        # Set remote description
        offer = RTCSessionDescription(sdp=sdp, type=offer_type)
        await pc.setRemoteDescription(offer)

        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        logger.info("WebRTC offer processed and answer created for session: %s", session_id)
        return pc.localDescription.sdp

    async def close_session(self, session_id: str):
        """Release WebRTC peer connection and associated tracks."""
        if session_id in self.tracks:
            self.tracks[session_id].stop()
            del self.tracks[session_id]

        if session_id in self.peer_connections:
            pc = self.peer_connections[session_id]
            await pc.close()
            del self.peer_connections[session_id]
            logger.info("WebRTC connection closed for session: %s", session_id)

webrtc_gateway = WebRTCGateway()
