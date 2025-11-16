"""Pydantic schemas for System Blueprints."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ResourceSpec(BaseModel):
    """Specification for a single resource."""

    cpu: Optional[int] = None
    memory: Optional[str] = None
    storage: Optional[str] = None
    network: Optional[str] = None


class ResourceDefinition(BaseModel):
    """Definition of an infrastructure resource."""

    type: str = Field(..., description="Type of resource (compute, network, storage, etc.)")
    name: str = Field(..., description="Name of the resource")
    provider: str = Field(..., description="Infrastructure provider (proxmox, mikrotik, etc.)")
    specs: Dict[str, Any] = Field(default_factory=dict, description="Resource specifications")
    dependencies: List[str] = Field(
        default_factory=list, description="List of resource names this depends on"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SystemBlueprintBase(BaseModel):
    """Base schema for System Blueprint."""

    version: str = Field(default="1.0", description="Blueprint version")
    name: str = Field(..., description="Name of the blueprint")
    description: Optional[str] = Field(None, description="Description of the blueprint")
    resources: List[ResourceDefinition] = Field(..., description="List of resources to deploy")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional blueprint metadata"
    )


class SystemBlueprintCreate(SystemBlueprintBase):
    """Schema for creating a new System Blueprint."""

    pass


class SystemBlueprintUpdate(BaseModel):
    """Schema for updating a System Blueprint."""

    version: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    resources: Optional[List[ResourceDefinition]] = None
    metadata: Optional[Dict[str, Any]] = None


class SystemBlueprintInDB(SystemBlueprintBase):
    """Schema for System Blueprint in database."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class SystemBlueprint(SystemBlueprintInDB):
    """Public schema for System Blueprint."""

    pass


class DeploymentRequest(BaseModel):
    """Request to deploy a blueprint."""

    blueprint_id: int
    dry_run: bool = Field(default=False, description="If true, only validate without deploying")
    engine: Optional[str] = Field(None, description="Specific engine to use (overrides default)")


class DeploymentResponse(BaseModel):
    """Response from a deployment operation."""

    deployment_id: str
    status: str
    message: str
    resources_created: List[str] = []
    resources_failed: List[str] = []
    metadata: Dict[str, Any] = {}
