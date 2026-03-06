"""
API Authentication Module
Provides API key authentication for public endpoints.

To generate a new API key, run:
    python -m core.api_key_generator
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from core.config import settings, logger
from core.api_key_generator import APIKeyGenerator

# Define API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyAuth:
    """API Key authentication utilities"""

    @staticmethod
    def _constant_time_compare(val1: str, val2: str) -> bool:
        """Constant-time string comparison to prevent timing attacks."""
        if len(val1) != len(val2):
            return False
        result = 0
        for x, y in zip(val1, val2):
            result |= ord(x) ^ ord(y)
        return result == 0


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from request header.

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        logger.error("API | AUTH | Missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include 'X-API-Key' header in your request.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    if not APIKeyAuth._constant_time_compare(api_key, settings.vaani_api_key):
        logger.error("API | AUTH | Invalid API key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

    return api_key
