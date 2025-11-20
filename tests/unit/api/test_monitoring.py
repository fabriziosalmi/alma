"""Tests for monitoring API routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from alma.api.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestMonitoring:
    """Tests for monitoring endpoints."""

    async def test_health_endpoint(self, client: AsyncClient) -> None:
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_metrics_endpoint(self, client: AsyncClient) -> None:
        """Test Prometheus metrics endpoint."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        # Metrics are returned as text/plain
        assert "text/plain" in response.headers.get("content-type", "")
