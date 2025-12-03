"""
ALMA Advanced Cognitive Engine
=================================

This module implements the meta-cognitive layer of the AI orchestrator. It is
responsible for context tracking, risk assessment, and dynamic persona selection
to provide a safer, more intuitive, and more aware conversational experience.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Constants ---

# If this value is returned, the orchestrator must halt all further processing.
SAFETY_OVERRIDE = "ACTION_BLOCKED_CRITICAL_RISK"

# Thresholds for risk assessment
FRUSTRATION_THRESHOLD_HIGH = 0.75

# Keywords for context detection
CONTEXT_KEYWORDS = {
    "networking": {"network", "subnet", "firewall", "vlan", "ip", "route"},
    "storage": {"disk", "storage", "volume", "ssd", "nfs"},
    "security": {"security", "auth", "user", "password", "permissions", "ssl"},
    "database": {"database", "postgres", "mysql", "db", "sql"},
}

# --- Data Models ---


class FocusContext(BaseModel):
    """Tracks the user's current conversational focus."""

    active_resource_id: str | None = Field(
        None, description="The specific resource being discussed."
    )
    current_topic: str = Field("general", description="The general topic of conversation.")
    topic_confidence: float = Field(0.0, description="Confidence score for the detected topic.")


class CommandRiskLevel(str, Enum):
    """Enumeration for the assessed risk level of a command."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class UserEmotionalStability(str, Enum):
    """Enumeration for the assessed emotional state of the user."""

    STABLE = "STABLE"
    NEUTRAL = "NEUTRAL"
    VOLATILE = "VOLATILE"


class SystemHealth(str, Enum):
    """Enumeration for the system's internal health state."""

    OPTIMAL = "OPTIMAL"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class RiskProfile(BaseModel):
    """Represents the overall risk assessment for a given request."""

    command_risk_level: CommandRiskLevel = CommandRiskLevel.LOW
    user_emotional_stability: UserEmotionalStability = UserEmotionalStability.STABLE
    requires_step_up_auth: bool = False


# --- Core Logic Functions ---


def detect_context_shift(input_text: str, current_focus: FocusContext) -> FocusContext:
    """
    Analyzes input text to detect shifts in conversational topic.

    If a topic shift is detected, it clears the active resource ID to prevent
    accidental commands being run on a previous, out-of-context resource.
    """
    input_words = set(input_text.lower().split())

    for topic, keywords in CONTEXT_KEYWORDS.items():
        if keywords.intersection(input_words):
            if topic != current_focus.current_topic:
                logger.warning(
                    f"Context shift detected: Old='{current_focus.current_topic}', New='{topic}'."
                )
                # Major shift: clear the active resource to be safe.
                return FocusContext(
                    active_resource_id=None,
                    current_topic=topic,
                    topic_confidence=0.9,  # High confidence on keyword match
                )

    # No shift detected, return the existing context
    return current_focus


def assess_risk(intent: str, frustration: float) -> RiskProfile:
    """
    Assesses the risk of an operation based on the user's intent and emotional state.
    """
    profile = RiskProfile()

    # Assess user stability
    if frustration > FRUSTRATION_THRESHOLD_HIGH:
        profile.user_emotional_stability = UserEmotionalStability.VOLATILE
    elif frustration > 0.4:
        profile.user_emotional_stability = UserEmotionalStability.NEUTRAL
    else:
        profile.user_emotional_stability = UserEmotionalStability.STABLE

    # Assess command risk
    if "destroy" in intent or "delete" in intent:
        profile.command_risk_level = CommandRiskLevel.HIGH
    elif "deploy" in intent or "apply" in intent or "create" in intent:
        profile.command_risk_level = CommandRiskLevel.MEDIUM
    else:
        profile.command_risk_level = CommandRiskLevel.LOW

    # CRITICAL RISK MATRIX: Destructive action + Volatile user
    if (
        profile.command_risk_level == CommandRiskLevel.HIGH
        and profile.user_emotional_stability == UserEmotionalStability.VOLATILE
    ):
        logger.critical("CRITICAL RISK DETECTED: Volatile user attempting destructive action.")
        profile.command_risk_level = CommandRiskLevel.CRITICAL
        profile.requires_step_up_auth = True

    return profile


def select_persona(intent_type: str, system_health: SystemHealth = SystemHealth.OPTIMAL) -> str:
    """
    Selects the appropriate AI persona based on the intent category and system health.
    """
    # If system is sick, the Medic takes charge immediately.
    if system_health != SystemHealth.OPTIMAL:
        return "MEDIC"

    if intent_type.startswith("generate_") or intent_type.startswith("suggest_"):
        return "ARCHITECT"
    if intent_type.startswith("deploy_") or intent_type.startswith("rollback_"):
        return "OPERATOR"
    if intent_type.startswith("troubleshoot_") or intent_type.startswith("diagnose_"):
        return "MEDIC"
    return "DEFAULT"


class AdvancedCognitiveEngine:
    """
    A stateful engine that integrates context, risk, and persona.
    """

    def __init__(self):
        self.focus = FocusContext()
        self.frustration_level = 0.0
        self.system_health = SystemHealth.OPTIMAL

    def process_advanced(self, user_input: str, intent: str) -> dict[str, Any]:
        """
        Runs the full meta-cognitive loop on a user request.

        Args:
            user_input: The raw text from the user.
            intent: The pre-classified intent (e.g., "destroy_vm").

        Returns:
            A dictionary containing the results of the cognitive analysis,
            or a safety override string.
        """
        # Normalize input and update frustration level
        self._update_frustration(user_input) # in context
        self.focus = detect_context_shift(user_input, self.focus)

        # 3. Assess the risk of the intended action
        risk_profile = assess_risk(intent, self.frustration_level)

        # 4. Check for SAFETY OVERRIDE
        if risk_profile.command_risk_level == CommandRiskLevel.CRITICAL:
            logger.error("Safety override triggered due to CRITICAL risk. Halting operation.")
            return {"override": SAFETY_OVERRIDE, "risk_profile": risk_profile}

        # 5. Select the appropriate persona for the response
        persona = select_persona(intent, self.system_health)

        logger.info(
            f"Cognitive analysis complete. Risk: {risk_profile.command_risk_level}, Persona: {persona}"
        )

        return {
            "focus_context": self.focus,
            "risk_profile": risk_profile,
            "persona": persona,
            "override": None,
        }
