"""Unit tests for ALMA API Routes."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from alma.api.main import app
from alma.core.database import get_session
from alma.middleware.auth import verify_api_key
from alma.models.blueprint import SystemBlueprintModel

@pytest.fixture
def mock_session():
    """Mock AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    
    # Create synchronous mocks for Result and Scalars
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    
    # Configure chain
    session.execute.return_value = mock_result
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none = MagicMock(return_value=None) # Default
    
    mock_scalars.all.return_value = []
    
    return session

@pytest.fixture
def client(mock_session):
    """TestClient with overrides."""
    
    # Override dependencies
    app.dependency_overrides[get_session] = lambda: mock_session
    app.dependency_overrides[verify_api_key] = lambda: "valid-key"
    
    # Patch lifecycle events to avoid real DB/LLM init
    with patch("alma.api.main.init_db", new_callable=AsyncMock), \
         patch("alma.api.main.initialize_llm", new_callable=AsyncMock), \
         patch("alma.api.main.warmup_llm", new_callable=AsyncMock), \
         patch("alma.api.main.shutdown_llm", new_callable=AsyncMock), \
         patch("alma.api.main.close_db", new_callable=AsyncMock):
         
        with TestClient(app) as c:
            yield c
            
    # Clean up overrides
    app.dependency_overrides = {}

def test_root(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"

def test_health(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_blueprints_empty(client, mock_session):
    """Test listing blueprints (empty)."""
    # Access the MagicMocks we set up
    mock_result = mock_session.execute.return_value
    mock_scalars = mock_result.scalars.return_value
    mock_scalars.all.return_value = []
    
    response = client.get("/api/v1/blueprints/")
    assert response.status_code == 200
    assert response.json() == []

def test_create_blueprint(client, mock_session):
    """Test creating a blueprint."""
    payload = {
        "version": "1.0",
        "name": "test-bp",
        "description": "desc",
        "resources": [{"name": "vm1", "type": "compute", "provider": "proxmox", "specs": {}}],
        "metadata": {}
    }
    
    # Simulate refresh updating ID and timestamps
    async def side_effect_refresh(obj):
        obj.id = 1
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        obj.created_at = now
        obj.updated_at = now
        return None
    mock_session.refresh = AsyncMock(side_effect=side_effect_refresh)

    response = client.post("/api/v1/blueprints/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-bp"
    assert data["resources"][0]["name"] == "vm1"
    
    # Verify session calls
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

def test_get_blueprint_found(client, mock_session):
    """Test getting a blueprint."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    bp = SystemBlueprintModel(
        id=1, version="1.0", name="found-bp", 
        resources=[], blueprint_metadata={},
        created_at=now, updated_at=now
    )
    
    mock_result = mock_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = bp
    
    response = client.get("/api/v1/blueprints/1")
    assert response.status_code == 200
    assert response.json()["name"] == "found-bp"

def test_get_blueprint_not_found(client, mock_session):
    """Test getting non-existent blueprint."""
    mock_result = mock_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None
    
    response = client.get("/api/v1/blueprints/999")
    assert response.status_code == 404

def test_deploy_blueprint(client, mock_session):
    """Test deploying a blueprint."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    # 1. Setup existing blueprint
    bp = SystemBlueprintModel(
        id=1, version="1.0", name="deploy-bp", 
        resources=[{"name": "vm1", "type": "compute", "specs": {}, "provider": "mock"}], 
        blueprint_metadata={}, created_at=now, updated_at=now
    )
    mock_session.get.return_value = bp
    
    # 2. Mock Engine (SimulationEngine is instantiated inside the route)
    # We need to patch where it's imported in the route
    with patch("alma.api.routes.blueprints.SimulationEngine") as MockEngine:
        engine_instance = MockEngine.return_value
        engine_instance.get_state = AsyncMock(return_value=[]) # Empty state
        engine_instance.apply = AsyncMock()
        engine_instance.destroy = AsyncMock()
        
        response = client.post("/api/v1/blueprints/1/deploy", json={"dry_run": False})
        
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        engine_instance.apply.assert_called()

def test_deploy_blueprint_not_found(client, mock_session):
    """Test deploying non-existent blueprint."""
    mock_session.get.return_value = None
    
    response = client.post("/api/v1/blueprints/999/deploy", json={"dry_run": False})
    
    assert response.status_code == 404
