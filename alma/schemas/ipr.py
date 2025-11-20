"""Pydantic schemas for Infrastructure Pull Requests."""

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class IPRBase(BaseModel):
    """Base schema for IPR."""

    title: str = Field(..., description="Title of the IPR")
    description: Optional[str] = Field(None, description="Detailed description")
    blueprint_id: int = Field(..., description="ID of the blueprint to deploy")


class IPRCreate(IPRBase):
    """Schema for creating a new IPR."""

    created_by: str = Field(..., description="User creating the IPR")
    changes_summary: Optional[Dict[str, Any]] = Field(None, description="Summary of changes")


class IPRUpdate(BaseModel):
    """Schema for updating an IPR."""

    title: Optional[str] = None
    description: Optional[str] = None
    review_comments: Optional[str] = None


class IPRReview(BaseModel):
    """Schema for reviewing an IPR."""

    approved: bool = Field(..., description="Whether to approve or reject")
    reviewed_by: str = Field(..., description="User reviewing the IPR")
    review_comments: Optional[str] = Field(None, description="Review comments")


class IPRInDB(IPRBase):
    """Schema for IPR in database."""

    id: int
    blueprint_snapshot: Dict[str, Any]
    changes_summary: Optional[Dict[str, Any]] = None
    status: str
    created_by: str
    reviewed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    deployment_id: Optional[str] = None
    review_comments: Optional[str] = None
    metadata: Dict[str, Any] = {}

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
