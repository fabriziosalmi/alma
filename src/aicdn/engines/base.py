"""
Base Engine interface - Abstract Base Class for all engines
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DeployStatus(str, Enum):
    """Status of deployment operations"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeployResult(BaseModel):
    """Result of a deploy operation"""

    status: DeployStatus
    endpoint: str | None = Field(None, description="Endpoint URL if applicable")
    message: str | None = Field(None, description="Status message")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Provider-specific metadata")
    error: str | None = Field(None, description="Error message if failed")


class ActionStatus(BaseModel):
    """Status of generic actions (destroy, update, etc.)"""

    success: bool
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResourceStatus(BaseModel):
    """Status of a resource"""

    state: str
    ready: bool = False
    endpoint: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseEngine(ABC):
    """
    Abstract Base Class for all infrastructure engines.

    Every engine (NetworkEngine, ComputeEngine, ServiceEngine) must inherit from this
    and implement all abstract methods.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize the engine with configuration

        Args:
            config: Engine-specific configuration
        """
        self.config = config or {}

    @abstractmethod
    async def deploy(self, resource_config: dict[str, Any]) -> DeployResult:
        """
        Deploy a resource based on its configuration

        Args:
            resource_config: Resource configuration dictionary

        Returns:
            DeployResult with status and metadata
        """
        pass

    @abstractmethod
    async def destroy(self, resource_config: dict[str, Any]) -> ActionStatus:
        """
        Destroy a deployed resource

        Args:
            resource_config: Resource configuration dictionary

        Returns:
            ActionStatus indicating success/failure
        """
        pass

    @abstractmethod
    async def get_status(self, resource_config: dict[str, Any]) -> ResourceStatus:
        """
        Get the current status of a resource

        Args:
            resource_config: Resource configuration dictionary

        Returns:
            ResourceStatus with current state
        """
        pass

    @abstractmethod
    async def dry_run(self, resource_config: dict[str, Any]) -> dict[str, Any]:
        """
        Perform a dry run to show what would be changed

        Args:
            resource_config: Resource configuration dictionary

        Returns:
            Dictionary describing the planned changes
        """
        pass

    def validate_config(self, resource_config: dict[str, Any]) -> bool:
        """
        Validate resource configuration (can be overridden)

        Args:
            resource_config: Resource configuration dictionary

        Returns:
            True if valid, False otherwise
        """
        return True
