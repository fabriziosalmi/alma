"""Integration tests for Blueprint API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from ai_cdn.api.main import app
from ai_cdn.models.blueprint import SystemBlueprintModel


@pytest.fixture
async def client(test_db_session: AsyncSession) -> AsyncClient:
    """Create test client with database session override."""
    from ai_cdn.core.database import get_session

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

    async def test_create_blueprint(
        self, client: AsyncClient, sample_blueprint_data: dict
    ) -> None:
        """Test creating a new blueprint."""
        response = await client.post(
            "/api/v1/blueprints/",
            json=sample_blueprint_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_blueprint_data["name"]
        assert data["version"] == sample_blueprint_data["version"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_list_blueprints(
        self, client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test listing all blueprints."""
        # Create test blueprints
        for i in range(3):
            blueprint = SystemBlueprintModel(
                version="1.0",
                name=f"test-blueprint-{i}",
                description="Test blueprint",
                resources=sample_blueprint_data["resources"],
                metadata={},
            )
            test_db_session.add(blueprint)
        await test_db_session.commit()

        # List blueprints
        response = await client.get("/api/v1/blueprints/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("id" in bp for bp in data)

    async def test_list_blueprints_with_pagination(
        self, client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test listing blueprints with pagination."""
        # Create 5 blueprints
        for i in range(5):
            blueprint = SystemBlueprintModel(
                version="1.0",
                name=f"test-blueprint-{i}",
                resources=sample_blueprint_data["resources"],
            )
            test_db_session.add(blueprint)
        await test_db_session.commit()

        # Get first page
        response = await client.get("/api/v1/blueprints/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Get second page
        response = await client.get("/api/v1/blueprints/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_get_blueprint(
        self, client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test getting a specific blueprint."""
        # Create blueprint
        blueprint = SystemBlueprintModel(
            version="1.0",
            name="test-blueprint",
            resources=sample_blueprint_data["resources"],
        )
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        # Get blueprint
        response = await client.get(f"/api/v1/blueprints/{blueprint.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == blueprint.id
        assert data["name"] == "test-blueprint"

    async def test_get_blueprint_not_found(self, client: AsyncClient) -> None:
        """Test getting non-existent blueprint."""
        response = await client.get("/api/v1/blueprints/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_update_blueprint(
        self, client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test updating a blueprint."""
        # Create blueprint
        blueprint = SystemBlueprintModel(
            version="1.0",
            name="original-name",
            resources=sample_blueprint_data["resources"],
        )
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        # Update blueprint
        update_data = {
            "name": "updated-name",
            "description": "Updated description",
        }
        response = await client.put(
            f"/api/v1/blueprints/{blueprint.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-name"
        assert data["description"] == "Updated description"

    async def test_update_blueprint_not_found(self, client: AsyncClient) -> None:
        """Test updating non-existent blueprint."""
        update_data = {"name": "new-name"}
        response = await client.put("/api/v1/blueprints/999", json=update_data)

        assert response.status_code == 404

    async def test_delete_blueprint(
        self, client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test deleting a blueprint."""
        # Create blueprint
        blueprint = SystemBlueprintModel(
            version="1.0",
            name="to-delete",
            resources=sample_blueprint_data["resources"],
        )
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        # Delete blueprint
        response = await client.delete(f"/api/v1/blueprints/{blueprint.id}")

        assert response.status_code == 204

        # Verify deletion
        response = await client.get(f"/api/v1/blueprints/{blueprint.id}")
        assert response.status_code == 404

    async def test_delete_blueprint_not_found(self, client: AsyncClient) -> None:
        """Test deleting non-existent blueprint."""
        response = await client.delete("/api/v1/blueprints/999")

        assert response.status_code == 404

    async def test_deploy_blueprint_dry_run(
        self, client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test deploying blueprint in dry-run mode."""
        # Create blueprint
        blueprint = SystemBlueprintModel(
            version="1.0",
            name="test-deploy",
            resources=sample_blueprint_data["resources"],
        )
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        # Deploy in dry-run mode
        deploy_data = {"blueprint_id": blueprint.id, "dry_run": True}
        response = await client.post(
            f"/api/v1/blueprints/{blueprint.id}/deploy",
            json=deploy_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deployment_id"] == "dry-run"
        assert data["status"] == "validated"

    async def test_deploy_blueprint_actual(
        self, client: AsyncClient, test_db_session: AsyncSession, sample_blueprint_data: dict
    ) -> None:
        """Test actual blueprint deployment."""
        # Create blueprint
        blueprint = SystemBlueprintModel(
            version="1.0",
            name="test-deploy",
            resources=sample_blueprint_data["resources"],
        )
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        # Deploy
        deploy_data = {"blueprint_id": blueprint.id, "dry_run": False}
        response = await client.post(
            f"/api/v1/blueprints/{blueprint.id}/deploy",
            json=deploy_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["resources_created"]) > 0
        assert "deployment_id" in data

    async def test_deploy_blueprint_invalid(
        self, client: AsyncClient, test_db_session: AsyncSession
    ) -> None:
        """Test deploying invalid blueprint."""
        # Create invalid blueprint (missing resources field)
        blueprint = SystemBlueprintModel(
            version="1.0",
            name="invalid-blueprint",
            resources=[],  # Empty resources
        )
        test_db_session.add(blueprint)
        await test_db_session.commit()
        await test_db_session.refresh(blueprint)

        # Attempt to deploy
        deploy_data = {"blueprint_id": blueprint.id, "dry_run": False}
        response = await client.post(
            f"/api/v1/blueprints/{blueprint.id}/deploy",
            json=deploy_data,
        )

        # FakeEngine should still succeed with empty resources
        assert response.status_code == 200

    async def test_deploy_blueprint_not_found(self, client: AsyncClient) -> None:
        """Test deploying non-existent blueprint."""
        deploy_data = {"blueprint_id": 999, "dry_run": False}
        response = await client.post("/api/v1/blueprints/999/deploy", json=deploy_data)

        assert response.status_code == 404
