from typing import Dict, List
from sqlalchemy.orm import Session
from app.crop.models import State

# Simple static fallback map if DB fails
STATIC_STATE_ALIASES = {
    "up": "Uttar Pradesh",
    "u.p.": "Uttar Pradesh",
    "mp": "Madhya Pradesh",
    "m.p.": "Madhya Pradesh",
    "ap": "Andhra Pradesh",
    "a.p.": "Andhra Pradesh",
    "j&k": "Jammu and Kashmir",
    "pondicherry": "Puducherry",
    "orissa": "Odisha",
    "tamilnadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "t.n.": "Tamil Nadu"
}

def build_alias_map_from_db(db: Session) -> Dict[str, str]:
    """
    Fetches the state mapping from crop.states and builds an alias lookup.
    Returns: {"alias_lower": "Canonical Name"}
    """
    alias_map = {}
    states = db.query(State).all()
    for state in states:
        canonical = state.state_name
        # Add canonical name itself as an alias (lowercase)
        alias_map[canonical.lower()] = canonical
        # Add all aliases
        if state.aliases:
            for alias in state.aliases:
                alias_map[str(alias).lower().strip()] = canonical
    
    # Merge with static fallback
    for k, v in STATIC_STATE_ALIASES.items():
        if k not in alias_map:
            alias_map[k] = v
            
    return alias_map

def normalize_state_token(token: str, alias_map: Dict[str, str]) -> str:
    """
    Given an input string (token) and mapping, returns the canonical state name.
    If not found exactly, returns the Titlecased original as fallback.
    """
    if not token:
        return ""
    
    token_lower = token.lower().strip()
    
    if token_lower in alias_map:
        return alias_map[token_lower]
        
    # Check partial match as fallback
    for k, canonical in alias_map.items():
        if k == token_lower or k in token_lower:
             return canonical
             
    # Fallback to general title case
    return token.title()
