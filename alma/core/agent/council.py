"""Multi-Agent Council implementation."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Type, TypeVar

from rich.console import Console
from pydantic import BaseModel

from alma.core.llm import LLMInterface
from alma.core.llm_service import get_llm
from alma.schemas.council import (
    InfrastructureDraft,
    SecurityCritique,
    CostAnalysis,
    FinalDecree,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass
class AgentMessage:
    agent_name: str
    content: dict[str, Any] | str
    role: str  # 'proposal', 'critique', 'analysis', 'finalization', 'error'


@dataclass
class CouncilResult:
    transcript: list[AgentMessage]
    final_blueprint: dict[str, Any] | None


class Agent:
    def __init__(self, name: str, role: str, persona: str, color: str):
        self.name = name
        self.role = role
        self.persona = persona
        self.color = color

    async def speak(
        self, context: str, task: str, response_model: Type[T] | None = None
    ) -> T | str:
        llm: LLMInterface = await get_llm()
        
        prompt = f"""
        You are {self.name}, the {self.role}.
        Your Persona: {self.persona}

        Context: {context}

        Task: {task}
        """

        if response_model:
            # SOTA Pattern: Schema Enforcement
            schema = response_model.model_json_schema()
            prompt += f"\nOutput must strictly adhere to this JSON schema:\n{schema}"
            
            try:
                # We pass the schema to the LLM interface
                response_text = await llm.generate(prompt, schema=schema)
                
                # SOTA Pattern: Robust parsing (even if LLM wraps in code blocks)
                clean_text = response_text.replace("```json", "").replace("```", "").strip()
                return response_model.model_validate_json(clean_text)
            except Exception as e:
                logger.error(f"Agent {self.name} failed to adhere to schema: {e}")
                raise e
        else:
            return await llm.generate(prompt)


class Council:
    def __init__(self) -> None:
        self.architect = Agent(
            name="Architect",
            role="Infrastructure Designer",
            persona="You are a visionary cloud architect. Design robust, scalable systems using modern patterns.",
            color="blue",
        )
        self.secops = Agent(
            name="SecOps",
            role="Security Auditor",
            persona="You are a paranoid security expert. Trust no one. Find vulnerabilities.",
            color="red",
        )
        self.finops = Agent(
            name="FinOps",
            role="Financial Analyst",
            persona="You are a frugal budget keeper. Identify waste and suggest savings.",
            color="green",
        )
        self.transcript: list[AgentMessage] = []

    def _log(self, agent: Agent, content: Any, role: str) -> None:
        # Convert Pydantic models to dict for storage/viewing
        if isinstance(content, BaseModel):
            log_content = content.model_dump()
        else:
            log_content = str(content)
            
        self.transcript.append(AgentMessage(agent_name=agent.name, content=log_content, role=role))

    async def convene(self, user_intent: str) -> CouncilResult:
        logger.info(f"Council convened for: {user_intent}")
        self.transcript = []

        try:
            # 1. Architect Drafts Blueprint
            draft_context = f"User Intent: '{user_intent}'"
            draft = await self.architect.speak(
                context=draft_context, 
                task="Create a preliminary infrastructure blueprint.", 
                response_model=InfrastructureDraft
            )
            self._log(self.architect, draft, "proposal")
            
            # 2. Parallel Review (SecOps & FinOps) - SOTA Pattern: Async/Await Gather
            logger.info("Starting parallel review...")
            if isinstance(draft, InfrastructureDraft):
                draft_json = draft.model_dump_json()
            else:
                draft_json = str(draft)

            async def run_secops() -> SecurityCritique:
                return await self.secops.speak(
                    context=f"Blueprint: {draft_json}",
                    task="Analyze for security risks.",
                    response_model=SecurityCritique
                )

            async def run_finops() -> CostAnalysis:
                return await self.finops.speak(
                    context=f"Blueprint: {draft_json}",
                    task="Estimate costs and savings.",
                    response_model=CostAnalysis
                )

            # Parallel execution
            sec_review, fin_review = await asyncio.gather(run_secops(), run_finops())
            
            self._log(self.secops, sec_review, "critique")
            self._log(self.finops, fin_review, "analysis")

            # 3. Final Synthesis
            final_context = f"""
            Original Draft: {draft_json}
            Security Feedback: {sec_review.model_dump_json()}
            Financial Feedback: {fin_review.model_dump_json()}
            """
            
            final_decree = await self.architect.speak(
                context=final_context,
                task="Synthesize all feedback into a Final Decree and Blueprint.",
                response_model=FinalDecree
            )
            self._log(self.architect, final_decree, "finalization")

            return CouncilResult(
                transcript=self.transcript, 
                final_blueprint=final_decree.blueprint.model_dump() if final_decree.approved else None
            )

        except Exception as e:
            logger.error(f"The Council collapsed: {e}")
            # Graceful degradation
            self.transcript.append(AgentMessage(agent_name="System", content=f"Council Error: {e}", role="error"))
            return CouncilResult(transcript=self.transcript, final_blueprint=None)
