import asyncio
import logging

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
peer_connections = set()
audio_tasks = set()


async def _receive_audio(track):
    try:
        while True:
            await track.recv()
    except MediaStreamError:
        logger.info("Audio track ended")


async def create_answer(sdp, offer_type):
    peer_connection = RTCPeerConnection()
    peer_connections.add(peer_connection)

    @peer_connection.on("track")
    def on_track(track):
        if track.kind != "audio":
            return

        print("Audio track received", flush=True)
        logger.info("Audio track received")
        task = asyncio.create_task(_receive_audio(track))
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
        await peer_connection.close()
        raise

    return {
        "sdp": peer_connection.localDescription.sdp,
        "type": peer_connection.localDescription.type,
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