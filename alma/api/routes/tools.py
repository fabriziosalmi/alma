"""API routes for LLM tool execution."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from alma.core.llm_orchestrator import EnhancedOrchestrator
from alma.core.llm_service import get_orchestrator
from alma.middleware.auth import verify_api_key

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolExecutionRequest(BaseModel):
    """Request to execute a tool."""

    query: str
    context: dict[str, Any] = {}


class DirectToolRequest(BaseModel):
    """Request to directly execute a specific tool."""

    tool_name: str
    arguments: dict[str, Any]
    context: dict[str, Any] = {}


class ToolExecutionResponse(BaseModel):
    """Response from tool execution."""

    success: bool
    tool: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    timestamp: str


class ToolsListResponse(BaseModel):
    """List of available tools."""

    tools: list[dict[str, Any]]
    count: int


@router.get("/", response_model=ToolsListResponse)
async def list_tools(
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> ToolsListResponse:
    """
    Get list of all available tools.

    Returns:
        List of tool definitions with descriptions and parameters
    """
    tools = orchestrator.get_available_tools()

    return ToolsListResponse(tools=tools, count=len(tools))


@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    request: ToolExecutionRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
    api_key: str = Depends(verify_api_key),
) -> ToolExecutionResponse:
    """
    Execute a tool based on natural language query.

    The LLM will analyze the query and select the most appropriate tool.

    Args:
        request: Tool execution request with natural language query
        orchestrator: Orchestrator instance

    Returns:
        Tool execution result
    """
    result = await orchestrator.execute_function_call(request.query, request.context)

    return ToolExecutionResponse(**result)


@router.post("/execute-direct", response_model=ToolExecutionResponse)
async def execute_tool_direct(
    request: DirectToolRequest,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
    api_key: str = Depends(verify_api_key),
) -> ToolExecutionResponse:
    """
    Directly execute a specific tool with provided arguments.

    Bypasses LLM selection and executes the named tool directly.

    Args:
        request: Direct tool execution request
        orchestrator: Orchestrator instance

    Returns:
        Tool execution result
    """
    from alma.core.tools import InfrastructureTools

    tools = InfrastructureTools()
    result = await tools.execute_tool(request.tool_name, request.arguments, request.context)

    return ToolExecutionResponse(**result.model_dump())


@router.get("/{tool_name}", response_model=dict[str, Any])
async def get_tool_info(
    tool_name: str,
    orchestrator: EnhancedOrchestrator = Depends(get_orchestrator),
) -> dict[str, Any]:
    """
    Get detailed information about a specific tool.

    Args:
        tool_name: Name of the tool
        orchestrator: Orchestrator instance

    Returns:
        Tool definition and documentation
    """
    tools = orchestrator.get_available_tools()

    for tool in tools:
        if tool["name"] == tool_name:
            return tool

    raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


@router.post("/validate-blueprint")
async def validate_blueprint(
    blueprint: dict[str, Any],
    strict: bool = False,
) -> dict[str, Any]:
    """
    Validate a blueprint using the validation tool.

    Convenience endpoint for blueprint validation.

    Args:
        blueprint: Blueprint to validate
        strict: Enable strict validation mode

    Returns:
        Validation result
    """
    from alma.core.tools import InfrastructureTools

    tools = InfrastructureTools()
    result = await tools.execute_tool(
        "validate_blueprint", {"blueprint": blueprint, "strict": strict}
    )

    return result.model_dump()


@router.post("/estimate-resources")
async def estimate_resources(
    workload_type: str, expected_load: str, availability: str = "standard"
) -> dict[str, Any]:
    """
    Estimate resource requirements for a workload.

    Convenience endpoint for resource estimation.

    Args:
        workload_type: Type of workload (web, database, cache, etc.)
        expected_load: Expected load description
        availability: Required availability level

    Returns:
        Resource estimation
    """
    from alma.core.tools import InfrastructureTools

    tools = InfrastructureTools()
    result = await tools.execute_tool(
        "estimate_resources",
        {
            "workload_type": workload_type,
            "expected_load": expected_load,
            "availability": availability,
        },
    )

    return result.model_dump()


@router.post("/security-audit")
async def security_audit(
    blueprint: dict[str, Any],
    compliance_framework: str = "general",
    severity_threshold: str = "medium",
) -> dict[str, Any]:
    """
    Perform security audit on a blueprint.

    Convenience endpoint for security auditing.

    Args:
        blueprint: Blueprint to audit
        compliance_framework: Compliance framework to check against
        severity_threshold: Minimum severity to report

    Returns:
        Security audit findings
    """
    from alma.core.tools import InfrastructureTools

    tools = InfrastructureTools()
    result = await tools.execute_tool(
        "security_audit",
        {
            "blueprint": blueprint,
            "compliance_framework": compliance_framework,
            "severity_threshold": severity_threshold,
        },
    )

    return result.model_dump()
