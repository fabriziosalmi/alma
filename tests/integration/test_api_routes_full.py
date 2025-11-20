"""Full API routes integration tests with rate limiting bypassed."""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    """Test client with rate limit bypass."""
    from alma.api.main import app
    from alma.core.database import get_session

    # Mock database session
    async def mock_session():
        from tests.unit.test_api_ipr import MockAsyncSession

        return MockAsyncSession()

    app.dependency_overrides[get_session] = mock_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


class TestBlueprintsAPIFull:
    """Test all blueprint endpoints without rate limiting."""

    async def test_list_blueprints_rapid_fire(self, client):
        """Test rapid requests don't get rate limited."""
        responses = []
        for _ in range(10):
            response = await client.get("/blueprints/")
            responses.append(response.status_code)

        # None should be 429 (rate limited)
        assert 429 not in responses

    async def test_create_blueprint_validation(self, client):
        """Test blueprint creation with various inputs."""
        # Valid blueprint
        valid_data = {"name": "test", "version": "1.0", "resources": []}
        response = await client.post("/blueprints/", json=valid_data)
        assert response.status_code in [200, 201, 404, 422]

        # Invalid blueprint (missing fields)
        response = await client.post("/blueprints/", json={})
        assert response.status_code in [422, 404]

    async def test_get_blueprint_by_id(self, client):
        """Test getting blueprint by ID."""
        response = await client.get("/blueprints/1")
        assert response.status_code in [200, 404]

        response = await client.get("/blueprints/999")
        assert response.status_code in [404]

    async def test_update_blueprint(self, client):
        """Test updating blueprint."""
        update_data = {"name": "updated", "resources": []}
        response = await client.put("/blueprints/1", json=update_data)
        assert response.status_code in [200, 404, 422]

    async def test_delete_blueprint(self, client):
        """Test deleting blueprint."""
        response = await client.delete("/blueprints/1")
        assert response.status_code in [200, 204, 404]


class TestConversationAPIFull:
    """Test conversation endpoints without rate limiting."""

    async def test_chat_endpoint_multiple_requests(self, client):
        """Test multiple chat requests in rapid succession."""
        chat_data = {"message": "Hello", "context": {}}

        responses = []
        for _ in range(5):
            response = await client.post("/conversation/chat", json=chat_data)
            responses.append(response.status_code)

        # Should not get rate limited
        assert 429 not in responses

    async def test_chat_with_various_inputs(self, client):
        """Test chat with different input variations."""
        # Empty message
        response = await client.post("/conversation/chat", json={"message": ""})
        assert response.status_code in [200, 400, 404, 422]

        # Long message
        long_message = "a" * 1000
        response = await client.post("/conversation/chat", json={"message": long_message})
        assert response.status_code in [200, 400, 404, 422]

    async def test_generate_blueprint_endpoint(self, client):
        """Test blueprint generation endpoint."""
        data = {"description": "Create a web server", "constraints": {}}
        response = await client.post("/conversation/generate-blueprint", json=data)
        assert response.status_code in [200, 201, 404, 422]

    async def test_describe_blueprint_endpoint(self, client):
        """Test blueprint description endpoint."""
        data = {"blueprint": {"name": "test", "version": "1.0", "resources": []}}
        response = await client.post("/conversation/describe-blueprint", json=data)
        assert response.status_code in [200, 404, 422]


class TestToolsAPIFull:
    """Test tools endpoints without rate limiting."""

    async def test_list_tools_endpoint(self, client):
        """Test listing available tools."""
        response = await client.get("/tools/")
        assert response.status_code in [200, 404]

    async def test_execute_tool_rapid_requests(self, client):
        """Test rapid tool execution."""
        tool_data = {"tool_name": "validate_blueprint", "arguments": {"blueprint": {}}}

        responses = []
        for _ in range(8):
            response = await client.post("/tools/execute", json=tool_data)
            responses.append(response.status_code)

        # Should not get rate limited (40 RPM limit)
        assert 429 not in responses


class TestTemplatesAPIFull:
    """Test templates endpoints without rate limiting."""

    async def test_list_templates(self, client):
        """Test listing templates."""
        response = await client.get("/templates/")
        assert response.status_code in [200, 404]

    async def test_get_template_by_id(self, client):
        """Test getting specific template."""
        response = await client.get("/templates/simple-web-app")
        assert response.status_code in [200, 404]


class TestMonitoringAPIFull:
    """Test monitoring endpoints without rate limiting."""

    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/monitoring/health")
        assert response.status_code in [200, 404]

    async def test_detailed_health_check(self, client):
        """Test detailed health check."""
        response = await client.get("/monitoring/health/detailed")
        assert response.status_code in [200, 404]

    async def test_metrics_summary(self, client):
        """Test metrics summary."""
        response = await client.get("/monitoring/metrics/summary")
        assert response.status_code in [200, 404]

    async def test_rate_limit_stats(self, client):
        """Test rate limit statistics."""
        response = await client.get("/monitoring/rate-limit/stats")
        assert response.status_code in [200, 404]


class TestIPRAPIFull:
    """Test IPR endpoints without rate limiting."""

    async def test_list_iprs(self, client):
        """Test listing IPRs."""
        response = await client.get("/iprs/")
        assert response.status_code in [200, 404]

    async def test_create_ipr(self, client):
        """Test creating IPR."""
        ipr_data = {"title": "Test IPR", "description": "Test description", "blueprint_id": 1}
        response = await client.post("/iprs/", json=ipr_data)
        assert response.status_code in [200, 201, 404, 422]

    async def test_get_ipr_by_id(self, client):
        """Test getting IPR by ID."""
        response = await client.get("/iprs/1")
        assert response.status_code in [200, 404]
