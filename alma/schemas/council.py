"""Schemas for The Council agents."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class InfrastructureResource(BaseModel):
    """Resource definition in the blueprint."""
    type: Literal["compute", "storage", "network", "database"]
    name: str
    provider: str = Field(description="Cloud provider or engine (e.g., proxmox, docker)")
    specs: dict[str, int | str] = Field(default_factory=dict)


class InfrastructureDraft(BaseModel):
    """Initial draft by the Architect."""
    version: str = "1.0"
    name: str
    description: str
    resources: list[InfrastructureResource]


class Vulnerability(BaseModel):
    """A security vulnerability found by SecOps."""
    severity: Literal["critical", "high", "medium", "low"]
    issue: str
    recommendation: str


class SecurityCritique(BaseModel):
    """Security review output."""
    safe: bool = Field(description="Is the design generally safe?")
    vulnerabilities: list[Vulnerability]
    summary: str


class CostItem(BaseModel):
    """Cost estimation for a resource."""
    resource_name: str
    estimated_monthly_cost: float
    currency: str = "USD"


class CostAnalysis(BaseModel):
    """Financial review output."""
    total_monthly_cost: float
    items: list[CostItem]
    savings_suggestions: list[str]


class FinalDecree(BaseModel):
    """Final autonomous decision by the Council."""
    blueprint: InfrastructureDraft
    approved: bool
    reasoning: str
