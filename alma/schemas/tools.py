"""Pydantic schemas for infrastructure tools."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    """Request schema for tool execution."""

    name: str = Field(..., description="Name of the tool to execute")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    context: Optional[dict[str, Any]] = Field(None, description="Optional execution context")


class ToolResponse(BaseModel):
    """Response schema for tool execution."""

    success: bool = Field(..., description="Whether the tool executed successfully")
    tool: str = Field(..., description="Name of the executed tool")
    result: Optional[dict[str, Any]] = Field(None, description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")


class ResourceEstimateRequest(BaseModel):
    """Request schema for resource estimation."""

    workload_type: str = Field(..., description="Type of workload (web, database, cache, etc.)")
    expected_load: Optional[str] = Field(None, description="Expected load description")
    availability: str = Field(
        "standard", description="Availability level (standard, high, critical)"
    )


class ResourceSpecs(BaseModel):
    """Resource specifications."""

    cpu: int = Field(..., description="Number of CPU cores")
    memory: str = Field(..., description="Memory size (e.g., '4GB')")
    storage: str = Field(..., description="Storage size (e.g., '50GB')")


class CostBreakdown(BaseModel):
    """Cost breakdown details."""

    hourly_usd: Optional[float] = Field(None, description="Hourly cost in USD")
    monthly_usd: float = Field(..., description="Monthly cost in USD")
    yearly_usd: Optional[float] = Field(None, description="Yearly cost in USD")
    estimate_type: str = Field(..., description="Type of estimate (ESTIMATED, REAL, FALLBACK)")
    confidence: Optional[str] = Field(None, description="Confidence level (low, medium, high)")
    note: Optional[str] = Field(None, description="Additional notes")
    pricing_source: Optional[str] = Field(None, description="Source of pricing data")
    breakdown: Optional[dict[str, Any]] = Field(None, description="Detailed breakdown")


class ResourceEstimateResponse(BaseModel):
    """Response schema for resource estimation."""

    workload_type: str
    expected_load: Optional[str] = None
    recommended_specs: ResourceSpecs
    recommended_instances: int
    availability_level: str
    estimated_monthly_cost: float
    cost_breakdown: CostBreakdown


class BlueprintRequest(BaseModel):
    """Request schema for blueprint operations."""

    name: str = Field(..., description="Blueprint name")
    description: Optional[str] = Field(None, description="Blueprint description")
    resources: list[dict[str, Any]] = Field(
        default_factory=list, description="Resource definitions"
    )


class ValidationIssue(BaseModel):
    """Validation issue details."""

    severity: str = Field(..., description="Issue severity (error, warning)")
    message: str = Field(..., description="Issue description")
    field: Optional[str] = Field(None, description="Field that caused the issue")


class BlueprintValidationResponse(BaseModel):
    """Response schema for blueprint validation."""

    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
