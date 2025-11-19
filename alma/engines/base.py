"""Base engine interface for infrastructure providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

# These are now the primary models for state and planning.
from alma.core.state import Plan, ResourceState
from alma.schemas.blueprint import SystemBlueprint


class Engine(ABC):
    """
    Abstract base class for infrastructure engines.

    Engines implement the logic to translate a declarative Plan into
    actions on a specific infrastructure provider (e.g., Kubernetes, Proxmox).
    """

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        """
        Initialize the engine.

        Args:
            config: Engine-specific configuration.
        """
        self.config = config or {}

    @abstractmethod
    async def apply(self, plan: Plan) -> None:
        """
        Applies a plan to the infrastructure.

        This method should handle resource creation and updates idempotently.

        Args:
            plan: The execution plan from the state differ.
        """
        pass

    @abstractmethod
    async def destroy(self, plan: Plan) -> None:
        """
        Destroys resources specified in a plan.

        Args:
            plan: The execution plan containing resources to be deleted.
        """
        pass

    @abstractmethod
    async def get_state(self, blueprint: SystemBlueprint) -> List[ResourceState]:
        """
        Get the current state of all resources managed by a blueprint.

        Args:
            blueprint: The system blueprint to query the state for.

        Returns:
            A list of ResourceState objects representing the current infrastructure.
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the engine can connect to its provider.

        Returns:
            True if healthy, False otherwise.
        """
        return True

    def get_supported_resource_types(self) -> List[str]:
        """
        Get list of resource types supported by this engine.

        Returns:
            List of supported resource type names.
        """
        return []