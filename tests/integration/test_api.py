"""
Integration test for API endpoints
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from alma.api.main import app


@pytest.fixture
async def client(test_db_session: AsyncSession) -> AsyncClient:
    """Create test client with database session override."""
    from alma.core.database import get_session

    async def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ALMA"
    assert data["status"] == "operational"


async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


async def test_create_blueprint(client: AsyncClient):
    """Test creating a blueprint"""
    blueprint_data = {
        "name": "test-blueprint",
        "description": "A test blueprint",
        "resources": []
    }
    
    response = await client.post("/api/v1/blueprints/", json=blueprint_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "test-blueprint"


async def test_list_blueprints(client: AsyncClient):
    """Test listing blueprints"""
    response = await client.get("/api/v1/blueprints/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)