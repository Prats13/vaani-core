"""
Vaani API Routes
================
FastAPI routes for session management and health checks.
Simplified: no Redis, in-memory session management.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uuid
import time

from core.livekit_manager import livekit_manager
from core.config import settings, logger
from core.auth import verify_api_key

router = APIRouter()


class ModelConfig(BaseModel):
    agent_type: str = "farmer_advisory"
    llm_config: Optional[str] = None
    stt_config: Optional[str] = None
    tts_config: Optional[str] = None


class StartSessionRequest(BaseModel):
    user_id: str
    config: Optional[ModelConfig] = None


class StartSessionResponse(BaseModel):
    room_name: str
    access_token: str
    livekit_url: str
    session_id: str


@router.post("/start_session", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest, api_key: str = Depends(verify_api_key)):
    """
    Create a new LiveKit room and generate access token.
    Requires API key authentication via X-API-Key header.
    """
    try:
        session_id = f"{uuid.uuid4()}_{int(time.time())}"

        # Generate dynamic room name
        room_name = livekit_manager.generate_room_name()

        # Create room
        await livekit_manager.create_room(room_name)

        # Generate access token
        access_token = livekit_manager.generate_access_token(
            room_name=room_name,
            identity=request.user_id
        )

        logger.debug(f"API | ROUTES | Session started: room={room_name}, user={request.user_id}")

        return StartSessionResponse(
            room_name=room_name,
            access_token=access_token,
            livekit_url=settings.external_livekit_url,
            session_id=session_id
        )

    except Exception as e:
        logger.error(f"API | ROUTES | Failed to start session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vaani"}
