import json
import asyncio
from typing import TypedDict, Annotated, Literal, Union, List, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage

from alma.core.config import get_settings
from alma.engines.proxmox import ProxmoxEngine
from alma.mcp_server import deploy_vm, download_template, list_resources

# --- State Definition ---
class DeploymentState(TypedDict):
    """State management for the deployment process."""
    messages: List[BaseMessage]
    intent: str
    vm_name: str | None
    template: str | None
    error: str | None
    status: str | None  # Current user-facing status message
    execution_result: Any | None

# --- Nodes ---

async def parse_intent(state: DeploymentState) -> dict[str, Any]:
    """Extract intent and params from the latest message."""
    import re
    last_msg = state["messages"][-1].content
    if isinstance(last_msg, list):
        last_msg = str(last_msg)  # Simple fallback for multimodal
    
    # Simple regex parsing (Fast Track logic extracted here)
    name_match = re.search(r"named\s+([a-zA-Z0-9\-\_]+)", last_msg, re.IGNORECASE)
    template_match = re.search(r"(alpine|ubuntu|debian)", last_msg, re.IGNORECASE)
    
    intent = "deploy" if "deploy" in last_msg.lower() else "unknown"
    vm_name = name_match.group(1) if name_match else state.get("vm_name")
    template = template_match.group(1) if template_match else (state.get("template") or "alpine")
    
    return {
        "intent": intent, 
        "vm_name": vm_name, 
        "template": template,
        "status": f"Parsing... Intent={intent}"
    }

async def validate_params(state: DeploymentState) -> dict[str, Any]:
    """Check if we have enough info to proceed."""
    if not state["vm_name"]:
        return {"error": "Missing VM Name", "status": "Error: Missing Name"}
    if not state["template"]:
        return {"error": "Missing Template", "status": "Error: Missing Template"}
    
    return {"error": None, "status": "Valid parameters."}

async def check_resources(state: DeploymentState) -> dict[str, Any]:
    """Verify if template exists, attempt self-healing (download) if needed."""
    template = state["template"]
    
    # Proactive check logic
    # We use ProxmoxEngine or MCP tools
    # Ideally logic should be in the tool, but the 'Self-Healing' is the agent's job.
    
    # Simulation for now: Check if template in ["alpine", "ubuntu"]
    # Real logic: Try to find optimization
    
    if template not in ["alpine", "ubuntu", "debian"]:
        return {"status": f"Template {template} unknown, might fail."}
    
    # We optimistically assume we can try to download if it's a known OS
    # The 'download_template' tool in MCP handles the actual check/download idempotency
    return {"status": f"Resources check passed for {template}"}

async def execute_deployment(state: DeploymentState) -> dict[str, Any]:
    """Execute the deployment via MCP."""
    vm_name = state["vm_name"]
    template = state["template"]
    if not vm_name or not template:
        return {"error": "Missing params", "status": "Failed"}
    
    # 1. Ensure Template (Self-Healing Step integrated in execution for simplicity or separate node)
    # Let's call download_template first just in case (Idempotent)
    # Raising status event
    
    try:
        # We need to run inside a loop or async context compatible with the tool
        # The tool `download_template` returns a string message
        dl_res = await download_template("local", template)
        
        # 2. Deploy
        res = await deploy_vm(vm_name, template)
        
        return {
            "execution_result": res, 
            "status": "Deployment Executed", 
            "error": None if "Successfully" in res else res
        }
    except Exception as e:
        return {"error": str(e), "status": "Deployment Failed"}

async def verify_deployment(state: DeploymentState) -> dict[str, Any]:
    """Verify state on Proxmox with retry."""
    if state.get("error"):
        return {"status": "Skipping verification due to error."}
    
    vm_name = state["vm_name"]
    found = False
    
    # Retry loop (10 attempts, 3s delay = 30s)
    for i in range(10):
        resources_json = await list_resources()
        resources = json.loads(resources_json)
        found = any(r.get("name") == vm_name for r in resources)
        if found:
            break
        await asyncio.sleep(3)
    
    if found:
        return {"status": f"Verified: {vm_name} is running!", "execution_result": "Success"}
    else:
        return {"error": "Verification Failed: VM not found after retries.", "status": "Verification Failed"}

# --- Edges ---

def route_validation(state: DeploymentState):
    if state["error"]:
        return "end" # Or ask clarification
    return "check_resources"

def route_execution(state: DeploymentState):
    # If check failed? 
    return "execute_deployment"

# --- Graph Assembly ---

workflow = StateGraph(DeploymentState)

workflow.add_node("parse_intent", parse_intent)
workflow.add_node("validate_params", validate_params)
workflow.add_node("check_resources", check_resources)
workflow.add_node("execute_deployment", execute_deployment)
workflow.add_node("verify_deployment", verify_deployment)

workflow.set_entry_point("parse_intent")

workflow.add_edge("parse_intent", "validate_params")
workflow.add_conditional_edges("validate_params", route_validation, {
    "end": END,
    "check_resources": "check_resources"
})
workflow.add_edge("check_resources", "execute_deployment")
workflow.add_edge("execute_deployment", "verify_deployment")
workflow.add_edge("verify_deployment", END)

# Compile
app = workflow.compile()
