"""SQLAlchemy models for Infrastructure Pull Requests (IPR)."""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy import Enum as SQLEnum

from alma.models.blueprint import Base


class IPRStatus(str, enum.Enum):
    """IPR status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InfrastructurePullRequestModel(Base):
    """Database model for Infrastructure Pull Request."""

    __tablename__ = "infrastructure_pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    blueprint_id = Column(Integer, nullable=False, index=True)
    blueprint_snapshot = Column(JSON, nullable=False)  # Snapshot of blueprint at creation
    changes_summary = Column(JSON, nullable=True)  # Summary of changes
    status = Column(
        SQLEnum(IPRStatus),
        nullable=False,
        default=IPRStatus.PENDING,
        index=True,
    )
    created_by = Column(String(255), nullable=False)
    reviewed_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    deployment_id = Column(String(255), nullable=True)
    review_comments = Column(Text, nullable=True)
    ipr_metadata = Column("metadata", JSON, nullable=True, default=dict)

    def __repr__(self) -> str:
        """String representation."""
        return f"<IPR(id={self.id}, title={self.title}, status={self.status})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "blueprint_id": self.blueprint_id,
            "blueprint_snapshot": self.blueprint_snapshot,
            "changes_summary": self.changes_summary,
            "status": self.status.value if isinstance(self.status, IPRStatus) else self.status,
            "created_by": self.created_by,
            "reviewed_by": self.reviewed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "deployment_id": self.deployment_id,
            "review_comments": self.review_comments,
            "metadata": self.ipr_metadata,
        }
