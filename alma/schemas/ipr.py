"""Pydantic schemas for Infrastructure Pull Requests."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IPRBase(BaseModel):
    """Base schema for IPR."""

    title: str = Field(..., description="Title of the IPR")
    description: str | None = Field(None, description="Detailed description")
    blueprint_id: int = Field(..., description="ID of the blueprint to deploy")


class IPRCreate(IPRBase):
    """Schema for creating a new IPR."""

    created_by: str = Field(..., description="User creating the IPR")
    changes_summary: dict[str, Any] | None = Field(None, description="Summary of changes")


class IPRUpdate(BaseModel):
    """Schema for updating an IPR."""

    title: str | None = None
    description: str | None = None
    review_comments: str | None = None


class IPRReview(BaseModel):
    """Schema for reviewing an IPR."""

    approved: bool = Field(..., description="Whether to approve or reject")
    reviewed_by: str = Field(..., description="User reviewing the IPR")
    review_comments: str | None = Field(None, description="Review comments")


class IPRInDB(IPRBase):
    """Schema for IPR in database."""

    id: int
    blueprint_snapshot: dict[str, Any]
    changes_summary: dict[str, Any] | None = None
    status: str
    created_by: str
    reviewed_by: str | None = None
    created_at: datetime
    updated_at: datetime
    reviewed_at: datetime | None = None
    deployed_at: datetime | None = None
    deployment_id: str | None = None
    review_comments: str | None = None
    metadata: dict[str, Any] = {}

    class Config:
        """Pydantic config."""

        from_attributes = True


class IPR(IPRInDB):
    """Public schema for IPR."""

    pass


class IPRListResponse(BaseModel):
    """Response for listing IPRs."""

    iprs: list[IPR]
    total: int
    pending: int
    approved: int
    deployed: int
