"""Pydantic models for tool arguments."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class CreateBlueprintArgs(BaseModel):
    """Arguments for create_blueprint tool."""

    name: str = Field(..., description="Name of the blueprint")
    description: str | None = Field(None, description="Description of the blueprint")
    resources: list[dict[str, Any]] = Field(default_factory=list, description="List of resources")


class ValidateBlueprintArgs(BaseModel):
    """Arguments for validate_blueprint tool."""

    blueprint: dict[str, Any] = Field(..., description="Blueprint to validate")
    strict: bool = Field(False, description="Enable strict validation mode")


class EstimateResourcesArgs(BaseModel):
    """Arguments for estimate_resources tool."""

    workload_type: str = Field(..., description="Type of workload (web, database, etc.)")
    expected_load: str = Field(..., description="Expected load description")
    availability: str = Field("standard", description="Required availability level")


class OptimizeCostsArgs(BaseModel):
    """Arguments for optimize_costs tool."""

    blueprint: dict[str, Any] = Field(default_factory=dict, description="Blueprint to optimize")
    provider: str = Field("aws", description="Cloud provider")
    optimization_goal: str = Field("balanced", description="Optimization goal")


class SecurityAuditArgs(BaseModel):
    """Arguments for security_audit tool."""

    blueprint: dict[str, Any] = Field(default_factory=dict, description="Blueprint to audit")
    compliance_framework: str = Field("general", description="Compliance framework")
    severity_threshold: str = Field("medium", description="Minimum severity to report")


class GenerateDeploymentPlanArgs(BaseModel):
    """Arguments for generate_deployment_plan tool."""

    blueprint: dict[str, Any] = Field(default_factory=dict, description="Blueprint to deploy")
    strategy: str = Field("rolling", description="Deployment strategy")
    rollback_enabled: bool = Field(True, description="Enable rollback on failure")


class TroubleshootIssueArgs(BaseModel):
    """Arguments for troubleshoot_issue tool."""

    issue_description: str = Field(..., description="Description of the issue")
    affected_resources: list[str] = Field(default_factory=list, description="List of affected resources")
    symptoms: list[str] = Field(default_factory=list, description="List of symptoms")


class CompareBlueprintsArgs(BaseModel):
    """Arguments for compare_blueprints tool."""

    blueprint_a: dict[str, Any] = Field(..., description="First blueprint")
    blueprint_b: dict[str, Any] = Field(..., description="Second blueprint")


class SuggestArchitectureArgs(BaseModel):
    """Arguments for suggest_architecture tool."""

    requirements: dict[str, Any] = Field(default_factory=dict, description="Requirements")
    constraints: dict[str, Any] = Field(default_factory=dict, description="Constraints")


class CalculateCapacityArgs(BaseModel):
    """Arguments for calculate_capacity tool."""

    current_metrics: dict[str, Any] = Field(..., description="Current resource metrics")
    growth_rate: float = Field(0, description="Projected growth rate percentage")
    time_horizon: str = Field("3 months", description="Forecast time horizon")


class MigrateInfrastructureArgs(BaseModel):
    """Arguments for migrate_infrastructure tool."""

    source_platform: str = Field(..., description="Source platform")
    target_platform: str = Field(..., description="Target platform")
    migration_strategy: str = Field("replatform", description="Migration strategy")


class CheckComplianceArgs(BaseModel):
    """Arguments for check_compliance tool."""

    blueprint: dict[str, Any] = Field(default_factory=dict, description="Blueprint to check")
    standards: list[str] = Field(default_factory=list, description="List of compliance standards")


class ForecastMetricsArgs(BaseModel):
    """Arguments for forecast_metrics tool."""

    historical_data: list[dict[str, Any]] = Field(default_factory=list, description="Historical metric data")
    forecast_period: str = Field(..., description="Period to forecast")
    confidence_level: float = Field(0.95, description="Confidence level (0.0-1.0)")
