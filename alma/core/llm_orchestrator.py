"""Enhanced conversational orchestrator with real LLM integration."""

import json
import re
from typing import Any

import yaml

from alma.core.llm import ConversationalOrchestrator, LLMInterface
from alma.core.prompts import InfrastructurePrompts
from alma.core.tools import InfrastructureTools


class EnhancedOrchestrator(ConversationalOrchestrator):
    """
    Enhanced orchestrator with real LLM support.

    Extends the base orchestrator with actual LLM capabilities
    using Qwen3 or other LLM providers.
    """

    def __init__(self, llm: LLMInterface | None = None, use_llm: bool = True) -> None:
        """
        Initialize enhanced orchestrator.

        Args:
            llm: LLM interface instance
            use_llm: Whether to use real LLM (False falls back to rule-based)
        """
        super().__init__(llm)
        self.use_llm = use_llm and llm is not None
        self.tools = InfrastructureTools()

    async def execute_function_call(
        self, user_input: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute function call based on user input using LLM.

        Args:
            user_input: User's request
            context: Optional context

        Returns:
            Function execution result
        """
        if not self.use_llm or self.llm is None:
            return {"success": False, "error": "LLM not available for function calling"}

        # Get available tools
        available_tools = self.tools.get_available_tools()

        try:
            # Ask LLM to select and call appropriate function
            function_call = await self.llm.function_call(user_input, available_tools)

            if not function_call or "function" not in function_call:
                return {"success": False, "error": "LLM did not return valid function call"}

            # Execute the selected tool
            tool_name = function_call.get("function")
            arguments = function_call.get("arguments", {})

            result = self.tools.execute_tool(tool_name, arguments, context)
            return result

        except Exception as e:
            return {"success": False, "error": f"Function call execution failed: {e}"}

    def get_available_tools(self) -> list[dict[str, Any]]:
        """
        Get list of available tools for function calling.

        Returns:
            List of tool definitions
        """
        return self.tools.get_available_tools()

    async def parse_intent_with_llm(self, user_input: str) -> dict[str, Any]:
        """
        Parse user intent using LLM.

        Args:
            user_input: User's natural language input

        Returns:
            Parsed intent with action, confidence, and entities
        """
        if not self.use_llm or self.llm is None:
            # Fallback to rule-based
            return await self.parse_intent(user_input)

        # Use LLM for intent classification
        prompt = InfrastructurePrompts.intent_classification(user_input)

        try:
            response = await self.llm.generate(prompt)

            # Parse JSON response
            intent_data = self._extract_json(response)

            if intent_data:
                return {
                    "intent": intent_data.get("intent", "unknown"),
                    "confidence": intent_data.get("confidence", 0.5),
                    "entities": intent_data.get("entities", {}),
                    "raw_input": user_input,
                    "reasoning": intent_data.get("reasoning", ""),
                }

        except Exception as e:
            print(f"LLM intent parsing failed: {e}, falling back to rules")

        # Fallback
        return await self.parse_intent(user_input)

    async def natural_language_to_blueprint(self, description: str) -> dict[str, Any]:
        """
        Convert natural language description to blueprint using LLM.

        Args:
            description: Natural language infrastructure description

        Returns:
            System blueprint
        """
        if not self.use_llm or self.llm is None:
            # Fallback to rule-based
            return await super().natural_language_to_blueprint(description)

        # Use LLM to generate blueprint
        prompt = InfrastructurePrompts.blueprint_generation(description)

        try:
            response = await self.llm.generate(prompt)

            # Extract YAML from response
            blueprint = self._extract_yaml(response)

            if blueprint:
                # Ensure required fields
                if "version" not in blueprint:
                    blueprint["version"] = "1.0"
                if "name" not in blueprint:
                    blueprint["name"] = "ai-generated-blueprint"
                if "resources" not in blueprint:
                    blueprint["resources"] = []

                blueprint.setdefault("metadata", {})
                blueprint["metadata"]["generated_by"] = "ALMA-llm"
                blueprint["metadata"]["source_description"] = description

                return blueprint

        except Exception as e:
            print(f"LLM blueprint generation failed: {e}, falling back to rules")

        # Fallback to rule-based
        return await super().natural_language_to_blueprint(description)

    async def blueprint_to_natural_language(self, blueprint: dict[str, Any]) -> str:
        """
        Convert blueprint to natural language using LLM.

        Args:
            blueprint: System blueprint

        Returns:
            Natural language description
        """
        if not self.use_llm or self.llm is None:
            # Fallback to rule-based
            return await super().blueprint_to_natural_language(blueprint)

        # Use LLM to describe blueprint
        prompt = InfrastructurePrompts.blueprint_description(blueprint)

        try:
            response = await self.llm.generate(prompt)
            return response.strip()

        except Exception as e:
            print(f"LLM description failed: {e}, falling back to rules")

        # Fallback
        return await super().blueprint_to_natural_language(blueprint)

    async def suggest_improvements(self, blueprint: dict[str, Any]) -> list[str]:
        """
        Suggest improvements using LLM.

        Args:
            blueprint: System blueprint

        Returns:
            List of improvement suggestions
        """
        if not self.use_llm or self.llm is None:
            # Fallback to rule-based
            return await super().suggest_improvements(blueprint)

        # Use LLM for suggestions
        prompt = InfrastructurePrompts.improvement_suggestions(blueprint)

        try:
            response = await self.llm.generate(prompt)

            # Parse numbered list
            suggestions = self._parse_numbered_list(response)

            if suggestions:
                return suggestions

        except Exception as e:
            print(f"LLM suggestions failed: {e}, falling back to rules")

        # Fallback
        return await super().suggest_improvements(blueprint)

    async def estimate_resources(self, workload: str, expected_load: str) -> dict[str, Any]:
        """
        Estimate resource requirements using LLM.

        Args:
            workload: Type of workload
            expected_load: Expected load description

        Returns:
            Resource recommendations
        """
        if not self.use_llm or self.llm is None:
            return {
                "cpu": 2,
                "memory": "4GB",
                "storage": "50GB",
                "storage_type": "SSD",
                "network": "1Gbps",
                "reasoning": "Default recommendations (LLM not available)",
            }

        # Use LLM for sizing
        prompt = InfrastructurePrompts.resource_sizing(workload, expected_load)

        try:
            response = await self.llm.generate(prompt)
            sizing_data = self._extract_json(response)

            if sizing_data:
                return sizing_data

        except Exception as e:
            print(f"LLM resource sizing failed: {e}")

        # Fallback
        return {
            "cpu": 4,
            "memory": "8GB",
            "storage": "100GB",
            "storage_type": "SSD",
            "network": "1Gbps",
            "reasoning": "Conservative default recommendations",
        }

    async def security_audit(self, blueprint: dict[str, Any]) -> list[dict[str, str]]:
        """
        Perform security audit using LLM.

        Args:
            blueprint: Blueprint to audit

        Returns:
            List of security findings
        """
        if not self.use_llm or self.llm is None:
            return [
                {
                    "severity": "info",
                    "issue": "Security audit requires LLM",
                    "recommendation": "Enable LLM for detailed security analysis",
                }
            ]

        prompt = InfrastructurePrompts.security_audit(blueprint)

        try:
            response = await self.llm.generate(prompt)

            # Parse findings (simple text parsing)
            findings = []
            current_finding = {}

            for line in response.split("\n"):
                line = line.strip()
                if not line:
                    if current_finding:
                        findings.append(current_finding)
                        current_finding = {}
                    continue

                if "severity:" in line.lower():
                    current_finding["severity"] = line.split(":", 1)[1].strip()
                elif "issue:" in line.lower() or "description:" in line.lower():
                    current_finding["issue"] = line.split(":", 1)[1].strip()
                elif "recommendation:" in line.lower():
                    current_finding["recommendation"] = line.split(":", 1)[1].strip()

            if current_finding:
                findings.append(current_finding)

            return findings if findings else [{"severity": "info", "issue": "No issues found"}]

        except Exception as e:
            print(f"LLM security audit failed: {e}")
            return [{"severity": "error", "issue": f"Audit failed: {str(e)}"}]

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """
        Extract JSON from text.

        Args:
            text: Text containing JSON

        Returns:
            Parsed JSON or None
        """
        # Try to find JSON in text
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1

        if start_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        return None

    def _extract_yaml(self, text: str) -> dict[str, Any] | None:
        """
        Extract YAML from text.

        Args:
            text: Text containing YAML

        Returns:
            Parsed YAML or None
        """
        # Try to extract from code blocks
        yaml_pattern = r"```(?:yaml)?\n(.*?)\n```"
        matches = re.findall(yaml_pattern, text, re.DOTALL)

        for match in matches:
            try:
                return yaml.safe_load(match)
            except yaml.YAMLError:
                continue

        # Try parsing entire text as YAML
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError:
            pass

        return None

    def _parse_numbered_list(self, text: str) -> list[str]:
        """
        Parse numbered list from text.

        Args:
            text: Text with numbered list

        Returns:
            List of items
        """
        items = []
        pattern = r"^\s*\d+[\.\)]\s+(.+)$"

        for line in text.split("\n"):
            match = re.match(pattern, line)
            if match:
                items.append(match.group(1).strip())

        return items
