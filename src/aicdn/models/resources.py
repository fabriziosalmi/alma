"""
Pydantic models for resources (ComputeNode, NetworkLink, etc.)
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ResourceKind(str, Enum):
    """Supported resource types"""

    COMPUTE_NODE = "ComputeNode"
    NETWORK_LINK = "NetworkLink"
    SERVICE_INSTANCE = "ServiceInstance"
    NETWORK_DOMAIN = "NetworkDomain"
    SECURITY_RULE = "SecurityRule"
    STORAGE_VOLUME = "StorageVolume"


class EngineSelector(BaseModel):
    """Engine selector for resource provisioning"""

    vendor: str | None = Field(None, description="Vendor name (e.g., 'proxmox', 'mikrotik')")
    type: str | None = Field(None, description="Resource type (e.g., 'lxc', 'vm', 'bare-metal')")
    version: str | None = Field(None, description="Version constraint")


class ResourceDefinition(BaseModel):
    """Base class for all infrastructure resources"""

    kind: ResourceKind = Field(..., description="Resource type")
    name: str = Field(..., description="Unique resource name")
    spec: dict[str, Any] = Field(default_factory=dict, description="Resource specification")
    engineSelector: EngineSelector | None = Field(
        None, description="Engine to use for provisioning"
    )
    connections: dict[str, Any] = Field(default_factory=dict, description="Resource connections")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ComputeNodeSpec(BaseModel):
    """Specification for compute node resources"""

    cpu: int = Field(..., ge=1, description="Number of CPU cores")
    memory: str = Field(..., description="Memory size (e.g., '8Gi', '16384Mi')")
    architecture: Literal["x86_64", "arm64"] = Field(default="x86_64")
    os: str | None = Field(None, description="Operating system")


class ComputeNode(ResourceDefinition):
    """Compute node resource"""

    kind: Literal[ResourceKind.COMPUTE_NODE] = ResourceKind.COMPUTE_NODE
    spec: ComputeNodeSpec

    class Config:
        use_enum_values = True


class NetworkLinkSpec(BaseModel):
    """Specification for network link resources"""

    domain: str = Field(..., description="Network domain name")
    vlanId: int | None = Field(None, ge=1, le=4094, description="VLAN ID")
    bandwidth: str | None = Field(None, description="Bandwidth (e.g., '10Gbps')")
    mtu: int = Field(default=1500, ge=512, le=9000, description="MTU size")


class NetworkLink(ResourceDefinition):
    """Network link resource"""

    kind: Literal[ResourceKind.NETWORK_LINK] = ResourceKind.NETWORK_LINK
    spec: NetworkLinkSpec

    class Config:
        use_enum_values = True


class ServiceInstanceSpec(BaseModel):
    """Specification for service instance resources"""

    serviceDefinition: str = Field(..., description="Reference to service definition")
    replicas: int = Field(default=1, ge=1, description="Number of replicas")
    healthCheck: dict[str, Any] | None = Field(None, description="Health check configuration")
    configuration: dict[str, Any] = Field(default_factory=dict, description="Service configuration")


class ServiceInstance(ResourceDefinition):
    """Service instance resource"""

    kind: Literal[ResourceKind.SERVICE_INSTANCE] = ResourceKind.SERVICE_INSTANCE
    spec: ServiceInstanceSpec

    class Config:
        use_enum_values = True
