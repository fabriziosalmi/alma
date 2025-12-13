"""Enhanced conversational orchestrator with real LLM integration."""

from __future__ import annotations

import json
import re
from typing import Any, cast

import yaml  # type: ignore[import]

from alma.core.llm import ConversationalOrchestrator, LLMInterface
from alma.core.prompts import InfrastructurePrompts
from alma.core.tools import InfrastructureTools
from alma.schemas.tools import ToolResponse
from alma.core.exceptions import MissingResourceError


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
        # 1. Native InfrastructureTools
        native_tools = self.tools.get_available_tools()
        
        # 2. Loading MCP Tools Dynamically
        mcp_tool_definitions = []
        try:
            from alma.mcp_server import mcp
            # FastMCP stores tools in _tool_manager.tool_registry usually, 
            # but let's check the public API or internal structure.
            # mcp.list_tools() is async.
            # We can also access decorated functions directly if we know them, 
            # OR we can replicate the schema generation.
            
            # For simplicity and robustness, let's use the list_tools() if possible, 
            # but we are in async context here? Yes.
            
            # However, list_tools() returns a list of Tool objects with schema.
            # We need to map that to OpenAI format.
            
            # Since mcp internal structure might vary, let's rely on `mcp._tool_manager.list_tools()` 
            # if we can't await here easily (we can, we are in async def).
            
            # Wait, `get_available_tools` is SYNC in the original code below (def get_available_tools).
            # But here we are in `execute_function_call` which IS async.
            # The LLM needs the tools *before* calling this.
            
            # So we need to update `get_available_tools` to be robust or pre-load them.
            # Let's handle this in `get_available_tools` (which is sync).
            pass 
        except ImportError:
            pass

        available_tools = self.get_available_tools()

        try:
            # Ask LLM to select and call appropriate function
            function_call = await self.llm.function_call(user_input, available_tools)

            if not function_call or "function" not in function_call:
                return {"success": False, "error": "LLM did not return valid function call"}

            # Execute the selected tool
            tool_name = function_call.get("function")
            arguments = function_call.get("arguments", {})

            # Check if it's an MCP tool
            try:
                from alma.mcp_server import mcp
                # Check directly in the underlying registry if possible
                # Accessing private members is risky but efficient for 'internalizing'
                # FastMCP uses a dictionary for tools
                tool_func = None
                
                # Check explicit MCP tools we know
                if tool_name == "deploy_vm":
                    # We might have name collision with native tools.
                    # Prioritize MCP?
                     from alma.mcp_server import deploy_vm
                     tool_func = deploy_vm
                elif tool_name == "control_vm":
                     from alma.mcp_server import control_vm
                     tool_func = control_vm
                elif tool_name == "list_resources":
                     from alma.mcp_server import list_resources
                     tool_func = list_resources
                elif tool_name == "get_resource_stats":
                     from alma.mcp_server import get_resource_stats
                     tool_func = get_resource_stats
                elif tool_name == "download_template":
                     from alma.mcp_server import download_template
                     tool_func = download_template
                     # Set default storage if missing
                     if "storage" not in arguments:
                         arguments["storage"] = "local"

                if tool_func:
                    print(f"Executing Internal MCP Tool: {tool_name}")
                    # FastMCP tools are async.
                    result = await tool_func(**arguments)
                    # Result is a JSON string usually (as per our MCP impl).
                    try:
                        return json.loads(result)
                    except:
                        # If simple string
                         return {"result": result}
            except ImportError:
                pass

            # Fallback to native tools
            result: ToolResponse = await self.tools.execute_tool(str(tool_name), arguments, context)
            return result.model_dump()

        except MissingResourceError as e:
            return {
                "success": False,
                "error": str(e),
                "status": "needs_clarification",
                "missing_resource": {
                    "type": e.resource_type,
                    "name": e.resource_name
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Function call execution failed: {e}"}

        """
        Get list of available tools for function calling.

        Returns:
            List of tool definitions
        """
        tools = self.tools.get_available_tools()
        
        # Add MCP tools
        # We manually define schemas for our known MCP tools for now
        # Ideally we'd convert FastMCP schemas
        
        tools.append({
            "type": "function",
            "function": {
                "name": "deploy_vm",
                "description": "Deploy a new VM from a template using Proxmox MCP",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the new VM"},
                        "template": {"type": "string", "description": "Template to clone from"},
                        "cores": {"type": "integer", "description": "CPU cores (default 2)"},
                        "memory": {"type": "integer", "description": "Memory in MB (default 2048)"}
                    },
                    "required": ["name", "template"]
                }
            }
        })
        
        tools.append({
             "type": "function",
             "function": {
                 "name": "control_vm",
                 "description": "Control a VM (start, stop, reboot) using Proxmox MCP",
                 "parameters": {
                     "type": "object",
                     "properties": {
                         "vmid": {"type": "string", "description": "VMID to control"},
                         "action": {"type": "string", "enum": ["start", "stop", "reboot", "shutdown"], "description": "Action to perform"}
                     },
                     "required": ["vmid", "action"]
                 }
             }
         })

        tools.append({
             "type": "function",
             "function": {
                 "name": "list_resources",
                 "description": "List all Proxmox resources (VMs and Containers) using MCP",
                 "parameters": {
                     "type": "object",
                     "properties": {},
                 }
             }
         })

        tools.append({
             "type": "function",
             "function": {
                 "name": "download_template",
                 "description": "Download a template to storage using MCP (e.g. download ubuntu-template to local)",
                 "parameters": {
                     "type": "object",
                     "properties": {
                         "storage": {"type": "string", "description": "Storage ID (default 'local')"},
                         "template": {"type": "string", "description": "Template name"}
                     },
                     "required": ["template"]
                 }
             }
         })

        return tools

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
            findings: list[dict[str, str]] = []
            current_finding: dict[str, str] = {}

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
                return cast(dict[str, Any], json.loads(json_str))
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
                return cast(dict[str, Any], yaml.safe_load(match))
            except yaml.YAMLError:
                continue

        # Try parsing entire text as YAML
        try:
            return cast(dict[str, Any], yaml.safe_load(text))
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
