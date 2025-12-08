"""SQLAlchemy models for System Blueprints."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass


class SystemBlueprintModel(Base):
    """Database model for System Blueprint."""

    __tablename__ = "system_blueprints"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), nullable=False, default="1.0")
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    resources = Column(JSON, nullable=False)
    blueprint_metadata = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<SystemBlueprint(id={self.id}, name={self.name}, version={self.version})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "resources": self.resources,
            "metadata": self.blueprint_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
