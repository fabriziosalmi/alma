"""Event Sourcing Core."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Type

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from alma.models.event import EventModel

logger = logging.getLogger(__name__)


class Event(BaseModel):
    """Base class for all domain events."""

    aggregate_id: str
    aggregate_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

    @property
    def event_type(self) -> str:
        return self.__class__.__name__


class EventStore:
    """Persists events to the database."""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory

    async def append(self, event: Event) -> None:
        """Save an event to the store."""
        async with self.session_factory() as session:
            async with session.begin():
                db_event = EventModel(
                    aggregate_id=event.aggregate_id,
                    aggregate_type=event.aggregate_type,
                    event_type=event.event_type,
                    payload=event.model_dump(mode="json"),
                    timestamp=event.timestamp,
                    version=event.version,
                )
                session.add(db_event)
                logger.debug(f"Persisted event: {event.event_type} for {event.aggregate_id}")

    async def get_events(self, aggregate_id: str) -> list[EventModel]:
        """Retrieve all events for an aggregate."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(EventModel)
                .where(EventModel.aggregate_id == aggregate_id)
                .order_by(EventModel.timestamp)
            )
            return result.scalars().all()


class EventBus:
    """
    In-memory Event Bus for dispatching events to handlers (Projectors/Sagas).
    """

    def __init__(self, store: EventStore):
        self.store = store
        self.handlers: dict[Type[Event], list[Callable[[Event], Any]]] = {}

    def subscribe(self, event_type: Type[Event], handler: Callable[[Event], Any]) -> None:
        """Register a handler for an event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Subscribed {handler.__name__} to {event_type.__name__}")

    async def publish(self, event: Event) -> None:
        """Persist event and notify subscribers."""
        # 1. Persist
        await self.store.append(event)

        # 2. Notify (Fire and Forget or Await?)
        # For consistency, we usually await handlers in simple systems.
        # For high throughput, we might background them.
        # We'll await for now to ensure read models are updated before returning.

        handlers = self.handlers.get(type(event), [])
        if handlers:
            logger.debug(f"Dispatching {event.event_type} to {len(handlers)} handlers")
            results = await asyncio.gather(*[h(event) for h in handlers], return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.error(f"Error handling event {event.event_type}: {r}")
