"""Tests for enhanced health check monitoring."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestHealthCheckEnhancements:
    """Test enhanced health check functionality."""

    @pytest.mark.asyncio
    async def test_database_health_check_healthy(self):
        """Test database health check returns healthy when DB is up."""
        from alma.api.routes.monitoring import check_database_health

        # Mock successful database query
        with patch("alma.api.routes.monitoring.get_session") as mock_session:
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=MagicMock())
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await check_database_health()
            assert result["status"] == "healthy"
            assert result["response_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_database_health_check_unhealthy(self):
        """Test database health check returns unhealthy when DB is down."""
        from alma.api.routes.monitoring import check_database_health

        # Mock database error
        with patch("alma.api.routes.monitoring.get_session") as mock_session:
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(side_effect=Exception("Connection refused"))
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await check_database_health()
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Connection refused" in result["error"]

    @pytest.mark.asyncio
    async def test_llm_health_check_healthy(self):
        """Test LLM health check returns healthy when LLM is available."""
        from alma.api.routes.monitoring import check_llm_health

        # Mock successful LLM check
        async def mock_get_orchestrator():
            mock_orchestrator = MagicMock()
            mock_llm = MagicMock()
            mock_llm.model_name = "test-model"
            mock_orchestrator.llm = mock_llm
            return mock_orchestrator

        with patch(
            "alma.api.routes.monitoring.get_orchestrator", side_effect=mock_get_orchestrator
        ):
            result = await check_llm_health()
            assert result["status"] == "healthy"
            assert result["model"] == "test-model"

    @pytest.mark.asyncio
    async def test_llm_health_check_unhealthy(self):
        """Test LLM health check returns unhealthy when LLM fails."""
        from alma.api.routes.monitoring import check_llm_health

        # Mock LLM error
        with patch("alma.api.routes.monitoring.get_orchestrator") as mock_orch:
            mock_orch.side_effect = Exception("Model not loaded")

            result = await check_llm_health()
            assert result["status"] == "unhealthy"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_detailed_health_endpoint_all_healthy(self, client):
        """Test detailed health endpoint when all components are healthy."""
        with (
            patch("alma.api.routes.monitoring.check_database_health") as mock_db,
            patch("alma.api.routes.monitoring.check_llm_health") as mock_llm,
        ):

            mock_db.return_value = {"status": "healthy", "response_time_ms": 5}
            mock_llm.return_value = {"status": "healthy", "model": "test-model"}

            response = await client.get("/api/v1/monitoring/health/detailed")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert data["components"]["database"]["status"] == "healthy"
            assert data["components"]["llm"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_detailed_health_endpoint_degraded(self, client):
        """Test detailed health endpoint when some components are unhealthy."""
        with (
            patch("alma.api.routes.monitoring.check_database_health") as mock_db,
            patch("alma.api.routes.monitoring.check_llm_health") as mock_llm,
        ):

            mock_db.return_value = {"status": "healthy", "response_time_ms": 5}
            mock_llm.return_value = {"status": "unhealthy", "error": "Model error"}

            response = await client.get("/api/v1/monitoring/health/detailed")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "degraded"
            assert data["components"]["database"]["status"] == "healthy"
            assert data["components"]["llm"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_detailed_health_endpoint_unhealthy(self, client):
        """Test detailed health endpoint when critical components are down."""
        with (
            patch("alma.api.routes.monitoring.check_database_health") as mock_db,
            patch("alma.api.routes.monitoring.check_llm_health") as mock_llm,
        ):

            mock_db.return_value = {"status": "unhealthy", "error": "DB down"}
            mock_llm.return_value = {"status": "unhealthy", "error": "Model error"}

            response = await client.get("/api/v1/monitoring/health/detailed")
            assert response.status_code == 503  # Service unavailable

            data = response.json()
            assert data["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_includes_version(self, client):
        """Test health check includes version information."""
        response = await client.get("/api/v1/monitoring/health/detailed")
        data = response.json()
        assert "version" in data
        assert data["version"] is not None

    @pytest.mark.asyncio
    async def test_health_check_includes_uptime(self, client):
        """Test health check includes uptime information."""
        response = await client.get("/api/v1/monitoring/health/detailed")
        data = response.json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0
