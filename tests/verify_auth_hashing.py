import hashlib
import os
import sys

# Add project root to path
sys.path.append(".")

# Set environment variables before importing auth
os.environ["ALMA_AUTH_ENABLED"] = "true"
os.environ["ALMA_API_KEYS"] = "secret-key-1,secret-key-2"

from alma.middleware.auth import APIKeyAuth


def test_auth_hashing():
    print("\n--- Testing API Key Hashing ---")

    auth = APIKeyAuth()

    # 1. Verify keys are NOT stored in plaintext
    print("Checking internal storage...")
    assert "secret-key-1" not in auth.valid_key_hashes, "Key stored in plaintext!"
    assert "secret-key-2" not in auth.valid_key_hashes, "Key stored in plaintext!"

    # 2. Verify hashes are stored
    expected_hash = hashlib.sha256(b"secret-key-1").hexdigest()
    print(f"Expected: {expected_hash}")
    print(f"Stored: {auth.valid_key_hashes}")
    assert expected_hash in auth.valid_key_hashes, "Hash not found in storage!"
    print("✓ Keys are stored as hashes")

    # 3. Verify validation works
    print("Testing validation...")
    assert auth.validate_key("secret-key-1"), "Valid key rejected"
    assert auth.validate_key("secret-key-2"), "Valid key rejected"
    assert not auth.validate_key("wrong-key"), "Invalid key accepted"
    print("✓ Validation logic works")

    print("✓ Secret Management Verified")


if __name__ == "__main__":
    test_auth_hashing()
