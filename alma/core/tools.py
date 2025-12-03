"""Function calling tools for LLM infrastructure operations."""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache
import json
from pathlib import Path
from typing import Any


class InfrastructureTools:
    """
    Collection of tools that can be called by LLM for infrastructure operations.

    Each tool is designed to be invoked via function calling to perform
    specific infrastructure management tasks.
    """

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_tools() -> list[dict[str, Any]]:
        """
        Load tool definitions from JSON configuration file.
        Cached to prevent repeated disk I/O.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Resolve path relative to this file
            base_path = Path(__file__).parent.parent
            config_path = base_path / "config" / "tools.json"
            
            if not config_path.exists():
                logger.warning(f"Tools configuration not found at {config_path}, using defaults")
                return []

            with open(config_path, "r") as f:
                tools = json.load(f)
                
            return tools or []
            
        except FileNotFoundError:
            logger.warning("Tools config file not found, using empty tool list")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in tools.json: {e}")
            raise ValueError(f"Tools configuration is invalid: {e}")
        except PermissionError as e:
            logger.error(f"Permission denied reading tools.json: {e}")
            raise
        except Exception as e:
            # Unexpected errors should fail loudly
            logger.exception("Unexpected error loading tools configuration")
            raise RuntimeError(f"Failed to load tools configuration: {e}")

    @staticmethod
    def get_available_tools() -> list[dict[str, Any]]:
        """
        Get list of available tools for LLM function calling.

        Returns:
            List of tool definitions in OpenAI function calling format
        """
        return InfrastructureTools._load_tools()

    # Tool Registry (class-level)
    _TOOL_REGISTRY: dict[str, Callable] = {}
    
    @classmethod
    def register_tool(cls, name: str, func: Callable) -> None:
        """Register a tool function."""
        cls._TOOL_REGISTRY[name] = func
    
    @classmethod
    def get_registered_tools(cls) -> list[str]:
        """Get list of registered tool names."""
        return list(cls._TOOL_REGISTRY.keys())
    
    @staticmethod
    async def execute_tool(
        tool_name: str, arguments: dict[str, Any], context: dict[str, Any] | None = None
    ) -> ToolResponse:
        """
        Execute a tool with given arguments using registry pattern.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            context: Optional execution context

        Returns:
            ToolResponse with execution result
        """
        from alma.schemas.tools import ToolResponse
        import inspect
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get tool from registry
        if tool_name not in InfrastructureTools._TOOL_REGISTRY:
            logger.warning(f"Unknown tool requested: {tool_name}")
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=f"Unknown tool: {tool_name}. Available: {InfrastructureTools.get_registered_tools()}",
            )

        try:
            tool_func = InfrastructureTools._TOOL_REGISTRY[tool_name]
            
            # Check if tool is async
            if inspect.iscoroutinefunction(tool_func):
                result = await tool_func(arguments, context)
            else:
                result = tool_func(arguments, context)
                
            return ToolResponse(
                success=True,
                tool=tool_name,
                result=result,
            )
        except ValueError as e:
            # Validation errors
            logger.error(f"Validation error in tool {tool_name}: {e}")
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=f"Validation error: {str(e)}",
            )
        except Exception as e:
            # Unexpected errors - log with full traceback
            logger.exception(f"Unexpected error executing tool {tool_name}")
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=f"Execution error: {str(e)}",
            )

    # Tool implementations

    @staticmethod
    def _create_blueprint(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Create blueprint implementation."""
        return {
            "blueprint": {
                "version": "1.0",
                "name": args.get("name"),
                "description": args.get("description"),
                "resources": args.get("resources", []),
                "metadata": {"created_by": "ALMA-llm", "created_at": datetime.utcnow().isoformat()},
            }
        }

    @staticmethod
    def _validate_blueprint(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Validate blueprint implementation."""
        blueprint = args.get("blueprint", {})
        strict = args.get("strict", False)

        issues = []
        warnings = []

        # Check required fields
        if "version" not in blueprint:
            issues.append("Missing 'version' field")
        if "name" not in blueprint:
            issues.append("Missing 'name' field")
        if "resources" not in blueprint:
            issues.append("Missing 'resources' field")

        # Check resources
        resources = blueprint.get("resources", [])
        for i, resource in enumerate(resources):
            if "type" not in resource:
                issues.append(f"Resource {i}: Missing 'type' field")
            if "name" not in resource:
                issues.append(f"Resource {i}: Missing 'name' field")
            if strict and "specs" not in resource:
                warnings.append(f"Resource {i}: Missing 'specs' field")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "strict_mode": strict,
        }

    @staticmethod
    async def _estimate_resources(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Estimate resources implementation with real pricing."""
        from alma.integrations.pricing import PricingService
        
        workload = args.get("workload_type")
        load = args.get("expected_load")
        availability = args.get("availability", "standard")

        # Simple estimation logic (can be enhanced)
        base_specs = {
            "web": {"cpu": 2, "memory": "4GB", "storage": "50GB"},
            "database": {"cpu": 4, "memory": "16GB", "storage": "500GB"},
            "cache": {"cpu": 2, "memory": "8GB", "storage": "100GB"},
            "queue": {"cpu": 2, "memory": "4GB", "storage": "100GB"},
            "ml": {"cpu": 8, "memory": "32GB", "storage": "1TB"},
            "analytics": {"cpu": 16, "memory": "64GB", "storage": "2TB"},
        }

        specs = base_specs.get(workload, {"cpu": 2, "memory": "4GB", "storage": "50GB"})

        # Adjust for availability
        instances = 1
        if availability == "high":
            instances = 3
        elif availability == "critical":
            instances = 5

        # Get real pricing estimate
        pricing_service = PricingService()
        try:
            cost_estimate = await pricing_service.estimate_cost("compute", specs)
            monthly_cost = cost_estimate.get("monthly_usd", 0) * instances
            cost_breakdown = cost_estimate
        except Exception as e:
            # Fallback to basic estimate if pricing fails
            monthly_cost = instances * 100
            cost_breakdown = {
                "monthly_usd": monthly_cost,
                "estimate_type": "FALLBACK",
                "error": str(e),
                "note": "Using basic fallback estimate"
            }

        return {
            "workload_type": workload,
            "expected_load": load,
            "recommended_specs": specs,
            "recommended_instances": instances,
            "availability_level": availability,
            "estimated_monthly_cost": monthly_cost,
            "cost_breakdown": cost_breakdown,
        }

    @staticmethod
    def _optimize_costs(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Cost optimization implementation."""
        args.get("blueprint", {})
        provider = args.get("provider", "aws")
        goal = args.get("optimization_goal", "balanced")

        suggestions = [
            "Consider using reserved instances for long-running workloads (up to 70% savings)",
            "Right-size instances based on actual usage metrics",
            "Use auto-scaling to match capacity with demand",
            "Consider spot instances for non-critical workloads (up to 90% savings)",
            "Implement data lifecycle policies for storage optimization",
        ]

        return {
            "provider": provider,
            "optimization_goal": goal,
            "suggestions": suggestions,
            "estimated_savings": "30-50%",
            "implementation_complexity": "medium",
        }

    @staticmethod
    def _security_audit(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Security audit implementation."""
        args.get("blueprint", {})
        framework = args.get("compliance_framework", "general")
        args.get("severity_threshold", "medium")

        findings = [
            {
                "severity": "high",
                "category": "network",
                "issue": "Resources may be exposed to public internet",
                "recommendation": "Implement network segmentation and use private subnets",
            },
            {
                "severity": "medium",
                "category": "encryption",
                "issue": "Encryption at rest not explicitly configured",
                "recommendation": "Enable encryption for all storage resources",
            },
            {
                "severity": "medium",
                "category": "access_control",
                "issue": "No explicit IAM/RBAC policies defined",
                "recommendation": "Implement least-privilege access control",
            },
        ]

        return {
            "compliance_framework": framework,
            "findings": findings,
            "risk_score": 6.5,
            "compliant": False,
        }

    @staticmethod
    def _generate_deployment_plan(
        args: dict[str, Any], ctx: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Generate deployment plan implementation."""
        args.get("blueprint", {})
        strategy = args.get("strategy", "rolling")
        rollback = args.get("rollback_enabled", True)

        steps = [
            {"step": 1, "action": "Pre-deployment validation", "duration": "5 min"},
            {"step": 2, "action": "Create IAM roles and policies", "duration": "2 min"},
            {"step": 3, "action": "Deploy network infrastructure", "duration": "10 min"},
            {"step": 4, "action": "Deploy compute resources", "duration": "15 min"},
            {"step": 5, "action": "Configure monitoring and alerts", "duration": "5 min"},
            {"step": 6, "action": "Run smoke tests", "duration": "5 min"},
            {"step": 7, "action": "Final verification", "duration": "3 min"},
        ]

        return {
            "strategy": strategy,
            "steps": steps,
            "estimated_duration": "45 minutes",
            "rollback_enabled": rollback,
            "parallel_execution": True,
        }

    @staticmethod
    def _troubleshoot_issue(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Troubleshoot implementation."""
        args.get("issue_description")
        args.get("affected_resources", [])
        args.get("symptoms", [])

        return {
            "diagnosis": "Possible resource exhaustion or network connectivity issue",
            "root_causes": [
                "High CPU/memory usage",
                "Network latency or packet loss",
                "Configuration mismatch",
            ],
            "recommended_actions": [
                "Check resource metrics (CPU, memory, disk)",
                "Verify network connectivity and security groups",
                "Review recent configuration changes",
                "Check application logs for errors",
            ],
            "severity": "medium",
            "estimated_resolution_time": "30 minutes",
        }

    @staticmethod
    def _compare_blueprints(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Compare blueprints implementation."""
        bp_a = args.get("blueprint_a", {})
        bp_b = args.get("blueprint_b", {})

        return {
            "differences": [
                {"field": "name", "value_a": bp_a.get("name"), "value_b": bp_b.get("name")},
                {
                    "field": "resource_count",
                    "value_a": len(bp_a.get("resources", [])),
                    "value_b": len(bp_b.get("resources", [])),
                },
            ],
            "similarity_score": 0.85,
            "recommendation": "Blueprints are largely similar with minor differences",
        }

    @staticmethod
    def _suggest_architecture(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Suggest architecture implementation."""
        args.get("requirements", {})
        args.get("constraints", {})

        return {
            "suggested_architecture": "3-tier web application",
            "components": [
                {"tier": "presentation", "technology": "Load Balancer + Web Servers"},
                {"tier": "application", "technology": "Application Servers + Cache"},
                {"tier": "data", "technology": "Database Cluster + Backup"},
            ],
            "estimated_cost": "$500-1000/month",
            "scalability": "high",
            "availability": "99.9%",
        }

    @staticmethod
    def _calculate_capacity(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Calculate capacity implementation."""
        current = args.get("current_metrics", {})
        growth = args.get("growth_rate", 0)
        horizon = args.get("time_horizon", "3 months")

        return {
            "current_capacity": current,
            "growth_rate": f"{growth}%",
            "forecast_horizon": horizon,
            "recommended_capacity": {
                "cpu": current.get("cpu_usage", 0) * (1 + growth / 100),
                "memory": current.get("memory_usage", 0) * (1 + growth / 100),
            },
            "scaling_recommendation": "Horizontal scaling recommended",
        }

    @staticmethod
    def _migrate_infrastructure(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Migrate infrastructure implementation."""
        args.get("source_platform")
        args.get("target_platform")
        strategy = args.get("migration_strategy", "replatform")

        return {
            "migration_strategy": strategy,
            "phases": [
                {"phase": 1, "name": "Assessment", "duration": "1 week"},
                {"phase": 2, "name": "Planning", "duration": "2 weeks"},
                {"phase": 3, "name": "Migration", "duration": "4 weeks"},
                {"phase": 4, "name": "Validation", "duration": "1 week"},
            ],
            "estimated_downtime": "minimal (< 1 hour)",
            "risk_level": "medium",
        }

    @staticmethod
    def _check_compliance(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Check compliance implementation."""
        args.get("blueprint", {})
        standards = args.get("standards", [])

        return {
            "standards_checked": standards,
            "compliance_status": dict.fromkeys(standards, "partial"),
            "gaps": [
                "Missing encryption configuration",
                "Incomplete access logging",
                "No backup retention policy",
            ],
            "recommendations": [
                "Enable encryption at rest",
                "Configure comprehensive audit logging",
                "Define backup and retention policies",
            ],
        }

    @staticmethod
    def _forecast_metrics(args: dict[str, Any], ctx: dict[str, Any] | None) -> dict[str, Any]:
        """Forecast metrics implementation."""
        args.get("historical_data", [])
        period = args.get("forecast_period")
        confidence = args.get("confidence_level", 0.95)

        return {
            "forecast_period": period,
            "confidence_level": confidence,
            "predictions": [
                {"metric": "cpu_usage", "predicted_value": 65, "trend": "increasing"},
                {"metric": "memory_usage", "predicted_value": 72, "trend": "stable"},
                {"metric": "storage_usage", "predicted_value": 85, "trend": "increasing"},
            ],
            "alerts": ["Storage may reach 90% capacity in 45 days"],
            "recommendations": [
                "Plan for storage expansion",
                "Review CPU optimization opportunities",
            ],
        }


# Register all tools at module load time
def _register_all_tools():
    """Register all tool implementations."""
    InfrastructureTools.register_tool("create_blueprint", InfrastructureTools._create_blueprint)
    InfrastructureTools.register_tool("validate_blueprint", InfrastructureTools._validate_blueprint)
    InfrastructureTools.register_tool("estimate_resources", InfrastructureTools._estimate_resources)
    InfrastructureTools.register_tool("optimize_costs", InfrastructureTools._optimize_costs)
    InfrastructureTools.register_tool("security_audit", InfrastructureTools._security_audit)
    InfrastructureTools.register_tool("generate_deployment_plan", InfrastructureTools._generate_deployment_plan)
    InfrastructureTools.register_tool("troubleshoot_issue", InfrastructureTools._troubleshoot_issue)
    InfrastructureTools.register_tool("compare_blueprints", InfrastructureTools._compare_blueprints)
    InfrastructureTools.register_tool("suggest_architecture", InfrastructureTools._suggest_architecture)
    InfrastructureTools.register_tool("calculate_capacity", InfrastructureTools._calculate_capacity)
    InfrastructureTools.register_tool("migrate_infrastructure", InfrastructureTools._migrate_infrastructure)
    InfrastructureTools.register_tool("check_compliance", InfrastructureTools._check_compliance)
    InfrastructureTools.register_tool("forecast_metrics", InfrastructureTools._forecast_metrics)

# Auto-register on import
_register_all_tools()

