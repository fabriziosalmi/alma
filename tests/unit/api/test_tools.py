"""Tests for tools API routes."""

import pytest
from httpx import AsyncClient, ASGITransport
from alma.api.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestToolsAPI:
    """Tests for tools endpoints."""

    async def test_list_tools(self, client: AsyncClient) -> None:
        """Test listing available tools."""
        response = await client.get("/api/v1/tools/")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)
        assert len(data["tools"]) > 0

        # Check tool structure
        tool = data["tools"][0]
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool

    async def test_execute_tool(self, client: AsyncClient) -> None:
        """Test executing a tool."""
        request_data = {
            "tool_name": "validate_blueprint",
            "arguments": {"blueprint": {"version": "1.0", "name": "test", "resources": []}},
        }
        response = await client.post("/api/v1/tools/execute-direct", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data

    async def test_execute_unknown_tool(self, client: AsyncClient) -> None:
        """Test executing an unknown tool."""
        request_data = {"tool_name": "nonexistent_tool", "arguments": {}}
        response = await client.post("/api/v1/tools/execute-direct", json=request_data)
        # Should handle gracefully - error in result
        assert response.status_code == 200
        data = response.json()
        assert "error" in data or not data.get("success", True)
