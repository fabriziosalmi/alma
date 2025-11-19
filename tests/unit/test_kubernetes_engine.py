"""Unit tests for the KubernetesEngine."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from kubernetes_asyncio.client import (
    ApiException,
    V1Deployment, V1DeploymentSpec,
    V1Service, V1ServiceSpec,
    V1ObjectMeta, V1PodTemplateSpec, V1PodSpec, V1Container, V1ContainerPort,
    V1LabelSelector, V1ServicePort
)

from alma.engines.kubernetes import KubernetesEngine
from alma.core.state import Plan, ResourceState
from alma.schemas.blueprint import SystemBlueprint, ResourceDefinition

pytestmark = pytest.mark.asyncio

@pytest.fixture
def k8s_engine():
    """Fixture to provide a mocked KubernetesEngine."""
    with patch('alma.engines.kubernetes.config') as mock_k8s_config:
        engine = KubernetesEngine(config_dict={"namespace": "test-ns"})
        
        # Mock the entire client so we don't need a real cluster
        mock_apps_v1 = AsyncMock()
        mock_core_v1 = AsyncMock()

        engine.apps_v1 = mock_apps_v1
        engine.core_v1 = mock_core_v1
        engine.api_client = MagicMock() # Avoids re-initialization
        
        yield engine, mock_apps_v1, mock_core_v1

@pytest.fixture
def test_blueprint():
    """Fixture to provide a test SystemBlueprint."""
    return SystemBlueprint(
        id=1, name="test-bp", resources=[],
        created_at="2025-01-01T00:00:00Z", updated_at="2025-01-01T00:00:00Z"
    )


async def test_get_state_empty(k8s_engine, test_blueprint):
    """Test get_state when no resources are found."""
    engine, mock_apps_v1, mock_core_v1 = k8s_engine
    mock_apps_v1.list_namespaced_deployment.return_value.items = []
    mock_core_v1.list_namespaced_service.return_value.items = []

    state = await engine.get_state(test_blueprint)
    
    assert state == []
    mock_apps_v1.list_namespaced_deployment.assert_called_with(
        namespace="test-ns", label_selector="ALMA-blueprint=test-bp"
    )

async def test_get_state_with_deployment(k8s_engine, test_blueprint):
    """Test get_state correctly translates a V1Deployment."""
    engine, mock_apps_v1, mock_core_v1 = k8s_engine
    labels = {"app": "my-app"}
    mock_dep = V1Deployment(
        metadata=V1ObjectMeta(name="my-app"),
        spec=V1DeploymentSpec(
            replicas=2,
            selector=V1LabelSelector(match_labels=labels),
            template=V1PodTemplateSpec(
                metadata=V1ObjectMeta(labels=labels),
                spec=V1PodSpec(
                    containers=[V1Container(
                        name="my-app",
                        image="nginx:latest",
                        ports=[V1ContainerPort(container_port=80)]
                    )]
                )
            )
        )
    )
    mock_apps_v1.list_namespaced_deployment.return_value.items = [mock_dep]
    mock_core_v1.list_namespaced_service.return_value.items = []

    states = await engine.get_state(test_blueprint)

    assert len(states) == 1
    state = states[0]
    assert state.id == "my-app"
    assert state.type == "compute"
    assert state.config["replicas"] == 2
    assert state.config["image"] == "nginx:latest"

async def test_apply_create_deployment(k8s_engine):
    """Test apply correctly creates a new deployment."""
    engine, mock_apps_v1, _ = k8s_engine
    resource = ResourceDefinition(
        name="new-app", type="compute", provider="kubernetes",
        specs={"image": "my-image:1.0", "replicas": 3, "port": 8080},
        metadata={"blueprint_name": "test-bp"}
    )
    plan = Plan(to_create=[resource])
    
    mock_apps_v1.read_namespaced_deployment.side_effect = ApiException(status=404)

    await engine.apply(plan)

    mock_apps_v1.create_namespaced_deployment.assert_called_once()
    call_args = mock_apps_v1.create_namespaced_deployment.call_args
    assert call_args.kwargs['namespace'] == 'test-ns'
    deployment_body = call_args.kwargs['body']
    assert deployment_body.metadata.name == "new-app"
    assert deployment_body.spec.replicas == 3
    assert deployment_body.spec.template.spec.containers[0].image == "my-image:1.0"

async def test_apply_patch_deployment(k8s_engine):
    """Test apply correctly patches an existing deployment."""
    engine, mock_apps_v1, _ = k8s_engine
    resource = ResourceDefinition(
        name="existing-app", type="compute", provider="kubernetes",
        specs={"image": "my-image:2.0"},
        metadata={"blueprint_name": "test-bp"}
    )
    old_state = ResourceState(id="existing-app", type="compute", config={"image": "my-image:1.0"})
    plan = Plan(to_update=[(old_state, resource)])

    mock_apps_v1.read_namespaced_deployment.return_value = MagicMock()

    await engine.apply(plan)

    mock_apps_v1.patch_namespaced_deployment.assert_called_once()
    call_args = mock_apps_v1.patch_namespaced_deployment.call_args
    assert call_args.kwargs['name'] == 'existing-app'
    deployment_body = call_args.kwargs['body']
    assert deployment_body.spec.template.spec.containers[0].image == "my-image:2.0"

async def test_destroy_deployment(k8s_engine):
    """Test destroy correctly calls delete for a deployment."""
    engine, mock_apps_v1, _ = k8s_engine
    resource_state = ResourceState(id="app-to-delete", type="compute", config={})
    plan = Plan(to_delete=[resource_state])

    await engine.destroy(plan)

    mock_apps_v1.delete_namespaced_deployment.assert_called_once_with(
        name="app-to-delete", namespace="test-ns"
    )

async def test_destroy_service_ignores_404(k8s_engine):
    """Test destroy ignores 404 errors on deletion."""
    engine, _, mock_core_v1 = k8s_engine
    resource_state = ResourceState(id="svc-to-delete", type="network", config={})
    plan = Plan(to_delete=[resource_state])

    mock_core_v1.delete_namespaced_service.side_effect = ApiException(status=404)

    await engine.destroy(plan)

    mock_core_v1.delete_namespaced_service.assert_called_once_with(
        name="svc-to-delete", namespace="test-ns"
    )
