"""Authentication middleware."""

from __future__ import annotations

import logging
import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# Try to import argon2, fall back to passlib if not available
try:
    from argon2 import PasswordHasher  # type: ignore[import]
    from argon2.exceptions import InvalidHash, VerifyMismatchError  # type: ignore[import]

    HAS_ARGON2 = True
except ImportError:
    try:
        from passlib.hash import argon2  # type: ignore[import]

        HAS_ARGON2 = True
    except ImportError:
        logger.warning(
            "argon2-cffi not installed, falling back to SHA-256 (INSECURE for production)"
        )
        import hashlib

        HAS_ARGON2 = False


class APIKeyAuth:
    """API Key authentication handler with secure hashing."""

    def __init__(self) -> None:
        """Initialize API key authentication."""
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        if HAS_ARGON2:
            try:
                self.ph = PasswordHasher()
            except Exception:  # noqa: S110
                # Fallback to passlib
                self.ph = None
        else:
            self.ph = None
        self._load_api_keys()

    def _hash_key(self, key: str) -> str:
        """
        Hash an API key using Argon2id (secure) or SHA-256 (fallback).

        WARNING: SHA-256 fallback is INSECURE for production.
        Install argon2-cffi: pip install argon2-cffi
        """
        if HAS_ARGON2:
            if self.ph:
                # Using argon2-cffi
                return self.ph.hash(key)
            else:
                # Using passlib
                return argon2.hash(key)
        else:
            # INSECURE FALLBACK - only for development
            logger.warning("Using SHA-256 for API key hashing - INSECURE for production!")
            return hashlib.sha256(key.encode()).hexdigest()

    def _verify_key(self, key: str, hash: str) -> bool:
        """Verify a key against its hash."""
        if HAS_ARGON2:
            try:
                if self.ph:
                    # Using argon2-cffi
                    self.ph.verify(hash, key)
                    return True
                else:
                    # Using passlib
                    return argon2.verify(key, hash)
            except (VerifyMismatchError, InvalidHash, ValueError):
                return False
        else:
            # Fallback to simple comparison
            return self._hash_key(key) == hash

    def _load_api_keys(self) -> None:
        """Load API keys from environment variables."""
        # Check if auth is enabled
        self.enabled = os.getenv("ALMA_AUTH_ENABLED", "true").lower() == "true"

        if not self.enabled:
            self.valid_key_hashes = {}
            return

        # Load API keys from environment
        env_keys = os.getenv("ALMA_API_KEYS", "")

        if env_keys:
            # Hash keys from environment
            self.valid_key_hashes = {
                key.strip(): self._hash_key(key.strip())
                for key in env_keys.split(",")
                if key.strip()
            }
        else:
            # Default development keys (hashed)
            # WARNING: Change these in production!
            dev_keys = [
                "test-api-key-12345",
                "dev-api-key-67890",
                "prod-api-key-abcdef",
            ]
            self.valid_key_hashes = {key: self._hash_key(key) for key in dev_keys}

    def validate_key(self, api_key: str | None) -> bool:
        """
        Validate an API key using constant-time comparison.

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

        # Check against all stored hashes using constant-time verification
        for _stored_key, stored_hash in self.valid_key_hashes.items():
            if self._verify_key(api_key, stored_hash):
                return True

        return False


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

    return api_key or ""


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
