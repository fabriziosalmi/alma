"""Saga state model."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String

from alma.models.blueprint import Base


class SagaStateModel(Base):
    """
    Database model for Saga State.

    Tracks the progress of long-running transactions.
    """

    __tablename__ = "saga_states"

    id = Column(Integer, primary_key=True, index=True)
    saga_id = Column(String, unique=True, index=True, nullable=False)
    correlation_id = Column(String, index=True, nullable=False)
    status = Column(String, default="PENDING", index=True)
    current_step = Column(String, nullable=True)
    history = Column(JSON, default=[])
    payload = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
