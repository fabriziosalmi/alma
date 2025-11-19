"""Tests for prompt templates."""

from alma.core.prompts import InfrastructurePrompts


class TestInfrastructurePrompts:
    """Tests for infrastructure prompt templates."""

    def test_blueprint_generation(self) -> None:
        """Test blueprint generation prompt."""
        prompt = InfrastructurePrompts.blueprint_generation("Create a web server")
        
        assert "Create a web server" in prompt
        assert "infrastructure blueprint" in prompt.lower()

    def test_blueprint_description(self) -> None:
        """Test blueprint description prompt."""
        blueprint = {"name": "test", "resources": []}
        prompt = InfrastructurePrompts.blueprint_description(blueprint)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_improvement_suggestions(self) -> None:
        """Test improvement suggestions prompt."""
        blueprint = {"name": "test", "resources": [{"type": "compute"}]}
        prompt = InfrastructurePrompts.improvement_suggestions(blueprint)
        
        assert "improve" in prompt.lower() or "suggest" in prompt.lower()

    def test_resource_sizing(self) -> None:
        """Test resource sizing prompt."""
        prompt = InfrastructurePrompts.resource_sizing("web app", "1000 users")
        
        assert "web app" in prompt
        assert "1000 users" in prompt

    def test_troubleshooting(self) -> None:
        """Test troubleshooting prompt."""
        issue = "High CPU usage"
        context = {"server": "web-1"}
        prompt = InfrastructurePrompts.troubleshooting(issue, context)
        
        assert "High CPU usage" in prompt

    def test_security_audit(self) -> None:
        """Test security audit prompt."""
        blueprint = {"name": "test", "resources": []}
        prompt = InfrastructurePrompts.security_audit(blueprint)
        
        assert "security" in prompt.lower()

    def test_cost_estimation(self) -> None:
        """Test cost estimation prompt."""
        blueprint = {"name": "test", "resources": []}
        prompt = InfrastructurePrompts.cost_estimation(blueprint, "aws")
        
        assert "cost" in prompt.lower()
        assert "aws" in prompt.lower()

    def test_migration_plan(self) -> None:
        """Test migration plan prompt."""
        blueprint = {"name": "test", "resources": []}
        prompt = InfrastructurePrompts.migration_plan("aws", "gcp", blueprint)
        
        assert "aws" in prompt.lower()
        assert "gcp" in prompt.lower()
        assert "migration" in prompt.lower()

    def test_intent_classification(self) -> None:
        """Test intent classification prompt."""
        prompt = InfrastructurePrompts.intent_classification("Deploy a database")
        
        assert "Deploy a database" in prompt
