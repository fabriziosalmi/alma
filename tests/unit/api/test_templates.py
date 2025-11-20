"""Tests for templates API routes."""

import pytest
from httpx import AsyncClient, ASGITransport
from alma.api.main import app
from alma.core.templates import BlueprintTemplates, TemplateCategory


@pytest.fixture
async def client() -> AsyncClient:
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestTemplatesAPI:
    """Tests for template endpoints."""

    async def test_list_templates(self, client: AsyncClient) -> None:
        """Test listing available templates."""
        response = await client.get("/api/v1/templates/")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)
        assert data["count"] > 0

    async def test_list_templates_by_category(self, client: AsyncClient) -> None:
        """Test filtering templates by category."""
        response = await client.get("/api/v1/templates/?category=web")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data

    async def test_get_template(self, client: AsyncClient) -> None:
        """Test getting a specific template."""
        response = await client.get("/api/v1/templates/simple-web-app")
        assert response.status_code == 200
        data = response.json()
        assert "template_id" in data
        assert "blueprint" in data
        blueprint = data["blueprint"]
        assert "version" in blueprint
        assert "name" in blueprint
        assert "resources" in blueprint

    async def test_get_nonexistent_template(self, client: AsyncClient) -> None:
        """Test getting a template that doesn't exist."""
        response = await client.get("/api/v1/templates/nonexistent-template")
        assert response.status_code == 404

    async def test_customize_template(self, client: AsyncClient) -> None:
        """Test customizing a template."""
        params = {"instance_count": 3, "cpu": 4, "memory": "8GB"}
        response = await client.post(
            "/api/v1/templates/simple-web-app/customize", json={"parameters": params}
        )
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
