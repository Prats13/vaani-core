"""
LiveKit Manager
===============
Handles all LiveKit server interactions including room creation and token generation.
Ported from freo-speech, simplified for Vaani (no S3 egress).
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from livekit import api
from livekit.api import CreateRoomRequest, AccessToken, VideoGrants, LiveKitAPI, ListRoomsRequest

from core.config import settings, logger


class LiveKitManager:
    """Handles all LiveKit server interactions including room creation and token generation"""

    def __init__(self):
        self.livekit_api = None

    async def initialize(self):
        """Initialize LiveKit API client - called during app startup"""
        self.livekit_api = LiveKitAPI(
            settings.livekit_url,
            settings.livekit_api_key,
            settings.livekit_api_secret
        )

    @staticmethod
    def generate_room_name() -> str:
        """Generate a unique room name"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"vaani_{timestamp}_{unique_id}"

    async def create_room(self, room_name: str):
        """Create a new LiveKit room"""
        try:
            request = CreateRoomRequest(
                name=room_name,
                empty_timeout=320,
                max_participants=5,
            )
            await self.livekit_api.room.create_room(request)
            return None
        except Exception as e:
            try:
                response = await self.livekit_api.room.list_rooms(ListRoomsRequest())
                for room in response.rooms:
                    if room.name == room_name:
                        return room
                raise e
            except:
                raise e

    @staticmethod
    def generate_access_token(
        room_name: str,
        identity: str,
        name: Optional[str] = None,
        ttl: int = 3600
    ) -> str:
        """Generate access token for a participant to join the room"""
        grants = VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        )

        token = (AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
                .with_identity(identity)
                .with_name(name or identity)
                .with_ttl(timedelta(seconds=ttl))
                .with_grants(grants))

        return token.to_jwt()

    async def delete_room(self, room_name: str) -> None:
        """Delete a room"""
        await self.livekit_api.room.delete_room(api.DeleteRoomRequest(room=room_name))

    async def list_rooms(self) -> list[api.Room]:
        """List all active rooms"""
        response = await self.livekit_api.room.list_rooms(ListRoomsRequest())
        return response.rooms

    async def close(self):
        """Close the LiveKit API client and cleanup resources"""
        if self.livekit_api:
            await self.livekit_api.aclose()
            self.livekit_api = None


livekit_manager = LiveKitManager()
