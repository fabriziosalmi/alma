"""CQRS Core."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alma.core.events import Event
from alma.models.view import InfrastructureViewModel

logger = logging.getLogger(__name__)


class Projector(ABC):
    """
    Base class for Projectors.

    Projectors listen to events and update Read Models.
    """

    @abstractmethod
    async def handle(self, event: Event) -> None:
        pass


class InfrastructureProjector(Projector):
    """
    Updates the Infrastructure View.
    """

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory

    async def handle(self, event: Event) -> None:
        """Handle events and update the view."""
        # We assume aggregate_id is the blueprint_id for simplicity in this example
        try:
            blueprint_id = int(event.aggregate_id)
        except ValueError:
            return

        async with self.session_factory() as session:
            async with session.begin():
                # Get or create view
                result = await session.execute(
                    select(InfrastructureViewModel).where(
                        InfrastructureViewModel.blueprint_id == blueprint_id
                    )
                )
                view = result.scalars().first()

                if not view:
                    view = InfrastructureViewModel(blueprint_id=blueprint_id)
                    session.add(view)

                # Update based on event type
                if event.event_type == "DeploymentStarted":
                    view.status = "DEPLOYING"
                elif event.event_type == "DeploymentCompleted":
                    view.status = "ACTIVE"
                elif event.event_type == "DeploymentFailed":
                    view.status = "FAILED"
                elif event.event_type == "ResourceProvisioned":
                    # Update resource list in the view
                    # Payload: {"resource_id": "...", "status": "..."}
                    resources = dict(view.resources)
                    res_id = event.model_dump().get("payload", {}).get("resource_id")
                    if res_id:
                        resources[res_id] = "PROVISIONED"
                        view.resources = resources

                view.last_updated = datetime.utcnow()
                logger.debug(f"Updated InfrastructureView for {blueprint_id} to {view.status}")

