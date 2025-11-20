"""LLM integration for conversational infrastructure management."""

from typing import Any, Dict, List, Optional
import json
from abc import ABC, abstractmethod


class LLMInterface(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: Input prompt
            context: Optional context information

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    async def function_call(self, prompt: str, functions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate function call from prompt.

        Args:
            prompt: Input prompt
            functions: Available functions

        Returns:
            Function call result
        """
        pass

    async def stream_generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Stream text generation from prompt (optional, falls back to generate).

        Args:
            prompt: Input prompt
            context: Optional context information

        Yields:
            Text chunks
        """
        # Default implementation: return full response
        response = await self.generate(prompt, context)
        yield response


class ConversationalOrchestrator:
    """
    Orchestrator for conversational infrastructure management.

    Translates natural language requests into infrastructure blueprints
    and operations.
    """

    def __init__(self, llm: Optional[LLMInterface] = None) -> None:
        """
        Initialize orchestrator.

        Args:
            llm: LLM interface instance
        """
        self.llm = llm
        self.conversation_history: List[Dict[str, str]] = []

    def add_to_history(self, role: str, content: str) -> None:
        """
        Add message to conversation history.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
        """
        self.conversation_history.append({"role": role, "content": content})

    async def parse_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user intent from natural language.

        Args:
            user_input: User's natural language input

        Returns:
            Parsed intent with action and parameters
        """
        # Add to history
        self.add_to_history("user", user_input)

        # Define available intents
        intents = {
            "create_blueprint": {
                "keywords": ["create", "deploy", "setup", "provision", "build"],
                "entities": ["server", "vm", "database", "network", "storage"],
            },
            "list_blueprints": {
                "keywords": ["list", "show", "display", "get"],
                "entities": ["blueprint", "infrastructure", "resources"],
            },
            "deploy": {
                "keywords": ["deploy", "launch", "start", "run"],
                "entities": ["blueprint", "infrastructure"],
            },
            "status": {
                "keywords": ["status", "state", "health", "check"],
                "entities": ["infrastructure", "resource", "deployment"],
            },
            "rollback": {
                "keywords": ["rollback", "revert", "undo"],
                "entities": ["deployment", "infrastructure"],
            },
        }

        # Simple keyword-based intent detection
        user_input_lower = user_input.lower()
        detected_intent = "unknown"
        confidence = 0.0

        for intent, patterns in intents.items():
            keyword_matches = sum(
                1 for keyword in patterns["keywords"] if keyword in user_input_lower
            )
            entity_matches = sum(1 for entity in patterns["entities"] if entity in user_input_lower)

            total_matches = keyword_matches + entity_matches
            if total_matches > confidence:
                confidence = total_matches
                detected_intent = intent

        return {
            "intent": detected_intent,
            "confidence": confidence,
            "raw_input": user_input,
        }

    async def natural_language_to_blueprint(self, description: str) -> Dict[str, Any]:
        """
        Convert natural language description to blueprint.

        Args:
            description: Natural language infrastructure description

        Returns:
            System blueprint
        """
        # Simple rule-based conversion for demonstration
        # In production, this would use the LLM

        blueprint = {
            "version": "1.0",
            "name": "ai-generated-blueprint",
            "description": description,
            "resources": [],
            "metadata": {"generated_by": "ALMA-llm"},
        }

        # Extract resource requirements from description
        description_lower = description.lower()

        # Check for web server
        if "web" in description_lower or "http" in description_lower:
            blueprint["resources"].append(
                {
                    "type": "compute",
                    "name": "web-server",
                    "provider": "fake",
                    "specs": {"cpu": 2, "memory": "4GB", "storage": "50GB"},
                    "dependencies": [],
                    "metadata": {"role": "web"},
                }
            )

        # Check for database
        if "database" in description_lower or "db" in description_lower:
            blueprint["resources"].append(
                {
                    "type": "compute",
                    "name": "database-server",
                    "provider": "fake",
                    "specs": {"cpu": 4, "memory": "8GB", "storage": "200GB"},
                    "dependencies": [],
                    "metadata": {"role": "database"},
                }
            )

        # Check for load balancer
        if "load balancer" in description_lower or "lb" in description_lower:
            backend_servers = [r["name"] for r in blueprint["resources"] if r["type"] == "compute"]
            blueprint["resources"].append(
                {
                    "type": "network",
                    "name": "load-balancer",
                    "provider": "fake",
                    "specs": {"type": "http", "backends": backend_servers},
                    "dependencies": backend_servers,
                    "metadata": {},
                }
            )

        return blueprint

    async def blueprint_to_natural_language(self, blueprint: Dict[str, Any]) -> str:
        """
        Convert blueprint to natural language description.

        Args:
            blueprint: System blueprint

        Returns:
            Natural language description
        """
        name = blueprint.get("name", "unnamed")
        resources = blueprint.get("resources", [])

        description_parts = [f"This infrastructure '{name}' consists of:"]

        for resource in resources:
            resource_type = resource.get("type", "unknown")
            resource_name = resource.get("name", "unnamed")
            specs = resource.get("specs", {})

            if resource_type == "compute":
                cpu = specs.get("cpu", "?")
                memory = specs.get("memory", "?")
                description_parts.append(
                    f"- A {resource_name} server with {cpu} CPU cores and {memory} of memory"
                )
            elif resource_type == "network":
                lb_type = specs.get("type", "?")
                description_parts.append(f"- A {lb_type} load balancer named {resource_name}")
            elif resource_type == "storage":
                size = specs.get("size", "?")
                description_parts.append(f"- Storage volume {resource_name} with {size} capacity")
            else:
                description_parts.append(f"- A {resource_type} resource named {resource_name}")

        return "\n".join(description_parts)

    async def suggest_improvements(self, blueprint: Dict[str, Any]) -> List[str]:
        """
        Suggest improvements to a blueprint.

        Args:
            blueprint: System blueprint

        Returns:
            List of improvement suggestions
        """
        suggestions = []
        resources = blueprint.get("resources", [])

        # Check for high availability
        compute_resources = [r for r in resources if r.get("type") == "compute"]
        if len(compute_resources) == 1:
            suggestions.append(
                "Consider adding redundant servers for high availability (minimum 2 instances)"
            )

        # Check for load balancer
        has_lb = any(r.get("type") == "network" for r in resources)
        if len(compute_resources) > 1 and not has_lb:
            suggestions.append("Add a load balancer to distribute traffic across servers")

        # Check for backup storage
        has_backup = any(
            "backup" in r.get("metadata", {}).get("purpose", "").lower() for r in resources
        )
        if not has_backup:
            suggestions.append("Add backup storage for disaster recovery")

        # Check resource specs
        for resource in compute_resources:
            specs = resource.get("specs", {})
            cpu = specs.get("cpu", 0)
            memory = specs.get("memory", "0MB")

            # Convert memory to MB for comparison
            memory_mb = 0
            if isinstance(memory, str):
                memory_upper = memory.upper()
                if "GB" in memory_upper:
                    memory_mb = int(float(memory_upper.replace("GB", "")) * 1024)
                elif "MB" in memory_upper:
                    memory_mb = int(memory_upper.replace("MB", ""))

            # Check for under-provisioned resources
            if cpu < 2:
                suggestions.append(
                    f"Resource '{resource.get('name')}' may be under-provisioned (CPU < 2)"
                )
            if memory_mb < 2048:
                suggestions.append(
                    f"Resource '{resource.get('name')}' may need more memory (< 2GB)"
                )

        if not suggestions:
            suggestions.append("Blueprint looks well-configured!")

        return suggestions

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []


# Mock LLM implementation for development
class MockLLM(LLMInterface):
    """Mock LLM implementation for testing."""

    async def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate mock response."""
        return f"Mock response to: {prompt}"

    async def function_call(self, prompt: str, functions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate mock function call."""
        if functions:
            return {
                "function": functions[0]["name"],
                "arguments": {},
            }
        return {}
