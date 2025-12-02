"""Unit tests for DockerEngine."""

from unittest.mock import MagicMock, patch
import pytest
from alma.core.state import Plan, ResourceState
from alma.engines.docker import DockerEngine
from alma.schemas.blueprint import ResourceDefinition, SystemBlueprint

@pytest.fixture
def engine():
    return DockerEngine()

@pytest.fixture
def sample_blueprint():
    return SystemBlueprint(
        id=1,
        created_at="2025-11-20T12:00:00",
        updated_at="2025-11-20T12:00:00",
        version="1.0",
        name="test-docker-blueprint",
        resources=[
            ResourceDefinition(
                type="container",
                name="test-container",
                provider="docker",
                specs={
                    "image": "nginx:latest",
                    "ports": {"80/tcp": 8080}
                },
            )
        ],
    )

class TestDockerEngine:
    
    @patch("alma.engines.docker.docker")
    async def test_health_check_success(self, mock_docker, engine):
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        
        assert await engine.health_check()
        mock_client.ping.assert_called_once()

    @patch("alma.engines.docker.docker")
    async def test_apply_create(self, mock_docker, engine, sample_blueprint):
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        
        plan = Plan(to_create=sample_blueprint.resources)
        await engine.apply(plan)
        
        mock_client.containers.run.assert_called_with(
            "nginx:latest",
            name="test-container",
            ports={"80/tcp": 8080},
            environment={},
            detach=True
        )

    @patch("alma.engines.docker.docker")
    async def test_get_state(self, mock_docker, engine, sample_blueprint):
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = MagicMock()
        mock_container.name = "test-container"
        mock_container.status = "running"
        mock_container.attrs = {
            "Config": {"Image": "nginx:latest"},
            "NetworkSettings": {"Ports": {"80/tcp": [{"HostPort": "8080"}]}}
        }
        mock_client.containers.list.return_value = [mock_container]
        
        state = await engine.get_state(sample_blueprint)
        assert len(state) == 1
        assert state[0].id == "test-container"
        assert state[0].config["image"] == "nginx:latest"

    @patch("alma.engines.docker.docker")
    async def test_destroy(self, mock_docker, engine):
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        
        resource_state = ResourceState(id="test-container", type="container", config={})
        plan = Plan(to_delete=[resource_state])
        
        await engine.destroy(plan)
        
        mock_client.containers.get.assert_called_with("test-container")
        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()
