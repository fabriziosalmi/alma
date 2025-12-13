import asyncio
import sys
import os
import subprocess

# Add project root to path
sys.path.append(os.getcwd())

from alma.core.config import get_settings
from alma.engines.proxmox import ProxmoxEngine
from alma.core.llm_service import LocalStudioLLM

async def check_ssh(host, username, password):
    """Check SSH connectivity using simple subprocess."""
    print(f"     -> Attempting SSH to {username}@{host}...")
    
    # Check if we can reach port 22
    try:
        # Extract hostname from URL if needed
        if "://" in host:
            host_clean = host.split("://")[1].split(":")[0]
        else:
            host_clean = host
            
        # Try generic nc (netcat) check first
        nc_cmd = ["nc", "-z", "-w", "2", host_clean, "22"]
        subprocess.run(nc_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("     -> SSH Port (22) is OPEN.")
        
        # We can't easily check password auth without paramiko or sshpass installed
        # But knowing the port is open is a good sign
        return True
    except subprocess.CalledProcessError:
        print("     -> SSH Port (22) seems CLOSED or blocked.")
        return False
    except FileNotFoundError:
        print("     -> 'nc' command not found, skipping port check.")
        return False

async def verify():
    settings = get_settings()
    
    # Force convert to bool/str for debug print
    verify_ssl = str(settings.proxmox_verify_ssl).lower() == "true"
    
    print("📋 Configuration Loaded:")
    print(f"  - Proxmox Host: {settings.proxmox_host}")
    print(f"  - Proxmox User: {settings.proxmox_username}")
    print(f"  - Verify SSL: {settings.proxmox_verify_ssl}")
    print(f"  - Password Set: {'Yes' if settings.proxmox_password else 'No'}")
    
    # 1. Verify Proxmox API
    print("\n🔒 Verifying Proxmox API connectivity...")
    proxmox_config = {
        "host": settings.proxmox_host,
        "username": settings.proxmox_username,
        "password": settings.proxmox_password,
        "verify_ssl": settings.proxmox_verify_ssl,
        "node": settings.proxmox_node
    }
    
    engine = ProxmoxEngine(proxmox_config)
    
    api_success = False
    try:
        is_healthy = await engine.health_check()
        if is_healthy:
            print(f"  ✅ Proxmox API Connected! (Ticket: {engine.ticket[:10]}...)")
            api_success = True
        else:
            print("  ❌ Proxmox API Auth Failed (401)")
    except Exception as e:
        print(f"  ❌ Proxmox API Error: {e}")

    # 2. SSH Fallback Check
    if not api_success:
        print("\n🔑 Checking SSH Fallback...")
        ssh_ok = await check_ssh(settings.proxmox_host, settings.proxmox_username, settings.proxmox_password)
        if ssh_ok:
            print("  ℹ️  SSH is available. (We might implement SSH-based engine if API fails persistenty)")
        
    # 3. Verify Local LLM
    print("\n🧠 Verifying Local LLM Connectivity...")
    llm = LocalStudioLLM(
        base_url=settings.llm_local_studio_url,
        model_name=settings.llm_local_studio_model
    )
    try:
        await llm._initialize()
        print("  ✅ Local LLM Online")
    except Exception as e:
        print(f"  ❌ Local LLM Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
