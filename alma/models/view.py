"""Read models for CQRS."""

from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from alma.models.blueprint import Base


class InfrastructureViewModel(Base):
    """
    Read model for Infrastructure status.

    Optimized for queries, updated by Projectors.
    """

    __tablename__ = "infrastructure_views"

    id = Column(Integer, primary_key=True, index=True)
    blueprint_id = Column(Integer, index=True, unique=True, nullable=False)
    status = Column(String, default="UNKNOWN", index=True)
    resources = Column(JSON, default={})
    last_updated = Column(DateTime, default=datetime.utcnow)
