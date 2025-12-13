"""Unit tests for Infrastructure Tools."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from alma.core.tools import InfrastructureTools

class TestInfrastructureTools:

    def setup_method(self):
        """Reset registry before each test to ensure isolation."""
        # Clean registry if needed, though mostly we test static methods
        pass

    def test_registry(self):
        """Test tool registration."""
        def dummy_tool(args, ctx):
            return "dummy"
        
        InfrastructureTools.register_tool("test_dummy", dummy_tool)
        assert "test_dummy" in InfrastructureTools.get_registered_tools()
        assert InfrastructureTools._TOOL_REGISTRY["test_dummy"] == dummy_tool

    @pytest.mark.asyncio
    async def test_execute_tool_success_sync(self):
        """Test executing a synchronous tool."""
        def sync_tool(args, ctx):
            return {"status": "ok", "arg": args.get("val")}
        
        InfrastructureTools.register_tool("sync_test", sync_tool)
        
        response = await InfrastructureTools.execute_tool("sync_test", {"val": 123})
        
        assert response.success is True
        assert response.result["arg"] == 123
        assert response.error is None

    @pytest.mark.asyncio
    async def test_execute_tool_success_async(self):
        """Test executing an asynchronous tool."""
        async def async_tool(args, ctx):
            return {"status": "async_ok"}
        
        InfrastructureTools.register_tool("async_test", async_tool)
        
        response = await InfrastructureTools.execute_tool("async_test", {})
        
        assert response.success is True
        assert response.result["status"] == "async_ok"

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        """Test executing a non-existent tool."""
        response = await InfrastructureTools.execute_tool("non_existent", {})
        
        assert response.success is False
        assert "Unknown tool" in response.error

    @pytest.mark.asyncio
    async def test_execute_tool_validation_error(self):
        """Test tool raising ValueError."""
        def fail_tool(args, ctx):
            raise ValueError("Invalid arg")
        
        InfrastructureTools.register_tool("fail_test", fail_tool)
        
        response = await InfrastructureTools.execute_tool("fail_test", {})
        
        assert response.success is False
        assert "Validation error" in response.error
        assert "Invalid arg" in response.error

    @pytest.mark.asyncio
    async def test_execute_tool_unexpected_error(self):
        """Test tool raising unexpected exception."""
        def crash_tool(args, ctx):
            raise RuntimeError("Crash")
        
        InfrastructureTools.register_tool("crash_test", crash_tool)
        
        response = await InfrastructureTools.execute_tool("crash_test", {})
        
        assert response.success is False
        assert "Execution error" in response.error
        assert "Crash" in response.error

    # --- Individual Tool Tests ---

    def test_create_blueprint_tool(self):
        """Test _create_blueprint logic."""
        args = {
            "name": "test-bp",
            "description": "desc",
            "resources": [{"name": "vm1", "type": "compute"}]
        }
        result = InfrastructureTools._create_blueprint(args, None)
        
        assert result["blueprint"]["name"] == "test-bp"
        assert len(result["blueprint"]["resources"]) == 1

    def test_validate_blueprint_tool(self):
        """Test _validate_blueprint logic."""
        # Valid
        args = {"blueprint": {"version": "1.0", "name": "ok", "resources": [{"name": "r1", "type": "c"}]}}
        res = InfrastructureTools._validate_blueprint(args, None)
        assert res["valid"] is True

        # Invalid
        args_bad = {"blueprint": {"name": "no-version"}} # Missing version
        res_bad = InfrastructureTools._validate_blueprint(args_bad, None)
        assert res_bad["valid"] is False
        assert "Missing 'version' field" in res_bad["issues"]

    @pytest.mark.asyncio
    async def test_estimate_resources_tool(self):
        """Test _estimate_resources with pricing fallback/mock."""
        args = {
            "workload_type": "web",
            "expected_load": "100 users", # Schema expects str
            "availability": "high"
        }
        
        # Mock PricingService to avoid integration issues
        with patch("alma.integrations.pricing.PricingService") as MockPricing:
            mock_instance = MockPricing.return_value
            mock_instance.estimate_cost = AsyncMock(return_value={"monthly_usd": 50})
            
            result = await InfrastructureTools._estimate_resources(args, None)
            
            assert result["workload_type"] == "web"
            assert result["recommended_instances"] == 3 # High availability
            # 50 * 3 = 150
            assert result["estimated_monthly_cost"] == 150

    def test_optimize_costs_tool(self):
        args = {
            "provider": "aws",
            "optimization_goal": "reduce_spend"
        }
        res = InfrastructureTools._optimize_costs(args, None)
        assert res["estimated_savings"] == "30-50%"

    def test_security_audit_tool(self):
        args = {"compliance_framework": "cis"}
        res = InfrastructureTools._security_audit(args, None)
        assert res["compliant"] is False
        assert len(res["findings"]) > 0

    def test_troubleshoot_issue_tool(self):
        args = {"issue_description": "slow", "affected_resources": ["vm-1"]}
        res = InfrastructureTools._troubleshoot_issue(args, None)
        assert "CPU/memory usage" in res["root_causes"][0]

    def test_compare_blueprints_tool(self):
        args = {
            "blueprint_a": {"name": "A", "resources": []},
            "blueprint_b": {"name": "B", "resources": [1]}
        }
        res = InfrastructureTools._compare_blueprints(args, None)
        assert res["similarity_score"] == 0.85

    def test_suggest_architecture_tool(self):
        args = {"requirements": {"type": "web app"}} # Schema expects dict
        res = InfrastructureTools._suggest_architecture(args, None)
        assert "3-tier" in res["suggested_architecture"]

    def test_calculate_capacity_tool(self):
        args = {
            "current_metrics": {"cpu_usage": 50, "memory_usage": 100},
            "growth_rate": 10,
            "time_horizon": "6 months"
        }
        res = InfrastructureTools._calculate_capacity(args, None)
        # 50 * 1.1 = 55.0. Use approx for safety
        assert res["recommended_capacity"]["cpu"] == pytest.approx(55.0)

    def test_migrate_infrastructure_tool(self):
        args = {"source_platform": "onprem", "target_platform": "cloud"}
        res = InfrastructureTools._migrate_infrastructure(args, None)
        assert len(res["phases"]) == 4

    def test_check_compliance_tool(self):
        args = {"blueprint": {"id": "vm-1"}, "standards": ["pci"]}
        res = InfrastructureTools._check_compliance(args, None)
        assert res["compliance_status"]["pci"] == "partial"

    def test_forecast_metrics_tool(self):
        args = {
            "historical_data": [{"val": 10}], 
            "forecast_period": "30 days"
        }
        res = InfrastructureTools._forecast_metrics(args, None)
        assert res["predictions"][0]["metric"] == "cpu_usage"
