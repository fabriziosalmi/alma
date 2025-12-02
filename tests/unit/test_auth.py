"""Tests for API Key authentication."""

import os

import pytest
from fastapi import HTTPException, status
from fastapi.security import APIKeyHeader

from alma.middleware.auth import APIKeyAuth, verify_api_key


@pytest.fixture(scope="module", autouse=True)
def enable_auth_for_module():
    """Enable authentication for all tests in this module."""
    original_value = os.environ.get("ALMA_AUTH_ENABLED")
    os.environ["ALMA_AUTH_ENABLED"] = "true"
    os.environ["ALMA_API_KEYS"] = (
        "test-api-key-12345,dev-api-key-67890,prod-api-key-abcdef,another-valid-key"
    )

    yield

    # Restore original value
    if original_value is not None:
        os.environ["ALMA_AUTH_ENABLED"] = original_value
    else:
        os.environ.pop("ALMA_AUTH_ENABLED", None)
    os.environ.pop("ALMA_API_KEYS", None)


class TestAPIKeyAuth:
    """Test API Key authentication middleware."""

    def test_api_key_header_scheme(self):
        """Test API key header is properly configured."""
        auth = APIKeyAuth()
        assert isinstance(auth.api_key_header, APIKeyHeader)
        assert auth.api_key_header.model.name == "X-API-Key"

    def test_valid_api_key(self):
        """Test authentication with valid API key."""
        auth = APIKeyAuth()
        # Using default test key
        result = auth.validate_key("test-api-key-12345")
        assert result is True

    def test_invalid_api_key(self):
        """Test authentication fails with invalid key."""
        auth = APIKeyAuth()
        result = auth.validate_key("invalid-key")
        assert result is False

    def test_empty_api_key(self):
        """Test authentication fails with empty key."""
        auth = APIKeyAuth()
        result = auth.validate_key("")
        assert result is False

    def test_none_api_key(self):
        """Test authentication fails with None key."""
        auth = APIKeyAuth()
        result = auth.validate_key(None)
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self):
        """Test verify_api_key dependency with valid key."""
        result = await verify_api_key("test-api-key-12345")
        assert result == "test-api-key-12345"

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self):
        """Test verify_api_key dependency with invalid key."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("invalid-key")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid API key" in str(exc_info.value.detail)

    def test_multiple_valid_keys(self):
        """Test multiple API keys are supported."""
        auth = APIKeyAuth()

        # Test default keys
        assert auth.validate_key("test-api-key-12345") is True
        assert auth.validate_key("dev-api-key-67890") is True
        assert auth.validate_key("prod-api-key-abcdef") is True

    def test_api_key_from_env(self, monkeypatch):
        """Test API keys loaded from environment variables."""
        monkeypatch.setenv("ALMA_API_KEYS", "custom-key-1,custom-key-2,custom-key-3")

        auth = APIKeyAuth()
        assert auth.validate_key("custom-key-1") is True
        assert auth.validate_key("custom-key-2") is True
        assert auth.validate_key("custom-key-3") is True
        assert auth.validate_key("test-api-key-12345") is False

    def test_auth_disabled_in_dev(self, monkeypatch):
        """Test authentication can be disabled in development."""
        monkeypatch.setenv("ALMA_AUTH_ENABLED", "false")

        auth = APIKeyAuth()
        # Any key should work when disabled
        assert auth.validate_key("any-random-key") is True
        assert auth.validate_key("") is True


class TestAPIKeyIntegration:
    """Integration tests for API key authentication."""

    @pytest.fixture
    async def test_client(self, test_db_session):
        """Create test client with auth enabled and database override."""
        import os

        from httpx import ASGITransport, AsyncClient

        from alma.api.main import app
        from alma.core.database import get_session

        # Enable auth and set valid keys
        os.environ["ALMA_AUTH_ENABLED"] = "true"
        os.environ["ALMA_API_KEYS"] = "test-api-key-12345"

        # Override database session
        async def override_get_session():
            yield test_db_session

        app.dependency_overrides[get_session] = override_get_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

        # Cleanup
        app.dependency_overrides.clear()
        os.environ.pop("ALMA_AUTH_ENABLED", None)
        os.environ.pop("ALMA_API_KEYS", None)

    @pytest.mark.asyncio
    async def test_blueprint_create_without_key(self, test_client):
        """Test blueprint creation rejects requests without API key."""
        response = await test_client.post(
            "/api/v1/blueprints/", json={"version": "1.0", "name": "test", "resources": []}
        )
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_blueprint_create_with_valid_key(self, test_client):
        """Test blueprint creation accepts valid API key."""
        response = await test_client.post(
            "/api/v1/blueprints/",
            json={"version": "1.0", "name": "test", "resources": []},
            headers={"X-API-Key": "test-api-key-12345"},
        )
        # Should not be 403 (may be 201, 422, or other depending on validation)
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_blueprint_create_with_invalid_key(self, test_client):
        """Test blueprint creation rejects invalid API key."""
        response = await test_client.post(
            "/api/v1/blueprints/",
            json={"version": "1.0", "name": "test", "resources": []},
            headers={"X-API-Key": "invalid-key-xyz"},
        )
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_ipr_create_requires_auth(self, test_client):
        """Test IPR creation requires authentication."""
        response = await test_client.post(
            "/api/v1/ipr/", json={"title": "Test IPR", "blueprint_id": 1}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_tools_execute_requires_auth(self, test_client):
        """Test tools execution requires authentication."""
        response = await test_client.post(
            "/api/v1/tools/execute", json={"tool_name": "validate_blueprint", "parameters": {}}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_public_endpoints_no_auth(self, test_client):
        """Test public endpoints don't require authentication."""
        # Health check should always be public
        response = await test_client.get("/api/v1/monitoring/health/detailed")
        assert response.status_code in [200, 503]  # Health status, not auth error

        # Metrics should be public
        response = await test_client.get("/metrics")
        assert response.status_code != 403
