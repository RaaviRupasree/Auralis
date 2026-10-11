from fastapi import APIRouter, HTTPException
from app.schemas.api_schemas import WebRTCOfferRequest, WebRTCAnswerResponse
from app.services.webrtc_gateway import webrtc_gateway

router = APIRouter()

@router.post("/webrtc/offer", response_model=WebRTCAnswerResponse)
async def webrtc_offer(offer_req: WebRTCOfferRequest):
    try:
        session_id = offer_req.session_id or "default_session"
        answer_sdp = await webrtc_gateway.handle_offer(
            sdp=offer_req.sdp,
            offer_type=offer_req.type,
            session_id=session_id
        )
        return WebRTCAnswerResponse(
            sdp=answer_sdp,
            type="answer",
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WebRTC signaling failed: {str(e)}")

@router.post("/webrtc/disconnect")
async def webrtc_disconnect(session_id: str):
    await webrtc_gateway.close_session(session_id)
    return {"status": "disconnected", "session_id": session_id}
