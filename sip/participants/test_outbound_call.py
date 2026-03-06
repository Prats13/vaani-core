"""
Test outbound call via SIP trunk.
Uses the test payload from test_outbound_participant_aip_to_line.json
"""
import asyncio
import json
import os
from pathlib import Path

from sip.participants.create_sip_participant import create_outbound_sip_participant


async def main():
    # Load test payload
    payload_path = Path(__file__).parent / "test_outbound_participant_aip_to_line.json"
    with open(payload_path) as f:
        payload = json.load(f)

    agent_params = payload["agent_params"]
    agent_config = payload["agent_config"]
    call_config = payload["call_config"]

    phone_number = call_config["call_to"]
    exophone_number = call_config["call_from"]

    # participant_attributes: agent_config + call_config as flat key-value strings
    participant_attributes = {
        **{str(k): str(v) for k, v in agent_config.items()},
        **{str(k): str(v) for k, v in call_config.items()},
    }

    # participant_metadata: agent_params as JSON string (native types preserved)
    participant_metadata = json.dumps(agent_params)

    # SIP headers
    headers = {}
    if exophone_number:
        sip_endpoint = os.getenv("LIVEKIT_SIP_ENDPOINT", "sip.freo.app")
        headers["P-Asserted-Identity"] = f"<sip:{exophone_number}@{sip_endpoint}>"

    print(f"Initiating outbound call to {phone_number}...")
    print(f"Agent type: {agent_config['agent_type']}")
    print(f"STT: {agent_config['stt_config']}")
    print(f"LLM: {agent_config['llm_config']}")
    print(f"TTS: {agent_config['tts_config']}")
    print(f"From: {exophone_number}")
    print()

    try:
        result = await create_outbound_sip_participant(
            customer_name=agent_params.get("customer_name", "Customer"),
            customer_phone_number=phone_number,
            customer_metadata=participant_metadata,
            headers=headers,
            participant_attributes=participant_attributes,
        )

        print(f"Call initiated successfully!")
        print(f"  Room:           {result.room_name}")
        print(f"  Participant ID: {result.participant_id}")
        print(f"  Identity:       {result.participant_identity}")

    except Exception as e:
        print(f"Call failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())