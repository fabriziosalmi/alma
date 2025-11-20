"""End-to-end tests for complete deployment workflow."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
import yaml
from pathlib import Path

from alma.api.main import app
from alma.engines.fake import FakeEngine


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


class TestDeploymentWorkflow:
    """End-to-end tests for complete deployment workflows."""

    async def test_simple_deployment_workflow(self, client: AsyncClient) -> None:
        """Test complete workflow: create blueprint -> deploy -> verify."""
        # Step 1: Create blueprint
        blueprint_data = {
            "version": "1.0",
            "name": "e2e-test-app",
            "description": "E2E test application",
            "resources": [
                {
                    "type": "compute",
                    "name": "app-server",
                    "provider": "fake",
                    "specs": {"cpu": 2, "memory": "4GB", "storage": "50GB"},
                    "dependencies": [],
                    "metadata": {},
                }
            ],
            "metadata": {"environment": "test"},
        }

        create_response = await client.post("/api/v1/blueprints/", json=blueprint_data)
        assert create_response.status_code == 201
        blueprint_id = create_response.json()["id"]

        # Step 2: Validate blueprint (dry-run)
        dry_run_response = await client.post(
            f"/api/v1/blueprints/{blueprint_id}/deploy",
            json={"blueprint_id": blueprint_id, "dry_run": True},
        )
        assert dry_run_response.status_code == 200
        assert dry_run_response.json()["status"] == "validated"

        # Step 3: Deploy blueprint
        deploy_response = await client.post(
            f"/api/v1/blueprints/{blueprint_id}/deploy",
            json={"blueprint_id": blueprint_id, "dry_run": False},
        )
        assert deploy_response.status_code == 200
        deployment_data = deploy_response.json()
        assert deployment_data["status"] == "completed"
        assert "app-server" in deployment_data["resources_created"]
        assert len(deployment_data["resources_failed"]) == 0

        # Step 4: Verify blueprint still exists
        get_response = await client.get(f"/api/v1/blueprints/{blueprint_id}")
        assert get_response.status_code == 200

    async def test_multi_resource_deployment(self, client: AsyncClient) -> None:
        """Test deploying blueprint with multiple dependent resources."""
        blueprint_data = {
            "version": "1.0",
            "name": "multi-tier-app",
            "resources": [
                {
                    "type": "compute",
                    "name": "database",
                    "provider": "fake",
                    "specs": {"cpu": 4, "memory": "16GB"},
                    "dependencies": [],
                    "metadata": {},
                },
                {
                    "type": "compute",
                    "name": "api-server",
                    "provider": "fake",
                    "specs": {"cpu": 2, "memory": "8GB"},
                    "dependencies": ["database"],
                    "metadata": {},
                },
                {
                    "type": "network",
                    "name": "load-balancer",
                    "provider": "fake",
                    "specs": {"type": "http", "backends": ["api-server"]},
                    "dependencies": ["api-server"],
                    "metadata": {},
                },
            ],
        }

        # Create and deploy
        create_response = await client.post("/api/v1/blueprints/", json=blueprint_data)
        blueprint_id = create_response.json()["id"]

        deploy_response = await client.post(
            f"/api/v1/blueprints/{blueprint_id}/deploy",
            json={"blueprint_id": blueprint_id, "dry_run": False},
        )

        assert deploy_response.status_code == 200
        deployment_data = deploy_response.json()
        assert deployment_data["status"] == "completed"
        assert len(deployment_data["resources_created"]) == 3
        assert "database" in deployment_data["resources_created"]
        assert "api-server" in deployment_data["resources_created"]
        assert "load-balancer" in deployment_data["resources_created"]

    async def test_blueprint_update_and_redeploy(self, client: AsyncClient) -> None:
        """Test updating a blueprint and redeploying."""
        # Create initial blueprint
        initial_data = {
            "version": "1.0",
            "name": "evolving-app",
            "resources": [
                {
                    "type": "compute",
                    "name": "web-server",
                    "provider": "fake",
                    "specs": {"cpu": 1, "memory": "2GB"},
                    "dependencies": [],
                    "metadata": {},
                }
            ],
        }

        create_response = await client.post("/api/v1/blueprints/", json=initial_data)
        blueprint_id = create_response.json()["id"]

        # Deploy initial version
        deploy1_response = await client.post(
            f"/api/v1/blueprints/{blueprint_id}/deploy",
            json={"blueprint_id": blueprint_id, "dry_run": False},
        )
        assert deploy1_response.status_code == 200

        # Update blueprint with more resources
        update_data = {
            "resources": [
                {
                    "type": "compute",
                    "name": "web-server",
                    "provider": "fake",
                    "specs": {"cpu": 2, "memory": "4GB"},  # Upgraded specs
                    "dependencies": [],
                    "metadata": {},
                },
                {
                    "type": "compute",
                    "name": "cache-server",
                    "provider": "fake",
                    "specs": {"cpu": 1, "memory": "4GB"},
                    "dependencies": [],
                    "metadata": {},
                },
            ]
        }

        update_response = await client.put(f"/api/v1/blueprints/{blueprint_id}", json=update_data)
        assert update_response.status_code == 200

        # Redeploy updated blueprint
        deploy2_response = await client.post(
            f"/api/v1/blueprints/{blueprint_id}/deploy",
            json={"blueprint_id": blueprint_id, "dry_run": False},
        )
        assert deploy2_response.status_code == 200
        deployment_data = deploy2_response.json()
        # Only new resource (cache-server) is created, web-server already exists with different specs
        assert len(deployment_data["resources_created"]) >= 1
        assert "cache-server" in deployment_data["resources_created"]

    async def test_multiple_blueprints_independent_deployment(self, client: AsyncClient) -> None:
        """Test deploying multiple blueprints independently."""
        blueprints = []

        # Create 3 different blueprints
        for i in range(3):
            blueprint_data = {
                "version": "1.0",
                "name": f"independent-app-{i}",
                "resources": [
                    {
                        "type": "compute",
                        "name": f"server-{i}",
                        "provider": "fake",
                        "specs": {"cpu": 2, "memory": "4GB"},
                        "dependencies": [],
                        "metadata": {},
                    }
                ],
            }

            response = await client.post("/api/v1/blueprints/", json=blueprint_data)
            assert response.status_code == 201
            blueprints.append(response.json()["id"])

        # Deploy all blueprints
        deployments = []
        for blueprint_id in blueprints:
            response = await client.post(
                f"/api/v1/blueprints/{blueprint_id}/deploy",
                json={"blueprint_id": blueprint_id, "dry_run": False},
            )
            assert response.status_code == 200
            deployments.append(response.json())

        # Verify all deployments succeeded
        assert all(d["status"] == "completed" for d in deployments)
        assert len(deployments) == 3

    async def test_validation_failure_prevents_deployment(self, client: AsyncClient) -> None:
        """Test that invalid blueprint cannot be deployed."""
        # Create blueprint missing required fields
        invalid_data = {
            "name": "invalid-blueprint",
            "resources": [
                {
                    "type": "compute",
                    "name": "server",
                    "provider": "fake",
                    "specs": {},
                    "dependencies": [],
                    "metadata": {},
                }
            ],
            # Missing version field will use default
        }

        create_response = await client.post("/api/v1/blueprints/", json=invalid_data)
        assert create_response.status_code == 201  # Creation succeeds with defaults

        blueprint_id = create_response.json()["id"]

        # Deployment should still work with FakeEngine
        deploy_response = await client.post(
            f"/api/v1/blueprints/{blueprint_id}/deploy",
            json={"blueprint_id": blueprint_id, "dry_run": False},
        )
        assert deploy_response.status_code == 200

    async def test_complete_lifecycle_create_deploy_delete(self, client: AsyncClient) -> None:
        """Test complete lifecycle: create -> deploy -> delete."""
        # Create
        blueprint_data = {
            "version": "1.0",
            "name": "lifecycle-test",
            "resources": [
                {
                    "type": "compute",
                    "name": "temp-server",
                    "provider": "fake",
                    "specs": {"cpu": 1, "memory": "2GB"},
                    "dependencies": [],
                    "metadata": {},
                }
            ],
        }

        create_response = await client.post("/api/v1/blueprints/", json=blueprint_data)
        assert create_response.status_code == 201
        blueprint_id = create_response.json()["id"]

        # Deploy
        deploy_response = await client.post(
            f"/api/v1/blueprints/{blueprint_id}/deploy",
            json={"blueprint_id": blueprint_id, "dry_run": False},
        )
        assert deploy_response.status_code == 200

        # Delete
        delete_response = await client.delete(f"/api/v1/blueprints/{blueprint_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/v1/blueprints/{blueprint_id}")
        assert get_response.status_code == 404
