"""
Generic Room Event Handler
==========================
Registers ALL LiveKit room event listeners immediately after ctx.connect().
Business-logic callbacks are injected via a mutable CallbackRegistry dict —
listeners read from it at event-fire time, so callbacks can be set/updated
at any point after registration.

Usage:
    # Phase 1 — in worker, right after ctx.connect()
    callbacks = create_callback_registry()
    started_track_sids = setup_room_listeners(room, log_context, callbacks)

    # Phase 2 — in dispatcher/agent, once session_data exists
    callbacks["on_sip_connected"] = lambda p: asyncio.create_task(...)
    callbacks["on_client_disconnect"] = lambda p: asyncio.create_task(...)
    callbacks["on_audio_track_published"] = lambda pub, p: asyncio.create_task(...)
"""
from typing import Callable, Optional, Dict, Set
from livekit import rtc
from core.config import logger


# Type alias for the callback registry
CallbackRegistry = Dict[str, Optional[Callable]]


def create_callback_registry(
    on_sip_connected: Optional[Callable] = None,
    on_client_disconnect: Optional[Callable] = None,
    on_audio_track_published: Optional[Callable] = None,
) -> CallbackRegistry:
    """
    Create a mutable callback registry dict.
    Listeners always read the CURRENT value at event-fire time.
    """
    return {
        "on_sip_connected": on_sip_connected,
        "on_client_disconnect": on_client_disconnect,
        "on_audio_track_published": on_audio_track_published,
    }


def setup_room_listeners(
    room: rtc.Room,
    log_context: dict,
    callbacks: CallbackRegistry,
) -> Set[str]:
    """
    Register ALL LiveKit room event listeners on the given room.
    Returns started_track_sids set for egress dedup.
    """
    rn = log_context.get("room_name", "-")
    rf = log_context.get("root_folder", "CORE")
    sf = log_context.get("sub_file_path", "ROOM_EVENT_HANDLER")
    started_track_sids: Set[str] = set()

    # =========================================================================
    # CONNECTION — Participant
    # =========================================================================

    @room.on("participant_connected")
    def on_participant_connected(participant):
        logger.debug(f"{rn} | {rf} | {sf} | ParticipantConnected: {participant.identity} (SID: {participant.sid})")

        cb = callbacks.get("on_sip_connected")
        if participant.identity.startswith("sip_participant_") and cb:
            cb(participant)

    @room.on("participant_disconnected")
    def on_participant_disconnected(participant):
        logger.debug(f"{rn} | {rf} | {sf} | ParticipantDisconnected: {participant.identity} (SID: {participant.sid})")

        cb = callbacks.get("on_client_disconnect")
        if cb:
            cb(participant)

    # =========================================================================
    # CONNECTION — Client (self)
    # =========================================================================

    @room.on("reconnecting")
    def on_reconnecting():
        logger.debug(f"{rn} | {rf} | {sf} | Reconnecting...")

    @room.on("reconnected")
    def on_reconnected():
        logger.debug(f"{rn} | {rf} | {sf} | Reconnected")

    @room.on("disconnected")
    def on_room_disconnected():
        logger.debug(f"{rn} | {rf} | {sf} | RoomDisconnected: Entire room disconnected")

    @room.on("connection_state_changed")
    def on_connection_state_changed(state):
        logger.debug(f"{rn} | {rf} | {sf} | ConnectionStateChanged: {state}")

    # =========================================================================
    # TRACK — Remote
    # =========================================================================

    @room.on("track_published")
    def on_track_published(publication, participant):
        logger.debug(f"{rn} | {rf} | {sf} | TrackPublished: kind={publication.kind} sid={publication.sid} from {participant.identity}")

        cb = callbacks.get("on_audio_track_published")
        if int(publication.kind) == 1 and cb:
            cb(publication, participant)

    @room.on("track_unpublished")
    def on_track_unpublished(publication, participant):
        logger.debug(f"{rn} | {rf} | {sf} | TrackUnpublished: kind={publication.kind} from {participant.identity}")

    @room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        logger.debug(f"{rn} | {rf} | {sf} | TrackSubscribed: kind={publication.kind} sid={publication.sid} from {participant.identity}")

    @room.on("track_unsubscribed")
    def on_track_unsubscribed(track, publication, participant):
        logger.debug(f"{rn} | {rf} | {sf} | TrackUnsubscribed: kind={publication.kind} from {participant.identity}")

    @room.on("track_muted")
    def on_track_muted(participant, publication):
        logger.debug(f"{rn} | {rf} | {sf} | TrackMuted: kind={publication.kind} from {participant.identity}")

    @room.on("track_unmuted")
    def on_track_unmuted(participant, publication):
        logger.debug(f"{rn} | {rf} | {sf} | TrackUnmuted: kind={publication.kind} from {participant.identity}")

    # =========================================================================
    # TRACK — Local
    # =========================================================================

    @room.on("local_track_published")
    def on_local_track_published(publication, track):
        logger.debug(f"{rn} | {rf} | {sf} | LocalTrackPublished: kind={publication.kind} sid={publication.sid}")

        cb = callbacks.get("on_audio_track_published")
        if int(publication.kind) == 1 and cb:
            cb(publication, room.local_participant)

    @room.on("local_track_unpublished")
    def on_local_track_unpublished(publication, participant):
        logger.debug(f"{rn} | {rf} | {sf} | LocalTrackUnpublished: kind={publication.kind}")

    # =========================================================================
    # SPEAKER DYNAMICS
    # =========================================================================

    @room.on("active_speakers_changed")
    def on_active_speakers_changed(speakers):
        identities = [s.identity for s in speakers]
        logger.debug(f"{rn} | {rf} | {sf} | ActiveSpeakersChanged: {identities}")

    # =========================================================================
    # QUALITY & NETWORK
    # =========================================================================

    @room.on("connection_quality_changed")
    def on_connection_quality_changed(participant, quality):
        logger.debug(f"{rn} | {rf} | {sf} | ConnectionQualityChanged: {participant.identity} → {quality}")

    # =========================================================================
    # PARTICIPANT STATE
    # =========================================================================

    @room.on("participant_attributes_changed")
    def on_participant_attributes_changed(changed_attributes, participant):
        logger.debug(f"{rn} | {rf} | {sf} | ParticipantAttributesChanged: {participant.identity} → {changed_attributes}")

    @room.on("participant_metadata_changed")
    def on_participant_metadata_changed(participant, old_metadata, new_metadata):
        logger.debug(f"{rn} | {rf} | {sf} | ParticipantMetadataChanged: {participant.identity}")

    @room.on("participant_name_changed")
    def on_participant_name_changed(participant, old_name, new_name):
        logger.debug(f"{rn} | {rf} | {sf} | ParticipantNameChanged: {participant.identity} ({old_name} → {new_name})")

    # =========================================================================
    # ROOM STATE
    # =========================================================================

    @room.on("room_metadata_changed")
    def on_room_metadata_changed(old_metadata, new_metadata):
        logger.debug(f"{rn} | {rf} | {sf} | RoomMetadataChanged")

    @room.on("data_received")
    def on_data_received(data_packet):
        logger.debug(f"{rn} | {rf} | {sf} | DataReceived: {len(data_packet.data)} bytes")

    # =========================================================================
    # CATCH-UP: Process remote tracks already published before listeners registered
    # =========================================================================

    cb = callbacks.get("on_audio_track_published")
    if cb:
        for p in room.remote_participants.values():
            for track_pub in p.track_publications.values():
                if int(track_pub.kind) == 1 and track_pub.sid not in started_track_sids:
                    cb(track_pub, p)

    logger.debug(f"{rn} | {rf} | {sf} | All room event listeners registered (callbacks bind on fire)")

    return started_track_sids
