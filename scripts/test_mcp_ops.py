import asyncio
import json
from alma.mcp_server import list_resources, deploy_vm, control_vm

async def main():
    print("--- Testing MCP Tools Internal Logic ---")
    
    # 1. List Resources
    print("\n1. Listing Resources...")
    try:
        res_json = await list_resources()
        resources = json.loads(res_json)
        print(f"Found {len(resources)} resources.")
        
        templates = [r for r in resources if r.get('template') == 1]
        print(f"Found {len(templates)} templates.")
        print(f"All Resources: {json.dumps(resources, indent=2)}")
        
    except Exception as e:
        print(f"FAILED to list resources: {e}")
        return

    # 2. Force Deployment Attempt (Verify Failure Mode)
    print("\n2. Attempting Deployment (Expecting Failure due to missing template)...")
    result = await deploy_vm("test-vm-mcp", "ubuntu-template", cores=1, memory=512)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
