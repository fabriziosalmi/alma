"""Authentication middleware."""

from __future__ import annotations
import logging
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


class APIKeyAuth:
    """API Key authentication handler."""

    def __init__(self):
        """Initialize API key authentication."""
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        self._load_api_keys()

    def _load_api_keys(self) -> None:
        """Load API keys from environment variables."""
        # Check if auth is enabled
        self.enabled = os.getenv("ALMA_AUTH_ENABLED", "true").lower() == "true"
        
        if not self.enabled:
            self.valid_keys = set()
            return

        # Load API keys from environment
        env_keys = os.getenv("ALMA_API_KEYS", "")
        
        if env_keys:
            # Use keys from environment
            self.valid_keys = {key.strip() for key in env_keys.split(",") if key.strip()}
        else:
            # Default development keys
            self.valid_keys = {
                "test-api-key-12345",
                "dev-api-key-67890",
                "prod-api-key-abcdef",
            }

    def validate_key(self, api_key: Optional[str]) -> bool:
        """
        Validate an API key.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        # If auth is disabled, allow all
        if not self.enabled:
            return True

        # Check if key is valid
        if not api_key:
            return False

        return api_key in self.valid_keys


# Global authentication instance
_auth_instance: Optional[APIKeyAuth] = None


def get_auth() -> APIKeyAuth:
    """Get or create global auth instance."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = APIKeyAuth()
    return _auth_instance


async def verify_api_key(
    api_key: Optional[str] = Security(APIKeyHeader(name="X-API-Key", auto_error=False))
) -> str:
    """
    FastAPI dependency for API key verification.

    Args:
        api_key: API key from request header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    auth = get_auth()

    # If auth is disabled, allow request
    if not auth.enabled:
        return "auth-disabled"

    # Validate the key
    if not auth.validate_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key. Please provide a valid X-API-Key header.",
        )

    return api_key


# Optional dependency - doesn't fail if no key provided
async def optional_api_key(
    api_key: Optional[str] = Security(APIKeyHeader(name="X-API-Key", auto_error=False))
) -> Optional[str]:
    """
    Optional API key verification (doesn't raise exception).

    Args:
        api_key: API key from request header

    Returns:
        API key if valid, None otherwise
    """
    auth = get_auth()

    if not auth.enabled:
        return None

    if auth.validate_key(api_key):
        return api_key

    return None
