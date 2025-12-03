"""Saga Pattern Core."""

import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alma.models.saga import SagaStateModel

logger = logging.getLogger(__name__)


class SagaStep(ABC):
    """A single step in a Saga."""

    name: str

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> None:
        """Perform the action."""
        pass

    @abstractmethod
    async def compensate(self, context: dict[str, Any]) -> None:
        """Undo the action."""
        pass


class SagaOrchestrator:
    """
    Manages the execution of a Saga.
    """

    def __init__(self, session_factory: Callable[[], AsyncSession], steps: list[SagaStep]):
        self.session_factory = session_factory
        self.status = "completed"  # type: ignore[assignment]
        self.steps = steps

    async def execute(self, correlation_id: str, payload: dict[str, Any]) -> None:
        """Run the saga."""
        saga_id = str(uuid.uuid4())
        logger.info(f"Starting Saga {saga_id} for {correlation_id}")

        # Persist initial state
        async with self.session_factory() as session:
            async with session.begin():
                state = SagaStateModel(
                    saga_id=saga_id,
                    correlation_id=correlation_id,
                    status="RUNNING",
                    payload=payload,
                    history=[],
                )
                session.add(state)

        context = payload.copy()
        completed_steps = []

        try:
            for step in self.steps:
                logger.info(f"Executing step {step.name}")

                # Update state
                await self._update_state(saga_id, step.name, "EXECUTING")

                await step.execute(context)
                completed_steps.append(step)

                # Update state
                await self._update_state(saga_id, step.name, "COMPLETED")

            # Finalize
            await self._update_status(saga_id, "COMPLETED")
            logger.info(f"Saga {saga_id} completed successfully")

        except Exception as e:
            logger.error(f"Saga {saga_id} failed at step {step.name}: {e}")
            await self._update_status(saga_id, "FAILED")
            await self._compensate(saga_id, completed_steps, context)
            raise

    async def _compensate(
        self, saga_id: str, steps: list[SagaStep], context: dict[str, Any]
    ) -> None:
        """Run compensating actions in reverse order."""
        logger.info(f"Starting compensation for Saga {saga_id}")
        for step in reversed(steps):
            try:
                logger.info(f"Compensating step {step.name}")
                await step.compensate(context)
            except Exception as e:
                logger.critical(f"Compensation failed for {step.name}: {e}")
                # In real world, we might need manual intervention here

    async def _update_state(self, saga_id: str, step: str, status: str) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(SagaStateModel).where(SagaStateModel.saga_id == saga_id)
                )
                state = result.scalars().first()
                if state:
                    state.current_step = step
                    history = list(state.history)
                    history.append(
                        {"step": step, "status": status, "timestamp": str(datetime.utcnow())}
                    )
                    state.history = history

    async def _update_status(self, saga_id: str, status: str) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(SagaStateModel).where(SagaStateModel.saga_id == saga_id)
                )
                state = result.scalars().first()
                if state:
                    state.status = status
