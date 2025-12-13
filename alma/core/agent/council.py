
"""Multi-Agent Council implementation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import json
import logging
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from alma.core.llm import LLMInterface
from alma.core.llm_service import get_llm

logger = logging.getLogger(__name__)

@dataclass
class AgentMessage:
    agent_name: str
    content: str
    role: str  # 'proposal', 'critique', 'analysis'

@dataclass
class CouncilResult:
    transcript: list[AgentMessage]
    final_blueprint: dict[str, Any]

class Agent:
    def __init__(self, name: str, role: str, persona: str, color: str):
        self.name = name
        self.role = role
        self.persona = persona
        self.color = color
        # LLM is fetched asynchronously

    async def speak(self, context: str, task: str) -> str:
        llm: LLMInterface = await get_llm()
        prompt = f"""
        You are {self.name}, the {self.role}.
        Your Persona: {self.persona}

        Context: {context}

        Task: {task}
        
        Respond entirely in the voice of your persona. Be concise but impactful.
        If you are producing JSON, ensure it is valid.
        """
        # In a real implementation, we'd use a specific method to enforce JSON if needed
        # For this "Wow" demo, we trust the prompt engineering capabilities
        if self.name == "Architect" and self.role == "Infrastructure Designer" and "Final Synthesis" in context:
            # Enforce Blueprint Schema for the Final Decree
            blueprint_schema = {
                "type": "object",
                "properties": {
                    "version": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "resources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "name": {"type": "string"},
                                "provider": {"type": "string"},
                                "specs": {"type": "object"}
                            },
                            "required": ["type", "name"]
                        }
                    }
                },
                "required": ["version", "name", "resources"]
            }
            response = await llm.generate(prompt, schema=blueprint_schema)
        else:
            response = await llm.generate(prompt)
            
        return response.strip()

class Council:
    def __init__(self):
        self.architect = Agent(
            name="Architect",
            role="Infrastructure Designer",
            persona="You are a visionary cloud architect. You design robust, scalable systems. You prioritize functionality and modern patterns.",
            color="blue"
        )
        self.secops = Agent(
            name="SecOps",
            role="Security Auditor",
            persona="You are a paranoid security expert. You trust no one. You hate open ports, root users, and weak passwords. You are harsh but fair.",
            color="red"
        )
        self.finops = Agent(
            name="FinOps",
            role="Financial Analyst",
            persona="You are a frugal budget keeper. You want to save money. You spot waste instantly. You suggest cheaper alternatives.",
            color="green"
        )
        self.logger = []

    def _log(self, agent: Agent, content: str, role: str):
        self.logger.append(AgentMessage(agent_name=agent.name, content=content, role=role))

    async def convene(self, user_intent: str) -> CouncilResult:
        transcript = []
        
        # 1. Architect Draft
        draft_task = f"User Intent: '{user_intent}'. Create a preliminary infrastructure blueprint JSON structure. Focus on resources."
        draft_bp_text = await self.architect.speak("New Project", draft_task)
        self._log(self.architect, draft_bp_text, "proposal")
        
        # 2. SecOps Review
        sec_task = f"Review this blueprint for vulnerabilities: {draft_bp_text}. Critique it mercilessly."
        sec_critique = await self.secops.speak("Security Review", sec_task)
        self._log(self.secops, sec_critique, "critique")

        # 3. FinOps Review
        fin_task = f"Estimate the cost of this blueprint: {draft_bp_text}. Suggest 1 way to save money."
        fin_estimate = await self.finops.speak("Cost Analysis", fin_task)
        self._log(self.finops, fin_estimate, "analysis")

        # 4. Architect Final Polish
        final_task = f"""
        incorporate this feedback into a FINAL valid JSON blueprint.
        Security Feedback: {sec_critique}
        Financial Feedback: {fin_estimate}
        Original Draft: {draft_bp_text}
        
        Output ONLY valid JSON. No markdown formatting.
        """
        final_bp_text = await self.architect.speak("Final Synthesis", final_task)
        
        # Try to parse JSON, if fail, fallback to empty dict (demo resilience)
        try:
            # Strip markdown code blocks if present
            clean_json = final_bp_text.replace("```json", "").replace("```", "").strip()
            final_blueprint = json.loads(clean_json)
        except json.JSONDecodeError:
            final_blueprint = {"error": "Failed to parse final blueprint", "raw": final_bp_text}
            
        self._log(self.architect, "Final blueprint generated.", "finalization")

        return CouncilResult(transcript=self.logger, final_blueprint=final_blueprint)
