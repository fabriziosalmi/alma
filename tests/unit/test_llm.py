"""Unit tests for LLM integration."""

import pytest

from alma.core.llm import ConversationalOrchestrator, MockLLM


@pytest.fixture
def orchestrator() -> ConversationalOrchestrator:
    """Create ConversationalOrchestrator instance."""
    return ConversationalOrchestrator(llm=MockLLM())


class TestConversationalOrchestrator:
    """Tests for ConversationalOrchestrator class."""

    def test_initialization(self, orchestrator: ConversationalOrchestrator) -> None:
        """Test orchestrator initialization."""
        assert orchestrator.llm is not None
        assert len(orchestrator.conversation_history) == 0

    def test_add_to_history(self, orchestrator: ConversationalOrchestrator) -> None:
        """Test adding messages to history."""
        orchestrator.add_to_history("user", "Hello")
        orchestrator.add_to_history("assistant", "Hi there")

        assert len(orchestrator.conversation_history) == 2
        assert orchestrator.conversation_history[0]["role"] == "user"
        assert orchestrator.conversation_history[1]["role"] == "assistant"

    async def test_parse_intent_create_blueprint(
        self, orchestrator: ConversationalOrchestrator
    ) -> None:
        """Test parsing create blueprint intent."""
        intent = await orchestrator.parse_intent("Create a web server with database")

        assert intent["intent"] == "create_blueprint"
        assert intent["confidence"] > 0
        assert "create" in intent["raw_input"].lower()

    async def test_parse_intent_list_blueprints(
        self, orchestrator: ConversationalOrchestrator
    ) -> None:
        """Test parsing list blueprints intent."""
        intent = await orchestrator.parse_intent("Show me all blueprints")

        assert intent["intent"] == "list_blueprints"
        assert intent["confidence"] > 0

    async def test_parse_intent_deploy(self, orchestrator: ConversationalOrchestrator) -> None:
        """Test parsing deploy intent."""
        intent = await orchestrator.parse_intent("Deploy the infrastructure")

        assert intent["intent"] == "deploy"
        assert intent["confidence"] > 0

    async def test_parse_intent_status(self, orchestrator: ConversationalOrchestrator) -> None:
        """Test parsing status intent."""
        intent = await orchestrator.parse_intent("Check the status of my infrastructure")

        assert intent["intent"] == "status"
        assert intent["confidence"] > 0

    async def test_parse_intent_rollback(self, orchestrator: ConversationalOrchestrator) -> None:
        """Test parsing rollback intent."""
        intent = await orchestrator.parse_intent("Rollback the last deployment")

        assert intent["intent"] == "rollback"
        assert intent["confidence"] > 0

    async def test_natural_language_to_blueprint_web_server(
        self, orchestrator: ConversationalOrchestrator
    ) -> None:
        """Test converting web server description to blueprint."""
        description = "I need a web server"
        blueprint = await orchestrator.natural_language_to_blueprint(description)

        assert blueprint["version"] == "1.0"
        assert len(blueprint["resources"]) > 0
        assert any(r["name"] == "web-server" for r in blueprint["resources"])

    async def test_natural_language_to_blueprint_database(
        self, orchestrator: ConversationalOrchestrator
    ) -> None:
        """Test converting database description to blueprint."""
        description = "Setup a database server"
        blueprint = await orchestrator.natural_language_to_blueprint(description)

        assert any(r["name"] == "database-server" for r in blueprint["resources"])

    async def test_natural_language_to_blueprint_with_load_balancer(
        self, orchestrator: ConversationalOrchestrator
    ) -> None:
        """Test converting description with load balancer."""
        description = "Create a web application with load balancer and database"
        blueprint = await orchestrator.natural_language_to_blueprint(description)

        resources = blueprint["resources"]
        assert len(resources) >= 3  # web, db, lb
        assert any(r["type"] == "network" for r in resources)
        assert any("web" in r["name"] for r in resources)
        assert any("database" in r["name"] for r in resources)

    async def test_blueprint_to_natural_language(
        self, orchestrator: ConversationalOrchestrator
    ) -> None:
        """Test converting blueprint to natural language."""
        blueprint = {
            "name": "test-app",
            "resources": [
                {
                    "type": "compute",
                    "name": "web-server",
                    "specs": {"cpu": 2, "memory": "4GB"},
                },
                {
                    "type": "network",
                    "name": "load-balancer",
                    "specs": {"type": "http"},
                },
            ],
        }

        description = await orchestrator.blueprint_to_natural_language(blueprint)

        assert "test-app" in description
        assert "web-server" in description
        assert "2 CPU" in description
        assert "4GB" in description
        assert "load-balancer" in description

    async def test_suggest_improvements_single_server(
        self, orchestrator: ConversationalOrchestrator
    ) -> None:
        """Test suggesting improvements for single server setup."""
        blueprint = {
            "name": "single-server",
            "resources": [
                {
                    "type": "compute",
                    "name": "app-server",
                    "specs": {"cpu": 2, "memory": "4GB"},
                    "metadata": {},
                }
            ],
        }

        suggestions = await orchestrator.suggest_improvements(blueprint)

        assert len(suggestions) > 0
        assert any("redundant" in s.lower() or "availability" in s.lower() for s in suggestions)

    async def test_suggest_improvements_no_backup(
        self, orchestrator: ConversationalOrchestrator
    ) -> None:
        """Test suggesting backup storage."""
        blueprint = {
            "name": "app-without-backup",
            "resources": [
                {
                    "type": "compute",
                    "name": "server-1",
                    "specs": {"cpu": 2, "memory": "4GB"},
                    "metadata": {},
                }
            ],
        }

        suggestions = await orchestrator.suggest_improvements(blueprint)

        assert any("backup" in s.lower() for s in suggestions)

    async def test_suggest_improvements_under_provisioned(
        self, orchestrator: ConversationalOrchestrator
    ) -> None:
        """Test detecting under-provisioned resources."""
        blueprint = {
            "name": "small-resources",
            "resources": [
                {
                    "type": "compute",
                    "name": "tiny-server",
                    "specs": {"cpu": 1, "memory": "512MB"},
                    "metadata": {},
                }
            ],
        }

        suggestions = await orchestrator.suggest_improvements(blueprint)

        assert any("under-provisioned" in s.lower() or "memory" in s.lower() for s in suggestions)

    async def test_suggest_improvements_well_configured(
        self, orchestrator: ConversationalOrchestrator
    ) -> None:
        """Test well-configured blueprint."""
        blueprint = {
            "name": "well-configured",
            "resources": [
                {
                    "type": "compute",
                    "name": "server-1",
                    "specs": {"cpu": 4, "memory": "8GB"},
                    "metadata": {},
                },
                {
                    "type": "compute",
                    "name": "server-2",
                    "specs": {"cpu": 4, "memory": "8GB"},
                    "metadata": {},
                },
                {
                    "type": "network",
                    "name": "load-balancer",
                    "specs": {},
                    "metadata": {},
                },
                {
                    "type": "storage",
                    "name": "backup-storage",
                    "specs": {},
                    "metadata": {"purpose": "backup"},
                },
            ],
        }

        suggestions = await orchestrator.suggest_improvements(blueprint)

        # Should have minimal or positive suggestions
        assert len(suggestions) > 0
        assert any("well-configured" in s.lower() or "looks" in s.lower() for s in suggestions)

    def test_clear_history(self, orchestrator: ConversationalOrchestrator) -> None:
        """Test clearing conversation history."""
        orchestrator.add_to_history("user", "Hello")
        orchestrator.add_to_history("assistant", "Hi")

        assert len(orchestrator.conversation_history) == 2

        orchestrator.clear_history()

        assert len(orchestrator.conversation_history) == 0


class TestMockLLM:
    """Tests for MockLLM implementation."""

    async def test_generate(self) -> None:
        """Test generate method."""
        llm = MockLLM()
        response = await llm.generate("Test prompt")

        assert isinstance(response, str)
        assert "Test prompt" in response

    async def test_function_call(self) -> None:
        """Test function call method."""
        llm = MockLLM()
        functions = [{"name": "test_function", "parameters": {}}]
        result = await llm.function_call("Test prompt", functions)

        assert isinstance(result, dict)
        assert "function" in result
        assert result["function"] == "test_function"

    async def test_function_call_no_functions(self) -> None:
        """Test function call with no functions."""
        llm = MockLLM()
        result = await llm.function_call("Test prompt", [])

        assert isinstance(result, dict)
        assert result == {}
