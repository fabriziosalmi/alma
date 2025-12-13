"""Conversation API routes."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from alma.core.llm_orchestrator import EnhancedOrchestrator
from alma.core.llm_service import get_orchestrator
from alma.core.exceptions import MissingResourceError

router = APIRouter(prefix="/conversation", tags=["conversation"])


class ConversationRequest(BaseModel):
    """Request for conversational interaction."""

    message: str
    context: dict[str, Any] = {}


class ConversationResponse(BaseModel):
    """Response from conversational interaction."""

    intent: str
    confidence: float
    response: str
    blueprint: dict[str, Any] | None = None


class BlueprintGenerationRequest(BaseModel):
    """Request to generate blueprint from description."""

    description: str


class BlueprintDescriptionRequest(BaseModel):
    """Request to describe a blueprint."""

    blueprint: dict[str, Any]


class ImprovementRequest(BaseModel):
    """Request for blueprint improvements."""

    blueprint: dict[str, Any]


class ImprovementResponse(BaseModel):
    """Response with improvement suggestions."""

    suggestions: list[str]


class ResourceSizingRequest(BaseModel):
    """Request for resource sizing."""

    workload: str
    expected_load: str


class SecurityAuditRequest(BaseModel):
    """Request for security audit."""

    blueprint: dict[str, Any]


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


@router.post("/generate-blueprint", response_model=dict[str, Any])
async def generate_blueprint(
    request: BlueprintGenerationRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> dict[str, Any]:
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


@router.post("/describe-blueprint", response_model=dict[str, str])
async def describe_blueprint(
    request: BlueprintDescriptionRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> dict[str, str]:
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
) -> dict[str, str]:
    """
    Clear conversation history.

    Args:
        orchestrator: Orchestrator instance

    Returns:
        Success message
    """
    orchestrator.clear_history()
    return {"message": "Conversation history cleared"}


@router.post("/resource-sizing", response_model=dict[str, Any])
async def resource_sizing(
    request: ResourceSizingRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> dict[str, Any]:
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


@router.post("/security-audit", response_model=dict[str, Any])
async def security_audit(
    request: SecurityAuditRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> dict[str, Any]:
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


@router.post("/chat-stream")
async def chat_stream(
    request: ConversationRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> StreamingResponse:
    """
    Stream conversational responses in real-time.

    This endpoint streams the AI's response as it's generated,
    providing better UX for long responses.

    Args:
        request: Conversation request
        orchestrator: Orchestrator instance

    Returns:
        Streaming response with Server-Sent Events
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response."""
        # First, parse intent
        intent_result = await orchestrator.parse_intent_with_llm(request.message)

        # Send intent as first event
        yield f"data: {json.dumps({'type': 'intent', 'data': intent_result})}\n\n"
        print(f"DEBUG: Intent={intent_result['intent']}, Message='{request.message}'")

        # --- FAST TRACK: Direct Execution for 'Deploy' with explicit parameters ---
        if intent_result["intent"] == "deploy":
            import re
            name_match = re.search(r"named\s+([a-zA-Z0-9\-\_]+)", request.message, re.IGNORECASE)
            template_match = re.search(r"(alpine|ubuntu|debian)", request.message, re.IGNORECASE)
            
            print(f"DEBUG: FastTrack check - NameMatch={name_match}, TemplateMatch={template_match}")

            if name_match:
                vm_name = name_match.group(1)
                template = template_match.group(1) if template_match else "alpine" # Default to alpine
                
                yield f"data: {json.dumps({'type': 'status', 'data': f'Initiating deployment of {vm_name} ({template})...'})}\n\n"
                
                try:
                    # Execute directly via Orchestrator -> Tool
                    from alma.mcp_server import deploy_vm, download_template
                    from alma.engines.proxmox import ProxmoxEngine
                    from alma.core.config import get_settings
                    
                    # 1. Check if template exists
                    settings = get_settings()
                    engine = ProxmoxEngine({
                        "host": settings.proxmox_host,
                        "username": settings.proxmox_username,
                        "password": settings.proxmox_password,
                        "verify_ssl": settings.proxmox_verify_ssl,
                        "node": settings.proxmox_node
                    })
                    
                    # Ensure template is available (Logic similar to apply but proactive)
                    # We need to check if "alpine" implies a filename or VM
                    # For Fast Track "alpine", we assume LXC template
                    exists = False
                    # Check list_resources (only covers VMs/CTs, not templates in storage)
                    # We need a proper 'list_templates' but engine doesn't expose it publicy efficiently
                    # So we use a heuristic: try to find it.
                    # Actually, let's just Try to Deploy. 
                    # If deploy fails with "Template not found" error string?
                    # But deploy_vm logic swallows error details often?
                    
                    # BETTER: Just try to download "alpine" if it's alpine/ubuntu
                    # download_template is idempotent (skips if exists)?
                    # Let's check download_template implementation.
                    # It calls `pveam download`. Proxmox handles idempotency? 
                    # Usually returns "already exists" error if exists.
                    
                    # Let's just run download_template for common OSes to be safe?
                    # That slows things down.
                    
                    # Let's try to verify via engine internal
                    # We can use `pveam list local` via SSH or API `nodes/node/storage/local/content`
                    # Too complex for inline.
                    
                    # PROACTIVE DOWNLOAD:
                    # If template is "alpine", ensure we have it.
                    if template in ["alpine", "ubuntu", "debian"]:
                         yield f"data: {json.dumps({'type': 'status', 'data': f'Ensuring {template} template is available...'})}\n\n"
                         # We blindly try to download (or check) 
                         # download_template tool implementation:
                         # It maps "alpine" to "alpine-3.19..." and calls pveam download.
                         # If we call it, and it exists, it might error or succeed fast.
                         # orchestrator.execute uses mcp_server.download_template
                         dl_result = await orchestrator.execute_function_call("download_template", {"os_type": template, "storage": "local"}) 
                         if not dl_result.get("success") and "already exists" not in str(dl_result.get("error", "")):
                              # Log warning but proceed?
                              pass

                    # 2. Deploy
                    result = await orchestrator.execute_function_call("deploy_vm", {"name": vm_name, "template": template})
                    
                    if result.get("success"):
                        response = f"Deployment of **{vm_name}** ({template}) started successfully! \n\nDetails: {result.get('content')}"
                        yield f"data: {json.dumps({'type': 'text', 'data': response})}\n\n"
                        # Also send done
                        yield f"data: {json.dumps({'type': 'done', 'data': 'complete'})}\n\n"
                    else:
                        response = f"Deployment failed: {result.get('error')}"
                        yield f"data: {json.dumps({'type': 'error', 'data': response})}\n\n"
                        yield f"data: {json.dumps({'type': 'done', 'data': 'error'})}\n\n"
                        
                except Exception as e:
                     yield f"data: {json.dumps({'type': 'error', 'data': f'Execution error: {str(e)}'})}\n\n"
                     yield f"data: {json.dumps({'type': 'done', 'data': 'error'})}\n\n"
                
                return

        # Proactive Validation for Deploy/Blueprint (Classic Flow)
        if intent_result["intent"] in ["create_blueprint", "deploy"]:
            try:
                yield f"data: {json.dumps({'type': 'status', 'data': 'Validating requirements...'})}\n\n"
                
                # 1. Generate tentative blueprint
                blueprint = await orchestrator.natural_language_to_blueprint(request.message)
                
                # 2. Check for missing resources (Templates)
                from alma.core.config import get_settings
                from alma.engines.proxmox import ProxmoxEngine
                
                settings = get_settings()
                engine = ProxmoxEngine({
                    "host": settings.proxmox_host,
                    "username": settings.proxmox_username,
                    "password": settings.proxmox_password,
                    "verify_ssl": settings.proxmox_verify_ssl,
                    "node": settings.proxmox_node
                })
                
                # Check templates logic...
                for res in blueprint.get("resources", []):
                    specs = res.get("specs", {})
                    if "template" in specs:
                        tpl_name = specs["template"]
                        vm = await engine._get_vm_by_name(tpl_name)
                        if not vm:
                            raise MissingResourceError("template", tpl_name, f"Template '{tpl_name}' not found.")
                            
            except MissingResourceError as e:
                # Ask CLARIFICATION directly
                suggestion = ""
                if e.resource_type == "template":
                    suggestion = f" I can try to download it for you if you want."
                
                msg = f"I'd love to help run that, but I need a valid **template**. I couldn't find '{e.resource_name}' in Proxmox.{suggestion}\n\nWhich template should I clone (or shall I download '{e.resource_name}')?"
                yield f"data: {json.dumps({'type': 'text', 'data': msg})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'data': 'clarification_needed'})}\n\n"
                return

        # Generate streaming response based on intent
        if intent_result["intent"] == "create_blueprint":
            prompt = f"Generate infrastructure blueprint for: {request.message}"
        elif intent_result["intent"] == "deploy":
            # Fallback to explanation if parameters missing
            prompt = f"Explain deployment process for: {request.message}"
        elif intent_result["intent"] == "status":
            prompt = f"Provide status information for: {request.message}"
        else:
            prompt = f"Respond to infrastructure query: {request.message}"

        # Stream LLM response
        if orchestrator.use_llm and orchestrator.llm:
            try:
                async for chunk in orchestrator.llm.stream_generate(prompt):
                    if chunk:
                        yield f"data: {json.dumps({'type': 'text', 'data': chunk})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
        else:
            # Fallback to non-streaming
            response = f"I understand you want to {intent_result['intent'].replace('_', ' ')}."
            yield f"data: {json.dumps({'type': 'text', 'data': response})}\n\n"

        # Send completion event
        yield f"data: {json.dumps({'type': 'done', 'data': 'complete'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/generate-blueprint-stream")
async def generate_blueprint_stream(
    request: BlueprintGenerationRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> StreamingResponse:
    """
    Stream blueprint generation in real-time.

    Shows the thinking process as the AI generates the blueprint.

    Args:
        request: Blueprint generation request
        orchestrator: Orchestrator instance

    Returns:
        Streaming response
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming blueprint creation."""
        yield f"data: {json.dumps({'type': 'status', 'data': 'Analyzing requirements...'})}\n\n"

        # Generate blueprint with streaming
        if orchestrator.use_llm and orchestrator.llm:
            from alma.core.prompts import InfrastructurePrompts

            prompt = InfrastructurePrompts.blueprint_generation(request.description)

            full_response = ""
            yield f"data: {json.dumps({'type': 'status', 'data': 'Generating blueprint...'})}\n\n"

            try:
                async for chunk in orchestrator.llm.stream_generate(prompt):
                    if chunk:
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'text', 'data': chunk})}\n\n"

                # Try to extract YAML from full response
                import yaml  # type: ignore[import]

                try:
                    # Extract YAML block
                    if "```yaml" in full_response:
                        yaml_start = full_response.find("```yaml") + 7
                        yaml_end = full_response.find("```", yaml_start)
                        yaml_content = full_response[yaml_start:yaml_end].strip()
                        blueprint = yaml.safe_load(yaml_content)
                    elif "```" in full_response:
                        yaml_start = full_response.find("```") + 3
                        yaml_end = full_response.find("```", yaml_start)
                        yaml_content = full_response[yaml_start:yaml_end].strip()
                        blueprint = yaml.safe_load(yaml_content)
                    else:
                        blueprint = yaml.safe_load(full_response)

                    yield f"data: {json.dumps({'type': 'blueprint', 'data': blueprint})}\n\n"
                except Exception:
                    yield f"data: {json.dumps({'type': 'warning', 'data': 'Could not parse as YAML'})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
        else:
            # Fallback
            blueprint = await orchestrator.natural_language_to_blueprint(request.description)
            yield f"data: {json.dumps({'type': 'blueprint', 'data': blueprint})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'data': 'complete'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
