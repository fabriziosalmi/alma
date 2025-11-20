"""
SystemBlueprint model - the core declarative format
"""

from typing import Any

from pydantic import BaseModel, Field

from aicdn.models.resources import ResourceDefinition


class BlueprintMetadata(BaseModel):
    """Metadata for SystemBlueprint"""

    name: str = Field(..., description="Blueprint name")
    description: str | None = Field(None, description="Blueprint description")
    version: str = Field(default="v1", description="Blueprint API version")
    labels: dict[str, str] = Field(default_factory=dict, description="Labels for organization")
    annotations: dict[str, str] = Field(default_factory=dict, description="Annotations")


class BlueprintSpec(BaseModel):
    """Specification for SystemBlueprint"""

    resources: list[ResourceDefinition] = Field(
        default_factory=list, description="List of resources"
    )
    variables: dict[str, Any] = Field(default_factory=dict, description="Blueprint variables")


class SystemBlueprint(BaseModel):
    """
    SystemBlueprint: The declarative definition of infrastructure state

    This is the core format that describes the desired state of the entire system.
    """

    apiVersion: str = Field(default="cdn-ng.io/v1", description="API version")
    kind: str = Field(default="SystemBlueprint", description="Resource kind")
    metadata: BlueprintMetadata = Field(..., description="Blueprint metadata")
    spec: BlueprintSpec = Field(..., description="Blueprint specification")

    class Config:
        json_schema_extra = {
            "example": {
                "apiVersion": "cdn-ng.io/v1",
                "kind": "SystemBlueprint",
                "metadata": {
                    "name": "my-cdn-pop",
                    "description": "CDN PoP in Milan",
                    "version": "v1",
                },
                "spec": {
                    "resources": [
                        {
                            "kind": "ComputeNode",
                            "name": "cache-01",
                            "spec": {"cpu": 4, "memory": "8Gi", "architecture": "x86_64"},
                        }
                    ]
                },
            }
        }
