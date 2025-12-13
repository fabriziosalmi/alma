import asyncio
from alma.mcp_server import download_template

async def main():
    print("--- Testing Template Download Logic ---")
    print("Attempting to download 'ubuntu-20.04-standard_20.04-1_amd64.tar.zst' to 'local'...")
    
    # Note: This requires SSH access to be configured and working
    # And the template to exist in Proxmox repo.
    # We use a known standard template name for testing.
    
    res = await download_template("local", "ubuntu-20.04-standard_20.04-1_amd64.tar.zst")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
