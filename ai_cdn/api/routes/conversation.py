"""API routes for conversational interface."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_cdn.core.llm import ConversationalOrchestrator, MockLLM

router = APIRouter(prefix="/conversation", tags=["conversation"])

# Global orchestrator instance
orchestrator = ConversationalOrchestrator(llm=MockLLM())


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


@router.post("/chat", response_model=ConversationResponse)
async def chat(request: ConversationRequest) -> ConversationResponse:
    """
    Chat with the AI about infrastructure.

    Args:
        request: Conversation request

    Returns:
        Conversation response with intent and suggestions
    """
    intent_result = await orchestrator.parse_intent(request.message)

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
async def generate_blueprint(request: BlueprintGenerationRequest) -> Dict[str, Any]:
    """
    Generate a blueprint from natural language description.

    Args:
        request: Blueprint generation request

    Returns:
        Generated blueprint
    """
    blueprint = await orchestrator.natural_language_to_blueprint(request.description)
    return blueprint


@router.post("/describe-blueprint", response_model=Dict[str, str])
async def describe_blueprint(request: BlueprintDescriptionRequest) -> Dict[str, str]:
    """
    Convert blueprint to natural language description.

    Args:
        request: Blueprint description request

    Returns:
        Natural language description
    """
    description = await orchestrator.blueprint_to_natural_language(request.blueprint)
    return {"description": description}


@router.post("/suggest-improvements", response_model=ImprovementResponse)
async def suggest_improvements(request: ImprovementRequest) -> ImprovementResponse:
    """
    Get AI suggestions for improving a blueprint.

    Args:
        request: Improvement request

    Returns:
        List of improvement suggestions
    """
    suggestions = await orchestrator.suggest_improvements(request.blueprint)
    return ImprovementResponse(suggestions=suggestions)


@router.post("/clear-history")
async def clear_history() -> Dict[str, str]:
    """
    Clear conversation history.

    Returns:
        Success message
    """
    orchestrator.clear_history()
    return {"message": "Conversation history cleared"}
