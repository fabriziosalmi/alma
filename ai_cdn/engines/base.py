"""Base engine interface for infrastructure providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel


class DeploymentStatus(str, Enum):
    """Deployment status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ResourceStatus(str, Enum):
    """Resource status enumeration."""

    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    DELETED = "deleted"


class DeploymentResult(BaseModel):
    """Result of a deployment operation."""

    status: DeploymentStatus
    message: str
    resources_created: List[str] = []
    resources_failed: List[str] = []
    metadata: Dict[str, Any] = {}


class ResourceState(BaseModel):
    """Current state of a resource."""

    resource_id: str
    resource_type: str
    status: ResourceStatus
    properties: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class Engine(ABC):
    """
    Abstract base class for infrastructure engines.

    Each engine implements the deployment and management logic
    for a specific infrastructure provider (Proxmox, MikroTik, etc.).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the engine.

        Args:
            config: Engine-specific configuration
        """
        self.config = config or {}

    @abstractmethod
    async def validate_blueprint(self, blueprint: Dict[str, Any]) -> bool:
        """
        Validate a blueprint before deployment.

        Args:
            blueprint: The system blueprint to validate

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If blueprint is invalid
        """
        pass

    @abstractmethod
    async def deploy(self, blueprint: Dict[str, Any]) -> DeploymentResult:
        """
        Deploy resources according to the blueprint.

        Args:
            blueprint: The system blueprint to deploy

        Returns:
            DeploymentResult with status and details
        """
        pass

    @abstractmethod
    async def get_state(self, resource_id: str) -> ResourceState:
        """
        Get current state of a resource.

        Args:
            resource_id: Unique identifier of the resource

        Returns:
            Current state of the resource
        """
        pass

    @abstractmethod
    async def destroy(self, resource_id: str) -> bool:
        """
        Destroy a resource.

        Args:
            resource_id: Unique identifier of the resource

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def rollback(self, deployment_id: str, target_state: Optional[str] = None) -> bool:
        """
        Rollback a deployment to a previous state.

        Args:
            deployment_id: Unique identifier of the deployment
            target_state: Optional specific state to rollback to

        Returns:
            True if successful, False otherwise
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the engine can connect to its provider.

        Returns:
            True if healthy, False otherwise
        """
        return True

    def get_supported_resource_types(self) -> List[str]:
        """
        Get list of resource types supported by this engine.

        Returns:
            List of supported resource type names
        """
        return []
