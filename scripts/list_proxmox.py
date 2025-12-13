import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from alma.core.config import get_settings
from alma.engines.proxmox import ProxmoxEngine

async def list_resources():
    settings = get_settings()
    
    config = {
        "host": settings.proxmox_host,
        "username": settings.proxmox_username,
        "password": settings.proxmox_password,
        "verify_ssl": settings.proxmox_verify_ssl,
        "node": settings.proxmox_node
    }
    
    engine = ProxmoxEngine(config)
    print(f"Connecting to {config['host']}...")
    
    if await engine.health_check():
        print("✅ Auth OK")
        
        # Try to list QEMU VMs
        print("\n--- VMs (QEMU) ---")
        try:
            if engine.use_ssh:
                out = await engine._run_ssh_command(f"pvesh get /nodes/{engine.node}/qemu --output-format json")
                vms = json.loads(out)
            else:
                vms = await engine._api_request("GET", f"nodes/{engine.node}/qemu")
            
            for vm in vms:
                status = vm.get('status', 'unknown')
                print(f"[{vm.get('vmid')}] {vm.get('name')} ({status})")
        except Exception as e:
            print(f"Failed to list VMs: {e}")

        # Try to list LXC Containers
        print("\n--- Containers (LXC) ---")
        try:
            if engine.use_ssh:
                out = await engine._run_ssh_command(f"pvesh get /nodes/{engine.node}/lxc --output-format json")
                cts = json.loads(out)
            else:
                cts = await engine._api_request("GET", f"nodes/{engine.node}/lxc")
                
            for ct in cts:
                status = ct.get('status', 'unknown')
                print(f"[{ct.get('vmid')}] {ct.get('name')} ({status})")
        except Exception as e:
            print(f"Failed to list CTs: {e}")
            
    else:
        print("❌ Auth Failed")

if __name__ == "__main__":
    asyncio.run(list_resources())
