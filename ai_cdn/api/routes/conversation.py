"""API routes for conversational interface."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ai_cdn.core.llm_orchestrator import EnhancedOrchestrator
from ai_cdn.core.llm_service import get_orchestrator

router = APIRouter(prefix="/conversation", tags=["conversation"])


class ConversationRequest(BaseModel):
    """Request for conversational interaction."""

    message: str
    context: Dict[str, Any] = {}


class ConversationResponse(BaseModel):
    """Response from conversational interaction."""

    intent: str
    confidence: float
    response: str
    blueprint: Dict[str, Any] | None = None


class BlueprintGenerationRequest(BaseModel):
    """Request to generate blueprint from description."""

    description: str


class BlueprintDescriptionRequest(BaseModel):
    """Request to describe a blueprint."""

    blueprint: Dict[str, Any]


class ImprovementRequest(BaseModel):
    """Request for blueprint improvements."""

    blueprint: Dict[str, Any]


class ImprovementResponse(BaseModel):
    """Response with improvement suggestions."""

    suggestions: list[str]


class ResourceSizingRequest(BaseModel):
    """Request for resource sizing."""

    workload: str
    expected_load: str


class SecurityAuditRequest(BaseModel):
    """Request for security audit."""

    blueprint: Dict[str, Any]


@router.post("/chat", response_model=ConversationResponse)
async def chat(
    request: ConversationRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> ConversationResponse:
    """
    Chat with the AI about infrastructure.

    Args:
        request: Conversation request
        orchestrator: Orchestrator instance

    Returns:
        Conversation response with intent and suggestions
    """
    intent_result = await orchestrator.parse_intent_with_llm(request.message)

    response_text = f"I understand you want to {intent_result['intent'].replace('_', ' ')}."

    # Generate appropriate response based on intent
    if intent_result["intent"] == "create_blueprint":
        response_text += " I can help you create an infrastructure blueprint."
    elif intent_result["intent"] == "list_blueprints":
        response_text += " You can list blueprints using the /api/v1/blueprints endpoint."
    elif intent_result["intent"] == "deploy":
        response_text += " To deploy, please specify the blueprint name or ID."
    elif intent_result["intent"] == "status":
        response_text += " I can check the status of your infrastructure."
    elif intent_result["intent"] == "rollback":
        response_text += " I can help you rollback a deployment."
    else:
        response_text = "I'm not sure what you want to do. Can you please rephrase?"

    return ConversationResponse(
        intent=intent_result["intent"],
        confidence=intent_result["confidence"],
        response=response_text,
        blueprint=None,
    )


@router.post("/generate-blueprint", response_model=Dict[str, Any])
async def generate_blueprint(
    request: BlueprintGenerationRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Generate a blueprint from natural language description.

    Args:
        request: Blueprint generation request
        orchestrator: Orchestrator instance

    Returns:
        Generated blueprint
    """
    blueprint = await orchestrator.natural_language_to_blueprint(request.description)
    return blueprint


@router.post("/describe-blueprint", response_model=Dict[str, str])
async def describe_blueprint(
    request: BlueprintDescriptionRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> Dict[str, str]:
    """
    Convert blueprint to natural language description.

    Args:
        request: Blueprint description request
        orchestrator: Orchestrator instance

    Returns:
        Natural language description
    """
    description = await orchestrator.blueprint_to_natural_language(request.blueprint)
    return {"description": description}


@router.post("/suggest-improvements", response_model=ImprovementResponse)
async def suggest_improvements(
    request: ImprovementRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> ImprovementResponse:
    """
    Get AI suggestions for improving a blueprint.

    Args:
        request: Improvement request
        orchestrator: Orchestrator instance

    Returns:
        List of improvement suggestions
    """
    suggestions = await orchestrator.suggest_improvements(request.blueprint)
    return ImprovementResponse(suggestions=suggestions)


@router.post("/clear-history")
async def clear_history(
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> Dict[str, str]:
    """
    Clear conversation history.

    Args:
        orchestrator: Orchestrator instance

    Returns:
        Success message
    """
    orchestrator.clear_history()
    return {"message": "Conversation history cleared"}


@router.post("/resource-sizing", response_model=Dict[str, Any])
async def resource_sizing(
    request: ResourceSizingRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get AI-powered resource sizing recommendations.

    Args:
        request: Resource sizing request
        orchestrator: Orchestrator instance

    Returns:
        Resource recommendations
    """
    sizing = await orchestrator.estimate_resources(request.workload, request.expected_load)
    return sizing


@router.post("/security-audit", response_model=Dict[str, Any])
async def security_audit(
    request: SecurityAuditRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Perform AI-powered security audit of a blueprint.

    Args:
        request: Security audit request
        orchestrator: Orchestrator instance

    Returns:
        Security findings
    """
    findings = await orchestrator.security_audit(request.blueprint)
    return {"findings": findings}
