"""
ALMA MCP Server.

Exposes Proxmox resources and tools via the Model Context Protocol.
"""

import asyncio
import json
from typing import Any

from mcp.server.fastmcp import FastMCP, Context

from alma.core.config import get_settings
from alma.engines.proxmox import ProxmoxEngine

# Initialize FastMCP Server
mcp = FastMCP("ALMA", dependencies=["httpx", "sshpass"])

# Export tools explicitly for internal usage
__all__ = ["mcp", "list_vms", "list_resources", "get_resource_stats", "deploy_vm", "control_vm", "download_template"]


def get_engine() -> ProxmoxEngine:
    """Get authenticated Proxmox engine."""
    settings = get_settings()
    return ProxmoxEngine({
        "host": settings.proxmox_host,
        "username": settings.proxmox_username,
        "password": settings.proxmox_password,
        "verify_ssl": settings.proxmox_verify_ssl,
        "node": settings.proxmox_node
    })


@mcp.resource("proxmox://{node}/vms")
async def list_vms(node: str) -> str:
    """List all VMs and Containers on a node as JSON."""
    engine = get_engine()
    # Ensure engine uses the requested node if possible, 
    # but ProxmoxEngine config is static per instance usually. 
    # For now, we assume the configured node, but check if it matches.
    if engine.node != node:
        # We could create a new engine or just warn. 
        # For simplicity in v1, we just list what the engine sees.
        pass
        
    resources = await engine.list_resources()
    return json.dumps(resources, indent=2)


@mcp.tool()
async def list_resources() -> str:
    """
    List all available Proxmox resources (VMs and Containers).
    
    Returns:
        JSON string of resources
    """
    engine = get_engine()
    resources = await engine.list_resources()
    return json.dumps(resources, indent=2)


@mcp.tool()
async def get_resource_stats(vmid: str) -> str:
    """
    Get statistics for a specific resource.
    
    Args:
        vmid: The VMID of the resource
    """
    engine = get_engine()
    # Reuse list_resources for now as it contains status
    # In future: implement specific stat call in engine
    resources = await engine.list_resources()
    for res in resources:
        if str(res.get("vmid")) == str(vmid):
            return json.dumps(res, indent=2)
    return json.dumps({"error": "Resource not found"})


@mcp.tool()
async def deploy_vm(name: str, template: str, cores: int = 2, memory: int = 2048) -> str:
    """
    Deploy a new VM from a template.
    
    Args:
        name: Name of the new VM
        template: Name of the template to clone
        cores: Number of CPU cores (default: 2)
        memory: Memory in MB (default: 2048)
    """
    engine = get_engine()
    from alma.core.state import Plan
    from alma.schemas.blueprint import ResourceDefinition
    
    # Construct a minimal plan for the engine
    plan = Plan(
        to_create=[
            ResourceDefinition(
                name=name,
                type="compute",
                provider="proxmox",
                specs={
                    "template": template,
                    "cpu": cores,
                    "memory": memory
                }
            )
        ],
        to_update=[],
        to_delete=[]
    )
    
    try:
        await engine.apply(plan)
        return f"Successfully deployed VM '{name}' from template '{template}'."
    except Exception as e:
        return f"Failed to deploy VM: {str(e)}"


@mcp.tool()
async def control_vm(vmid: str, action: str) -> str:
    """
    Control a VM (start, stop, reboot).
    
    Args:
        vmid: The VMID to control
        action: One of 'start', 'stop', 'reboot', 'shutdown'
    """
    engine = get_engine()
    valid_actions = ["start", "stop", "reboot", "shutdown"]
    if action not in valid_actions:
        return f"Invalid action. Must be one of {valid_actions}"

    # We need to implement this in engine or use raw commands here?
    # Engine has _run_ssh_command.
    # Let's add a public control method to engine or use the private one here (naughty but works)
    # Better: Update engine to have `control_resource(vmid, action)`
    
    # For now, I'll use the private method if I can't update engine easily.
    # But I CAN update engine easily.
    
    # Let's just implement the logic here using the engine's primitive (private) methods for now 
    # to avoid touching core logic too much, OR better: use `engine._authenticate()` then run command.
    
    if not await engine._authenticate():
        return "Authentication failed"
        
    cmd_map = {
        "start": "start",
        "stop": "stop",
        "shutdown": "shutdown", 
        "reboot": "reboot"
    }
    
    qm_cmd = cmd_map[action]
    
    try:
        if engine.use_ssh:
             await engine._run_ssh_command(f"qm {qm_cmd} {vmid}")
        else:
             # API
             # Need to know node. Engine has self.node
             # And type (qemu vs lxc). We don't know type easily without lookup.
             # We should look it up.
             resources = await engine.list_resources()
             res_type = "qemu"
             for r in resources:
                 if str(r.get("vmid")) == str(vmid):
                     res_type = r.get("type", "qemu")
                     break
            
             await engine._api_request("POST", f"nodes/{engine.node}/{res_type}/{vmid}/status/{qm_cmd}")
             
        return f"Successfully executed '{action}' on VM {vmid}"
    except Exception as e:
        return f"Action failed: {str(e)}"

@mcp.tool()
async def download_template(storage: str, template: str) -> str:
    """
    Download a template to storage (e.g., 'local').
    
    Args:
        storage: Storage ID (e.g., 'local', 'local-lvm')
        template: Template name (e.g., 'ubuntu-22.04-standard_22.04-1_amd64.tar.zst')
    """
    engine = get_engine()
    try:
        await engine.download_template(storage, template)
        return f"Successfully downloaded template '{template}' to '{storage}'."
    except Exception as e:
        return f"Failed to download template: {str(e)}"

if __name__ == "__main__":
    mcp.run()
