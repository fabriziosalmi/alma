"""Pydantic schemas for System Blueprints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResourceSpec(BaseModel):
    """Specification for a single resource."""

    cpu: int | None = None
    memory: str | None = None
    storage: str | None = None
    network: str | None = None


class ResourceDefinition(BaseModel):
    """Definition of an infrastructure resource."""

    type: str = Field(..., description="Type of resource (compute, network, storage, etc.)")
    name: str = Field(..., description="Name of the resource")
    provider: str = Field(..., description="Infrastructure provider (proxmox, mikrotik, etc.)")
    specs: dict[str, Any] = Field(default_factory=dict, description="Resource specifications")
    dependencies: list[str] = Field(
        default_factory=list, description="List of resource names this depends on"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SystemBlueprintBase(BaseModel):
    """Base schema for System Blueprint."""

    version: str = Field(default="1.0", description="Blueprint version")
    name: str = Field(..., description="Name of the blueprint")
    description: str | None = Field(None, description="Description of the blueprint")
    resources: list[ResourceDefinition] = Field(..., description="List of resources to deploy")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional blueprint metadata"
    )


class SystemBlueprintCreate(SystemBlueprintBase):
    """Schema for creating a new System Blueprint."""

    pass


class SystemBlueprintUpdate(BaseModel):
    """Schema for updating a System Blueprint."""

    version: str | None = None
    name: str | None = None
    description: str | None = None
    resources: list[ResourceDefinition] | None = None
    metadata: dict[str, Any] | None = None


class SystemBlueprintInDB(SystemBlueprintBase):
    """Schema for System Blueprint in database."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        # Map the blueprint_metadata field to metadata when reading from SQLAlchemy
        # This allows Pydantic to read blueprint_metadata as metadata
    )


class SystemBlueprint(SystemBlueprintInDB):
    """Public schema for System Blueprint."""

    pass


class DeploymentRequest(BaseModel):
    """Request to deploy a blueprint."""

    dry_run: bool = Field(default=False, description="If true, only validate without deploying")
    engine: str | None = Field(None, description="Specific engine to use (overrides default)")


class DeploymentResponse(BaseModel):
    """Response from a deployment operation."""

    deployment_id: str
    status: str
    message: str
    plan_summary: str | None = None
    resources_created: list[str] = []
    resources_failed: list[str] = []
    metadata: dict[str, Any] = {}
