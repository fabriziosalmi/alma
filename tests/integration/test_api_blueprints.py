"""Integration tests for Blueprint API endpoints."""

import datetime
from unittest.mock import patch, AsyncMock

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from alma.api.main import app
from alma.models.blueprint import SystemBlueprintModel

# Keep the original client fixture
@pytest.fixture
async def client() -> AsyncClient:
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# A separate fixture for tests that need DB access
@pytest.fixture
async def db_client(test_db_session: AsyncSession) -> AsyncClient:
    """Create test client with database session override."""
    from alma.core.database import get_session

    async def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_blueprint_data() -> dict:
    """Sample blueprint data for testing."""
    return {
        "version": "1.0",
        "name": "test-blueprint",
        "description": "Test blueprint for integration tests",
        "resources": [
            {
                "type": "compute",
                "name": "web-server",
                "provider": "fake",
                "specs": {"cpu": 2, "memory": "4GB"},
                "dependencies": [],
                "metadata": {},
            }
        ],
        "metadata": {"environment": "test"},
    }


class TestBlueprintAPI:
    """Integration tests for Blueprint API endpoints."""

    # This test doesn't need the DB, so it uses the simpler client
    async def test_get_blueprint_not_found(self, client: AsyncClient) -> None:
        """Test getting non-existent blueprint returns 404."""
        response = await client.get("/api/v1/blueprints/999")
        assert response.status_code == 404

    async def test_create_blueprint(
        self, db_client: AsyncClient, sample_blueprint_data: dict
    ) -> None:
        """Test creating a new blueprint."""
        response = await db_client.post("/api/v1/blueprints/", json=sample_blueprint_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_blueprint_data["name"]

    async def test_list_blueprints(
        self, db_client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test listing all blueprints."""
        now = datetime.datetime.now(datetime.UTC)
        test_db_session.add(SystemBlueprintModel(
            name="bp-1", resources=[], created_at=now, updated_at=now
        ))
        test_db_session.add(SystemBlueprintModel(
            name="bp-2", resources=[], created_at=now, updated_at=now
        ))
        await test_db_session.commit()

        response = await db_client.get("/api/v1/blueprints/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_update_blueprint(
        self, db_client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test updating a blueprint."""
        now = datetime.datetime.now(datetime.UTC)
        blueprint = SystemBlueprintModel(
            name="original-name", resources=[], created_at=now, updated_at=now
        )
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        update_data = {"name": "updated-name"}
        response = await db_client.put(f"/api/v1/blueprints/{blueprint.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-name"

    async def test_delete_blueprint(
        self, db_client: AsyncClient, test_db_session: AsyncSession
    ) -> None:
        """Test deleting a blueprint."""
        now = datetime.datetime.now(datetime.UTC)
        blueprint = SystemBlueprintModel(name="to-delete", resources=[], created_at=now, updated_at=now)
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        response = await db_client.delete(f"/api/v1/blueprints/{blueprint.id}")
        assert response.status_code == 204

        get_response = await db_client.get(f"/api/v1/blueprints/{blueprint.id}")
        assert get_response.status_code == 404

    # --- REFACTORED DEPLOYMENT TESTS ---

    @patch("alma.api.routes.blueprints.FakeEngine")
    async def test_deploy_blueprint_dry_run(
        self, MockFakeEngine, db_client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test dry-run deploy returns a plan summary."""
        # Mock the engine to simulate no resources currently exist
        mock_engine_instance = MockFakeEngine.return_value
        mock_engine_instance.get_state = AsyncMock(return_value=[])
        
        now = datetime.datetime.now(datetime.UTC)
        blueprint = SystemBlueprintModel(name=sample_blueprint_data["name"], resources=sample_blueprint_data["resources"], created_at=now, updated_at=now)
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        deploy_data = {"dry_run": True}
        response = await db_client.post(f"/api/v1/blueprints/{blueprint.id}/deploy", json=deploy_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "validated"
        assert "deployment_id" in data
        assert data["deployment_id"] == "dry-run"
        assert "1 to create" in data["plan_summary"] # Check the plan is returned

    @patch("alma.api.routes.blueprints.FakeEngine")
    async def test_deploy_blueprint_actual(
        self, MockFakeEngine, db_client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test an actual deploy calls the engine's apply and destroy methods."""
        mock_engine_instance = MockFakeEngine.return_value
        mock_engine_instance.get_state = AsyncMock(return_value=[])
        mock_engine_instance.apply = AsyncMock()
        mock_engine_instance.destroy = AsyncMock()

        now = datetime.datetime.now(datetime.UTC)
        blueprint = SystemBlueprintModel(name=sample_blueprint_data["name"], resources=sample_blueprint_data["resources"], created_at=now, updated_at=now)
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        deploy_data = {"dry_run": False}
        response = await db_client.post(f"/api/v1/blueprints/{blueprint.id}/deploy", json=deploy_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["resources_created"]) == 1 # Based on sample data
        
        mock_engine_instance.apply.assert_called_once()
        mock_engine_instance.destroy.assert_called_once()

    @patch("alma.api.routes.blueprints.FakeEngine")
    async def test_deploy_no_changes(
        self, MockFakeEngine, db_client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test deploying a blueprint that is already up-to-date."""
        # Mock engine to return a state that matches the blueprint
        from alma.core.state import ResourceState
        mock_engine_instance = MockFakeEngine.return_value
        mock_engine_instance.get_state = AsyncMock(return_value=[
            ResourceState(
                id="web-server", type="compute", config={"cpu": 2, "memory": "4GB"}
            )
        ])
        mock_engine_instance.apply = AsyncMock()

        now = datetime.datetime.now(datetime.UTC)
        blueprint = SystemBlueprintModel(name=sample_blueprint_data["name"], resources=sample_blueprint_data["resources"], created_at=now, updated_at=now)
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        deploy_data = {"dry_run": False}
        response = await db_client.post(f"/api/v1/blueprints/{blueprint.id}/deploy", json=deploy_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "No changes required" in data["message"]
        # Apply should NOT be called if the plan is empty
        mock_engine_instance.apply.assert_not_called()