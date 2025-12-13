"""Unit tests for Docker Engine."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from alma.engines.docker import DockerEngine
from alma.schemas.blueprint import SystemBlueprint, ResourceDefinition
from datetime import datetime

@pytest.fixture
def mock_docker_lib():
    """Mock the docker library."""
    with patch("alma.engines.docker.docker", create=True) as mock_dock:
        mock_client = MagicMock()
        mock_dock.DockerClient.return_value = mock_client
        mock_dock.from_env.return_value = mock_client
        yield mock_dock, mock_client

@pytest.fixture
def engine(mock_docker_lib):
    """Create DockerEngine with mocked client."""
    return DockerEngine(config={"base_url": "unix:///var/run/docker.sock"})

class TestDockerEngine:
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, engine, mock_docker_lib):
        _, mock_client = mock_docker_lib
        
        assert await engine.health_check() is True
        mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, engine, mock_docker_lib):
        _, mock_client = mock_docker_lib
        mock_client.ping.side_effect = Exception("Docker Down")
        
        assert await engine.health_check() is False

    @pytest.mark.asyncio
    async def test_apply_create_container(self, engine, mock_docker_lib):
        _, mock_client = mock_docker_lib
        
        resource = ResourceDefinition(
            name="test-redis",
            type="container", 
            provider="docker",
            specs={"image": "redis:alpine", "ports": {"6379/tcp": 6379}}
        )
        plan = MagicMock()
        plan.to_create = [resource]
        plan.to_update = []
        
        await engine.apply(plan)
        
        mock_client.containers.run.assert_called_once()
        args, kwargs = mock_client.containers.run.call_args
        assert args[0] == "redis:alpine"
        assert kwargs["name"] == "test-redis"
        assert kwargs["detach"] is True

    @pytest.mark.asyncio
    async def test_apply_update_container(self, engine, mock_docker_lib):
        _, mock_client = mock_docker_lib
        
        # Mock existing container found
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        
        resource = ResourceDefinition(
            name="test-redis",
            type="container", 
            provider="docker",
            specs={"image": "redis:latest"}
        )
        plan = MagicMock()
        plan.to_create = []
        plan.to_update = [(MagicMock(), resource)]
        
        await engine.apply(plan)
        
        # Should stop and remove old container
        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()
        
        # Should run new one
        mock_client.containers.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_destroy_container(self, engine, mock_docker_lib):
        _, mock_client = mock_docker_lib
        
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        
        res_state = MagicMock()
        res_state.id = "test-redis"
        
        plan = MagicMock()
        plan.to_delete = [res_state]
        
        await engine.destroy(plan)
        
        mock_client.containers.get.assert_called_with("test-redis")
        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()
