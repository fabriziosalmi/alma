"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from alma.schemas.blueprint import (
    DeploymentRequest,
    ResourceDefinition,
    SystemBlueprintCreate,
    SystemBlueprintUpdate,
)


class TestResourceDefinition:
    """Tests for ResourceDefinition schema."""

    def test_resource_definition_valid(self) -> None:
        """Test creating a valid resource definition."""
        resource = ResourceDefinition(
            type="compute",
            name="web-server",
            provider="proxmox",
            specs={"cpu": 4, "memory": "8GB"},
        )

        assert resource.type == "compute"
        assert resource.name == "web-server"
        assert resource.provider == "proxmox"
        assert resource.specs["cpu"] == 4
        assert resource.dependencies == []

    def test_resource_definition_with_dependencies(self) -> None:
        """Test resource definition with dependencies."""
        resource = ResourceDefinition(
            type="service",
            name="api-service",
            provider="docker",
            specs={"image": "nginx"},
            dependencies=["web-server", "database"],
        )

        assert len(resource.dependencies) == 2
        assert "web-server" in resource.dependencies

    def test_resource_definition_missing_required_fields(self) -> None:
        """Test validation fails when required fields are missing."""
        with pytest.raises(ValidationError):
            ResourceDefinition(type="compute")  # Missing name and provider


class TestSystemBlueprintCreate:
    """Tests for SystemBlueprintCreate schema."""

    def test_blueprint_create_valid(self) -> None:
        """Test creating a valid blueprint."""
        blueprint = SystemBlueprintCreate(
            version="1.0",
            name="production-cluster",
            description="Production infrastructure",
            resources=[
                ResourceDefinition(
                    type="compute",
                    name="web-server",
                    provider="proxmox",
                    specs={"cpu": 2},
                )
            ],
        )

        assert blueprint.version == "1.0"
        assert blueprint.name == "production-cluster"
        assert len(blueprint.resources) == 1

    def test_blueprint_create_minimal(self) -> None:
        """Test creating blueprint with minimal required fields."""
        blueprint = SystemBlueprintCreate(
            name="minimal",
            resources=[],
        )

        assert blueprint.version == "1.0"  # Default value
        assert blueprint.name == "minimal"
        assert blueprint.description is None
        assert blueprint.metadata == {}

    def test_blueprint_create_missing_name(self) -> None:
        """Test validation fails when name is missing."""
        with pytest.raises(ValidationError):
            SystemBlueprintCreate(resources=[])


class TestSystemBlueprintUpdate:
    """Tests for SystemBlueprintUpdate schema."""

    def test_blueprint_update_partial(self) -> None:
        """Test updating only some fields."""
        update = SystemBlueprintUpdate(name="new-name")

        assert update.name == "new-name"
        assert update.version is None
        assert update.description is None

    def test_blueprint_update_all_fields(self) -> None:
        """Test updating all fields."""
        update = SystemBlueprintUpdate(
            version="2.0",
            name="updated-name",
            description="Updated description",
            resources=[],
            metadata={"env": "staging"},
        )

        assert update.version == "2.0"
        assert update.name == "updated-name"
        assert update.metadata == {"env": "staging"}


class TestDeploymentRequest:
    """Tests for DeploymentRequest schema."""

    def test_deployment_request_minimal(self) -> None:
        """Test deployment request with minimal fields."""
        request = DeploymentRequest()

        assert request.dry_run is False
        assert request.engine is None

    def test_deployment_request_with_options(self) -> None:
        """Test deployment request with all options."""
        request = DeploymentRequest(
            dry_run=True,
            engine="proxmox",
        )

        assert request.dry_run is True
        assert request.engine == "proxmox"

    def test_deployment_request_defaults(self) -> None:
        """Test deployment request defaults."""
        request = DeploymentRequest()
        assert request.dry_run is False
        assert request.engine is None
