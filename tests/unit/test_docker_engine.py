
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from alma.engines.docker import DockerEngine
from alma.schemas.blueprint import ResourceDefinition, SystemBlueprint
from alma.core.state import Plan, ResourceState

# Mock docker package
import sys
sys.modules['docker'] = MagicMock()
import docker
docker.errors = MagicMock()
docker.errors.DockerException = Exception
docker.errors.NotFound = Exception
docker.errors.APIError = Exception

@pytest.fixture
def resource_def():
    return ResourceDefinition(
        name="test-container",
        type="container",
        provider="docker",
        specs={"image": "nginx", "ports": {"80/tcp": 8080}}
    )

@pytest.fixture
def plan(resource_def):
    return Plan(
        to_create=[resource_def],
        to_update=[],
        to_delete=[]
    )

@pytest.mark.asyncio
async def test_apply_create(plan):
    with patch("alma.engines.docker.docker") as mock_docker:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run = MagicMock()
        
        engine = DockerEngine()
        await engine.apply(plan)
        
        mock_client.containers.run.assert_called_once()
        args, kwargs = mock_client.containers.run.call_args
        assert args[0] == "nginx"
        assert kwargs["name"] == "test-container"
        assert kwargs["ports"] == {"80/tcp": 8080}

@pytest.mark.asyncio
async def test_apply_destroy():
    state = ResourceState(id="test-container", type="container", config={})
    plan = Plan(to_create=[], to_update=[], to_delete=[state])
    
    with patch("alma.engines.docker.docker") as mock_docker:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        
        engine = DockerEngine()
        await engine.destroy(plan)
        
        mock_client.containers.get.assert_called_with("test-container")
        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()
