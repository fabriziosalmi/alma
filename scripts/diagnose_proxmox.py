import asyncio
import os
from alma.engines.proxmox import ProxmoxEngine

# Force load env vars if needed, or rely on system env
# We assume Pydantic settings will pick up ALMA_PROXMOX_PASSWORD etc from environment
# if they are set in the terminal running this.

async def main():
    print("--- Proxmox Diagnostic ---")
    
    # Initialize Engine
    engine = ProxmoxEngine()
    print(f"Config Host: {engine.host}")
    print(f"Config User: {engine.username}")
    # Don't print password explicitly for security, but check if set
    print(f"Password Set: {'Yes' if engine.password else 'No'}")
    
    print("\n[Authenticating...]")
    is_auth = await engine._authenticate()
    print(f"Authenticated: {is_auth}")
    print(f"Mode: {'SSH' if engine.use_ssh else 'API'}")
    
    if not is_auth:
        print("!!! Authentication Failed completely.")
        return

    print("\n[Listing Resources via Engine]")
    try:
        resources = await engine.list_resources()
        print(f"Found {len(resources)} resources.")
        for r in resources:
            print(f" - {r.get('name')} ({r.get('type')}) ID: {r.get('vmid')}")
    except Exception as e:
        print(f"Error listing resources: {e}")

    print("\n[Checking Available Templates via SSH/pveam]")
    # We can use the internal _run_ssh_command if we are in SSH mode
    if engine.use_ssh:
        try:
            # List available templates to download
            # cmd = "pveam available"
            # output = await engine._run_ssh_command(cmd)
            # print("Available Templates (Sample):\n" + output[:200] + "...")
            
            # List downloaded templates on 'local' storage
            cmd = "pveam list local"
            output = await engine._run_ssh_command(cmd)
            print("\nDownloaded Templates on 'local':\n" + output)
        except Exception as e:
            print(f"Error checking templates: {e}")
    else:
        print("Skipping template check (Not in SSH mode).")
        # Try to force SSH check explicitly if currently in API mode
        print("Attempting to force SSH check...")
        if await engine._check_ssh_access():
             print("SSH Access verified!")
             cmd = "pveam list local"
             output = await engine._run_ssh_command(cmd)
             print("\nDownloaded Templates on 'local':\n" + output)
        else:
             print("Could not get SSH access.")

if __name__ == "__main__":
    asyncio.run(main())
