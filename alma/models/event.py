"""Event model."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String

from alma.models.blueprint import Base


class EventModel(Base):
    """
    Database model for an Event.

    Implements the Event Sourcing pattern by storing an immutable log of state changes.
    """

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    aggregate_id = Column(String, index=True, nullable=False)
    aggregate_type = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    version = Column(Integer, nullable=False, default=1)
