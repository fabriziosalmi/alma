"""
Test for SystemBlueprint model
"""
import pytest
from aicdn.models.blueprint import SystemBlueprint, BlueprintMetadata, BlueprintSpec
from aicdn.models.resources import ComputeNode, ComputeNodeSpec, ResourceKind


def test_system_blueprint_creation():
    """Test creating a valid SystemBlueprint"""
    blueprint = SystemBlueprint(
        metadata=BlueprintMetadata(name="test-blueprint"),
        spec=BlueprintSpec(resources=[])
    )
    
    assert blueprint.apiVersion == "cdn-ng.io/v1"
    assert blueprint.kind == "SystemBlueprint"
    assert blueprint.metadata.name == "test-blueprint"


def test_blueprint_with_compute_node():
    """Test blueprint with a ComputeNode resource"""
    compute_node = ComputeNode(
        name="test-node",
        spec=ComputeNodeSpec(
            cpu=4,
            memory="8Gi",
            architecture="x86_64"
        )
    )
    
    blueprint = SystemBlueprint(
        metadata=BlueprintMetadata(name="test-with-node"),
        spec=BlueprintSpec(resources=[compute_node])
    )
    
    assert len(blueprint.spec.resources) == 1
    assert blueprint.spec.resources[0].name == "test-node"
    assert blueprint.spec.resources[0].kind == ResourceKind.COMPUTE_NODE


def test_blueprint_serialization():
    """Test blueprint JSON serialization"""
    blueprint = SystemBlueprint(
        metadata=BlueprintMetadata(name="serialize-test"),
        spec=BlueprintSpec(resources=[])
    )
    
    json_data = blueprint.model_dump()
    
    assert json_data["apiVersion"] == "cdn-ng.io/v1"
    assert json_data["metadata"]["name"] == "serialize-test"
    
    # Test deserialization
    blueprint_restored = SystemBlueprint(**json_data)
    assert blueprint_restored.metadata.name == "serialize-test"
