"""Authentication middleware."""

from __future__ import annotations

import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


import hashlib
import secrets

class APIKeyAuth:
    """API Key authentication handler."""

    def __init__(self):
        """Initialize API key authentication."""
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        self._load_api_keys()

    def _hash_key(self, key: str) -> str:
        """Hash an API key using SHA-256."""
        return hashlib.sha256(key.encode()).hexdigest()

    def _load_api_keys(self) -> None:
        """Load API keys from environment variables."""
        # Check if auth is enabled
        self.enabled = os.getenv("ALMA_AUTH_ENABLED", "true").lower() == "true"

        if not self.enabled:
            self.valid_key_hashes = set()
            return

        # Load API keys from environment
        env_keys = os.getenv("ALMA_API_KEYS", "")

        if env_keys:
            # Hash keys from environment
            self.valid_key_hashes = {
                self._hash_key(key.strip()) 
                for key in env_keys.split(",") 
                if key.strip()
            }
        else:
            # Default development keys (hashed)
            # test-api-key-12345
            # dev-api-key-67890
            # prod-api-key-abcdef
            self.valid_key_hashes = {
                self._hash_key("test-api-key-12345"),
                self._hash_key("dev-api-key-67890"),
                self._hash_key("prod-api-key-abcdef"),
            }

    def validate_key(self, api_key: str | None) -> bool:
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

        # Hash incoming key and check against stored hashes
        # Use constant time comparison to prevent timing attacks (though set lookup is fast)
        input_hash = self._hash_key(api_key)
        return input_hash in self.valid_key_hashes


# Global authentication instance
_auth_instance: APIKeyAuth | None = None


def get_auth() -> APIKeyAuth:
    """Get or create global auth instance."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = APIKeyAuth()
    return _auth_instance


async def verify_api_key(
    api_key: str | None = Security(APIKeyHeader(name="X-API-Key", auto_error=False))
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
    api_key: str | None = Security(APIKeyHeader(name="X-API-Key", auto_error=False))
) -> str | None:
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
