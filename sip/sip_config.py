import os
import json

from dotenv import load_dotenv
from google.protobuf.duration_pb2 import Duration

load_dotenv()

LIVEKIT_SIP_ENDPOINT=os.getenv("LIVEKIT_SIP_ENDPOINT")

# OUTBOUND TRUNK INFO
OUTBOUND_TRUNK_ID=os.getenv("OUTBOUND_TRUNK_ID")
OUTBOUND_TRUNK_NAME=os.getenv("OUTBOUND_TRUNK_NAME", "freo-sip-outbound")
OUTBOUND_TRUNK_ADDRESS=os.getenv("OUTBOUND_TRUNK_ADDRESS")
OUTBOUND_TRUNK_DESTINATION_COUNTRY=os.getenv("OUTBOUND_TRUNK_DESTINATION_COUNTRY", "IN")
OUTBOUND_TRUNK_NUMBERS=json.loads(os.getenv("OUTBOUND_TRUNK_NUMBERS", '[]'))
OUTBOUND_TRUNK_AUTH_USER_NAME=os.getenv("OUTBOUND_TRUNK_AUTH_USER_NAME")
OUTBOUND_TRUNK_AUTH_USER_PASSWORD=os.getenv("OUTBOUND_TRUNK_AUTH_USER_PASSWORD")
_outbound_ringing_timeout_seconds = int(os.getenv("OUTBOUND_RINGING_TIMEOUT", "80"))
OUTBOUND_RINGING_TIMEOUT = Duration(seconds=_outbound_ringing_timeout_seconds)

# Exotel requires From header domain = account_sid.pstn.exotel.com
# e.g. freo62m.pstn.exotel.com
EXOTEL_SIP_DOMAIN=os.getenv("EXOTEL_SIP_DOMAIN", "")

# INBOUND TRUNK INFO
INBOUND_TRUNK_NAME=os.getenv("INBOUND_TRUNK_NAME")
INBOUND_ALLOWED_NUMBERS=json.loads(os.getenv("INBOUND_ALLOWED_NUMBERS", '[]'))
INBOUND_ALLOWED_ADDRESSES=json.loads(os.getenv("INBOUND_ALLOWED_ADDRESSES", '[]'))
INBOUND_HEADERS_TO_ATTRIBUTES = {
      "X-Exotel-CallSid": "exotel_call_sid",
      "X-Exotel-LegSid": "exotel_leg_sid",
      "X-Exotel-TrunkSid": "exotel_trunk_sid",
      "P-Asserted-Identity": "exotel_asserted_identity"
  }
_inbound_ringing_timeout_seconds = int(os.getenv("INBOUND_RINGING_TIMEOUT", "80"))
INBOUND_RINGING_TIMEOUT = Duration(seconds=_inbound_ringing_timeout_seconds)
_inbound_max_call_duration_seconds = int(os.getenv("INBOUND_MAX_CALL_DURATION", "3600"))
INBOUND_MAX_CALL_DURATION = Duration(seconds=_inbound_max_call_duration_seconds)

# DISPATCH RULE
DISPATCH_RULE_ASSOCIATED_TRUNK_IDS = json.loads(os.getenv("DISPATCH_RULE_ASSOCIATED_TRUNK_IDS", '[]'))
DISPATCH_RULE_NAME = os.getenv("DISPATCH_RULE_NAME", "freo-inbound-dispatch")
DISPATCH_RULE_ATTRIBUTES = {
    "call_direction": "inbound",
    "call_type": "pstn",
    "call_provider": "exotel"
}

# Room configuration for inbound calls
INBOUND_ROOM_EMPTY_TIMEOUT = int(os.getenv("INBOUND_ROOM_EMPTY_TIMEOUT", "300"))
INBOUND_ROOM_DEPARTURE_TIMEOUT = int(os.getenv("INBOUND_ROOM_DEPARTURE_TIMEOUT", "20"))
INBOUND_ROOM_MAX_PARTICIPANTS = int(os.getenv("INBOUND_ROOM_MAX_PARTICIPANTS", "5"))

