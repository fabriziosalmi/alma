"""
Test for SystemBlueprint schema
"""
import pytest
from alma.schemas.blueprint import SystemBlueprint, ResourceDefinition


def test_system_blueprint_creation():
    """Test creating a valid SystemBlueprint"""
    blueprint = SystemBlueprint(
        id=1,
        created_at="2025-11-20T12:00:00",
        updated_at="2025-11-20T12:00:00",
        name="test-blueprint",
        resources=[],
    )

    assert blueprint.name == "test-blueprint"
    assert blueprint.version == "1.0"


def test_blueprint_with_compute_node():
    """Test blueprint with a ComputeNode resource"""
    compute_node = ResourceDefinition(
        type="compute",
        name="test-node",
        provider="fake",
        specs={"cpu": 4, "memory": "8Gi", "storage": "100GB"},
    )

    blueprint = SystemBlueprint(
        id=1,
        created_at="2025-11-20T12:00:00",
        updated_at="2025-11-20T12:00:00",
        name="test-with-node",
        resources=[compute_node],
    )

    assert len(blueprint.resources) == 1
    assert blueprint.resources[0].name == "test-node"
    assert blueprint.resources[0].type == "compute"


def test_blueprint_serialization():
    """Test blueprint JSON serialization"""
    blueprint = SystemBlueprint(
        id=1,
        created_at="2025-11-20T12:00:00",
        updated_at="2025-11-20T12:00:00",
        name="serialize-test",
        resources=[],
    )

    json_data = blueprint.model_dump()

    assert json_data["name"] == "serialize-test"

    # Test deserialization
    blueprint_restored = SystemBlueprint(**json_data)
    assert blueprint_restored.name == "serialize-test"
