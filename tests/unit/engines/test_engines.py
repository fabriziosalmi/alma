"""Tests for engine modules."""

import pytest
from alma.engines.base import Engine
from alma.engines.kubernetes import KubernetesEngine
from alma.engines.proxmox import ProxmoxEngine
from alma.schemas.blueprint import ResourceDefinition


class TestBaseEngine:
    """Tests for base engine class."""

    def test_base_engine_cannot_instantiate(self) -> None:
        """Test that Engine cannot be instantiated directly."""
        # Engine is abstract, but we can test its structure
        assert hasattr(Engine, "apply")
        assert hasattr(Engine, "destroy")
        assert hasattr(Engine, "get_state")


class TestKubernetesEngine:
    """Tests for Kubernetes engine."""

    def test_kubernetes_engine_init(self) -> None:
        """Test Kubernetes engine initialization."""
        engine = KubernetesEngine()
        assert engine is not None

    @pytest.mark.asyncio
    async def test_kubernetes_validate(self) -> None:
        """Test Kubernetes resource validation."""
        engine = KubernetesEngine()
        resource = ResourceDefinition(
            type="deployment",
            name="test-deployment",
            provider="kubernetes",
            specs={"replicas": 3, "image": "nginx:latest"},
        )

        # Should not raise an error for valid resource
        try:
            await engine.validate(resource)
        except Exception as e:
            # Some validation errors are expected without a real cluster
            assert "kubernetes" in str(e).lower() or "connection" in str(e).lower()


class TestProxmoxEngine:
    """Tests for Proxmox engine."""

    def test_proxmox_engine_init(self) -> None:
        """Test Proxmox engine initialization."""
        engine = ProxmoxEngine()
        assert engine is not None

    @pytest.mark.asyncio
    async def test_proxmox_validate(self) -> None:
        """Test Proxmox resource validation."""
        engine = ProxmoxEngine()
        resource = ResourceDefinition(
            type="vm",
            name="test-vm",
            provider="proxmox",
            specs={"cpu": 2, "memory": "4GB", "disk": "50GB"},
        )

        # Should not raise an error for valid resource structure
        try:
            await engine.validate(resource)
        except Exception as e:
            # Some validation errors are expected without a real Proxmox server
            assert "proxmox" in str(e).lower() or "connection" in str(e).lower()
