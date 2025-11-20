"""Tests for enhanced function calling tools."""

import pytest
from alma.core.tools import InfrastructureTools


def test_get_available_tools():
    """Test getting list of available tools."""
    tools_list = InfrastructureTools.get_available_tools()

    assert isinstance(tools_list, list)
    assert len(tools_list) > 0

    # Check first tool has required fields
    tool = tools_list[0]
    assert "name" in tool
    assert "description" in tool
    assert "parameters" in tool


def test_create_blueprint_tool():
    """Test blueprint creation tool."""
    args = {
        "name": "test-blueprint",
        "description": "Test infrastructure",
        "resources": [
            {
                "type": "compute",
                "name": "web-server",
                "provider": "fake",
                "specs": {"cpu": 2, "memory": "4GB"},
            }
        ],
    }

    result = InfrastructureTools.execute_tool("create_blueprint", args)

    assert result["success"] is True
    assert "blueprint" in result["result"]
    assert result["result"]["blueprint"]["name"] == "test-blueprint"


def test_validate_blueprint_tool():
    """Test blueprint validation tool."""
    valid_blueprint = {
        "version": "1.0",
        "name": "test-bp",
        "resources": [{"type": "compute", "name": "server1"}],
    }

    result = InfrastructureTools.execute_tool(
        "validate_blueprint", {"blueprint": valid_blueprint, "strict": False}
    )

    assert result["success"] is True
    assert result["result"]["valid"] is True


def test_validate_blueprint_invalid():
    """Test validation with invalid blueprint."""
    invalid_blueprint = {"resources": []}  # Missing version and name

    result = InfrastructureTools.execute_tool(
        "validate_blueprint", {"blueprint": invalid_blueprint}
    )

    assert result["success"] is True
    assert result["result"]["valid"] is False
    assert len(result["result"]["issues"]) > 0


def test_estimate_resources_tool():
    """Test resource estimation tool."""
    args = {"workload_type": "web", "expected_load": "1000 requests/sec", "availability": "high"}

    result = InfrastructureTools.execute_tool("estimate_resources", args)

    assert result["success"] is True
    assert "recommended_specs" in result["result"]
    assert "recommended_instances" in result["result"]
    assert result["result"]["recommended_instances"] == 3  # High availability


def test_optimize_costs_tool():
    """Test cost optimization tool."""
    blueprint = {"version": "1.0", "name": "expensive-infra", "resources": []}

    args = {"blueprint": blueprint, "provider": "aws", "optimization_goal": "cost"}

    result = InfrastructureTools.execute_tool("optimize_costs", args)

    assert result["success"] is True
    assert "suggestions" in result["result"]
    assert len(result["result"]["suggestions"]) > 0


def test_security_audit_tool():
    """Test security audit tool."""
    blueprint = {
        "version": "1.0",
        "name": "test-infra",
        "resources": [{"type": "compute", "name": "server1"}],
    }

    args = {"blueprint": blueprint, "compliance_framework": "general"}

    result = InfrastructureTools.execute_tool("security_audit", args)

    assert result["success"] is True
    assert "findings" in result["result"]
    assert isinstance(result["result"]["findings"], list)


def test_deployment_plan_tool():
    """Test deployment plan generation."""
    blueprint = {"version": "1.0", "name": "test-deploy", "resources": []}

    args = {"blueprint": blueprint, "strategy": "rolling"}

    result = InfrastructureTools.execute_tool("generate_deployment_plan", args)

    assert result["success"] is True
    assert "steps" in result["result"]
    assert result["result"]["strategy"] == "rolling"


def test_troubleshoot_tool():
    """Test troubleshooting tool."""
    args = {"issue_description": "Application is slow", "symptoms": ["high latency", "timeouts"]}

    result = InfrastructureTools.execute_tool("troubleshoot_issue", args)

    assert result["success"] is True
    assert "diagnosis" in result["result"]
    assert "recommended_actions" in result["result"]


def test_compare_blueprints_tool():
    """Test blueprint comparison."""
    bp_a = {
        "version": "1.0",
        "name": "blueprint-a",
        "resources": [{"type": "compute", "name": "server1"}],
    }

    bp_b = {
        "version": "1.0",
        "name": "blueprint-b",
        "resources": [
            {"type": "compute", "name": "server1"},
            {"type": "compute", "name": "server2"},
        ],
    }

    args = {"blueprint_a": bp_a, "blueprint_b": bp_b}

    result = InfrastructureTools.execute_tool("compare_blueprints", args)

    assert result["success"] is True
    assert "differences" in result["result"]
    assert "similarity_score" in result["result"]


def test_suggest_architecture_tool():
    """Test architecture suggestion."""
    args = {
        "requirements": {
            "application_type": "e-commerce",
            "expected_users": 10000,
            "data_size": "100GB",
        }
    }

    result = InfrastructureTools.execute_tool("suggest_architecture", args)

    assert result["success"] is True
    assert "suggested_architecture" in result["result"]
    assert "components" in result["result"]


def test_calculate_capacity_tool():
    """Test capacity calculation."""
    args = {
        "current_metrics": {"cpu_usage": 60, "memory_usage": 70},
        "growth_rate": 20,
        "time_horizon": "3 months",
    }

    result = InfrastructureTools.execute_tool("calculate_capacity", args)

    assert result["success"] is True
    assert "recommended_capacity" in result["result"]


def test_migration_plan_tool():
    """Test migration planning."""
    blueprint = {"version": "1.0", "name": "current-infra", "resources": []}

    args = {
        "source_platform": "aws",
        "target_platform": "gcp",
        "blueprint": blueprint,
        "migration_strategy": "replatform",
    }

    result = InfrastructureTools.execute_tool("migrate_infrastructure", args)

    assert result["success"] is True
    assert "phases" in result["result"]
    assert result["result"]["migration_strategy"] == "replatform"


def test_compliance_check_tool():
    """Test compliance checking."""
    blueprint = {"version": "1.0", "name": "prod-infra", "resources": []}

    args = {"blueprint": blueprint, "standards": ["pci-dss", "gdpr"]}

    result = InfrastructureTools.execute_tool("check_compliance", args)

    assert result["success"] is True
    assert "compliance_status" in result["result"]
    assert "gaps" in result["result"]


def test_forecast_metrics_tool():
    """Test metrics forecasting."""
    args = {
        "historical_data": [
            {"timestamp": "2024-01-01", "metrics": {"cpu": 50}},
            {"timestamp": "2024-01-02", "metrics": {"cpu": 55}},
        ],
        "forecast_period": "30 days",
    }

    result = InfrastructureTools.execute_tool("forecast_metrics", args)

    assert result["success"] is True
    assert "predictions" in result["result"]
    assert "recommendations" in result["result"]


def test_unknown_tool():
    """Test handling of unknown tool."""
    result = InfrastructureTools.execute_tool("nonexistent_tool", {})

    assert result["success"] is False
    assert "error" in result
    assert "available_tools" in result


def test_tool_execution_error():
    """Test handling of tool execution errors."""
    # This should cause an error due to missing required args
    result = InfrastructureTools.execute_tool("create_blueprint", {})

    # Should still return a structured response
    assert "success" in result
    assert "tool" in result


@pytest.mark.asyncio
async def test_orchestrator_integration():
    """Test integration with orchestrator."""
    from alma.core.llm_orchestrator import EnhancedOrchestrator
    from alma.core.llm import MockLLM

    llm = MockLLM()
    orchestrator = EnhancedOrchestrator(llm=llm, use_llm=True)

    # Get available tools
    tools = orchestrator.get_available_tools()

    assert len(tools) > 0
    assert all("name" in tool for tool in tools)
