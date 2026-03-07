"""
Vaani Agent Registry
====================
Maps agent_type strings to their session starter functions.
To add a new outbound agent:
  1. Build your agent under agents/<your_agent>/
  2. Register it here with a single entry in OUTBOUND_AGENT_REGISTRY.
"""
from typing import Callable, Dict

from agents.vaani_onboarding.session import start_onboarding_session

OUTBOUND_AGENT_REGISTRY: Dict[str, Callable] = {
    "farmer_onboarding": start_onboarding_session,
    # "farmer_advisory": start_advisory_session,  ← add new agents here
}
