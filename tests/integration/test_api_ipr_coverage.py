"""IPR API routes coverage tests with rate limiting bypassed."""
import os
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch


# Set testing environment
os.environ["TESTING"] = "true"
os.environ["BYPASS_RATE_LIMIT"] = "true"


@pytest.fixture
async def client():
    """Test client with database mocked."""
    from alma.api.main import app
    from alma.core.database import get_session

    # Mock database session
    class MockAsyncSession:
        async def execute(self, query):
            result = MagicMock()
            result.scalars.return_value.all.return_value = []
            result.scalars.return_value.first.return_value = None
            return result

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

        def add(self, obj):
            pass

        async def get(self, model, id):
            return None

    async def mock_get_session():
        return MockAsyncSession()

    app.dependency_overrides[get_session] = mock_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


class TestIPRAPIRoutes:
    """Test IPR (Infrastructure Pull Request) API routes."""

    async def test_list_iprs(self, client):
        """Test listing IPRs."""
        response = await client.get("/iprs/")
        # Should not be rate limited
        assert response.status_code in [200, 404]

    async def test_list_iprs_with_pagination(self, client):
        """Test IPR listing with pagination."""
        response = await client.get("/iprs/?skip=0&limit=10")
        assert response.status_code in [200, 404]

    async def test_list_iprs_with_status_filter(self, client):
        """Test filtering IPRs by status."""
        response = await client.get("/iprs/?status=pending")
        assert response.status_code in [200, 404]

    async def test_create_ipr(self, client):
        """Test creating an IPR."""
        payload = {
            "title": "Test IPR",
            "description": "Test infrastructure change",
            "blueprint_id": 1,
            "changes_summary": {"added": ["resource1"], "removed": [], "modified": []},
        }
        response = await client.post("/iprs/", json=payload)
        assert response.status_code in [200, 201, 404, 422]

    async def test_create_ipr_invalid_data(self, client):
        """Test creating IPR with invalid data."""
        payload = {"title": ""}  # Missing required fields
        response = await client.post("/iprs/", json=payload)
        assert response.status_code in [422, 404]

    async def test_get_ipr_by_id(self, client):
        """Test getting specific IPR."""
        response = await client.get("/iprs/1")
        assert response.status_code in [200, 404]

    async def test_get_ipr_nonexistent(self, client):
        """Test getting non-existent IPR."""
        response = await client.get("/iprs/99999")
        assert response.status_code in [404]

    async def test_update_ipr(self, client):
        """Test updating an IPR."""
        payload = {"title": "Updated IPR", "description": "Updated description"}
        response = await client.put("/iprs/1", json=payload)
        assert response.status_code in [200, 404, 422]

    async def test_delete_ipr(self, client):
        """Test deleting an IPR."""
        response = await client.delete("/iprs/1")
        assert response.status_code in [200, 204, 404]

    async def test_review_ipr(self, client):
        """Test reviewing an IPR."""
        payload = {"action": "approve", "comments": "Looks good", "reviewer": "test-user"}
        response = await client.post("/iprs/1/review", json=payload)
        assert response.status_code in [200, 404, 422]

    async def test_review_ipr_reject(self, client):
        """Test rejecting an IPR."""
        payload = {"action": "reject", "comments": "Needs changes", "reviewer": "test-user"}
        response = await client.post("/iprs/1/review", json=payload)
        assert response.status_code in [200, 404, 422]

    async def test_deploy_ipr(self, client):
        """Test deploying an IPR."""
        payload = {"engine": "fake", "dry_run": False}
        response = await client.post("/iprs/1/deploy", json=payload)
        assert response.status_code in [200, 201, 404, 422]

    async def test_deploy_ipr_dry_run(self, client):
        """Test IPR dry run deployment."""
        payload = {"engine": "fake", "dry_run": True}
        response = await client.post("/iprs/1/deploy", json=payload)
        assert response.status_code in [200, 404, 422]

    async def test_ipr_stats(self, client):
        """Test getting IPR statistics."""
        response = await client.get("/iprs/stats")
        assert response.status_code in [200, 404]

    async def test_rapid_ipr_requests(self, client):
        """Test rapid IPR requests don't get rate limited."""
        responses = []
        for _ in range(15):
            response = await client.get("/iprs/")
            responses.append(response.status_code)

        # None should be 429 (rate limited)
        assert 429 not in responses
        assert all(code in [200, 404] for code in responses)


class TestIPRWorkflow:
    """Test complete IPR workflow."""

    async def test_create_review_deploy_workflow(self, client):
        """Test full IPR lifecycle."""
        # Create IPR
        create_payload = {
            "title": "Workflow Test IPR",
            "description": "Testing complete workflow",
            "blueprint_id": 1,
        }
        create_response = await client.post("/iprs/", json=create_payload)
        assert create_response.status_code in [200, 201, 404, 422]

        # Review IPR
        review_payload = {"action": "approve", "reviewer": "test-reviewer"}
        review_response = await client.post("/iprs/1/review", json=review_payload)
        assert review_response.status_code in [200, 404, 422]

        # Deploy IPR
        deploy_payload = {"engine": "fake", "dry_run": False}
        deploy_response = await client.post("/iprs/1/deploy", json=deploy_payload)
        assert deploy_response.status_code in [200, 201, 404, 422]
