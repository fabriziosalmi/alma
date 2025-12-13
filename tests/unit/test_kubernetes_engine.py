"""Unit tests for Kubernetes Engine."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from alma.engines.kubernetes import KubernetesEngine
from alma.schemas.blueprint import SystemBlueprint, ResourceDefinition
from datetime import datetime
from kubernetes_asyncio.client.exceptions import ApiException

@pytest.fixture
def mock_k8s_client():
    """Mock the kubernetes_asyncio client."""
    with patch("alma.engines.kubernetes.client") as mock_client, \
         patch("alma.engines.kubernetes.config") as mock_config:
        
        # Mock Clients
        mock_api = MagicMock()
        mock_apps = MagicMock()
        mock_core = MagicMock()
        
        mock_client.ApiClient.return_value = mock_api
        mock_client.AppsV1Api.return_value = mock_apps
        mock_client.CoreV1Api.return_value = mock_core
        
        # Configure object constructors to return verifiable mocks
        mock_deployment = MagicMock()
        mock_deployment.kind = "Deployment"
        mock_deployment.metadata.name = "web-app"  # This needs to be dynamic?
        # Actually, verifying call args to constructor is better if we want to be strict.
        # But simply creating a generic mock that behaves nicely:
        def create_deployment(**kwargs):
            m = MagicMock()
            m.kind = kwargs.get("kind")
            m.metadata.name = kwargs.get("metadata").name if kwargs.get("metadata") else None
            return m
        mock_client.V1Deployment.side_effect = create_deployment

        mock_config.load_kube_config = AsyncMock()
        mock_config.load_incluster_config = AsyncMock()
        
        yield mock_client, mock_apps, mock_core

@pytest.fixture
def engine(mock_k8s_client):
    return KubernetesEngine(config_dict={"namespace": "test-ns"})

@pytest.fixture
def blueprint():
    return SystemBlueprint(
        id=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        name="test-k8s-bp",
        resources=[]
    )

class TestKubernetesEngine:

    @pytest.mark.asyncio
    async def test_health_check_success(self, engine, mock_k8s_client):
        _, _, mock_core = mock_k8s_client
        mock_core.get_api_resources = AsyncMock()
        
        assert await engine.health_check() is True
        mock_core.get_api_resources.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, engine, mock_k8s_client):
        _, _, mock_core = mock_k8s_client
        mock_core.get_api_resources = AsyncMock(side_effect=Exception("API Error"))
        
        assert await engine.health_check() is False

    @pytest.mark.asyncio
    async def test_apply_deployment_create(self, engine, mock_k8s_client):
        """Test creating a new deployment."""
        mock_client, mock_apps, mock_core = mock_k8s_client
        
        # Mock read_namespace (exists)
        mock_core.read_namespace = AsyncMock()
        
        # Mock create deployment
        mock_apps.create_namespaced_deployment = AsyncMock()
        
        # Mock wait for rollout
        # read_namespaced_deployment needs to raise 404 first (for apply logic check)
        # then return a status (for wait logic)
        # BUT _apply_deployment first calls read (to decide patch vs create)
        # then create
        # then wait (calls read again)
        
        # We need side_effect to return different outcomes
        # AsyncMock side_effect with exception works.
        # AsyncMock side_effect with iterable of values works IF the values are what is returned by 'await'.
        
        mock_status = MagicMock()
        mock_status.status.available_replicas = 1
        mock_status.spec.replicas = 1
        
        # Define side_effect function to handle logic safely
        async def side_effect(*args, **kwargs):
            val = next(results)
            if isinstance(val, Exception):
                raise val
            return val

        # Iterator for results: 
        # 1. 404 (Existence Check)
        # 2. Status (Wait Loop)
        results = iter([
            ApiException(status=404),
            mock_status
        ])
        
        # NOTE: AsyncMock needs to RAISE the exception if it's in side_effect?
        # If side_effect yields an Exception object, AsyncMock raises it.
        
        mock_apps.read_namespaced_deployment = AsyncMock(side_effect=results)

        resource = ResourceDefinition(
            name="web-app",
            type="compute", 
            provider="kubernetes",
            specs={"image": "nginx", "replicas": 1},
            metadata={"blueprint_name": "test"}
        )
        plan = MagicMock()
        plan.to_create = [resource]
        plan.to_update = []
        
        # Patch _construct_deployment to avoid deep client mocking issues
        mock_body = MagicMock()
        mock_body.kind = "Deployment"
        mock_body.metadata.name = "web-app"
        
        with patch.object(engine, "_construct_deployment", return_value=mock_body):
            await engine.apply(plan)
        
        # Verify side_effect calls
        # 1. read (404)
        # 2. create (called)
        
        mock_apps.create_namespaced_deployment.assert_called_once()
        args, kwargs = mock_apps.create_namespaced_deployment.call_args
        assert kwargs["namespace"] == "test-ns"
        assert kwargs["body"] == mock_body # Direct object comparison
        assert kwargs["body"].kind == "Deployment"

    @pytest.mark.asyncio
    async def test_apply_deployment_update(self, engine, mock_k8s_client):
        """Test updating an existing deployment."""
        mock_client, mock_apps, mock_core = mock_k8s_client
        
        mock_core.read_namespace = AsyncMock()
        
        mock_status = MagicMock()
        # Ensure these are ints
        mock_status.status.available_replicas = 1
        mock_status.spec.replicas = 1
        
        mock_apps.read_namespaced_deployment = AsyncMock(return_value=mock_status)
        mock_apps.patch_namespaced_deployment = AsyncMock()
        
        resource = ResourceDefinition(
            name="web-app",
            type="compute", 
            provider="kubernetes",
            specs={"image": "nginx:latest"},
            metadata={"blueprint_name": "test"}
        )
        plan = MagicMock()
        plan.to_create = []
        plan.to_update = [(MagicMock(), resource)]
        
        await engine.apply(plan)
        
        mock_apps.patch_namespaced_deployment.assert_called_once()

    @pytest.mark.asyncio
    async def test_destroy_resource(self, engine, mock_k8s_client):
        _, mock_apps, _ = mock_k8s_client
        
        mock_apps.delete_namespaced_deployment = AsyncMock()
        
        res_state = MagicMock()
        res_state.id = "web-app"
        res_state.type = "compute"
        
        plan = MagicMock()
        plan.to_delete = [res_state]
        
        await engine.destroy(plan)
        
        mock_apps.delete_namespaced_deployment.assert_called_once_with(
            name="web-app", namespace="test-ns"
        )
