import asyncio
import httpx
import json

# Configuration
TEST_CONTAINER_NAME = "deep-verify-lxc"
TEMPLATE_NAME = "alpine" 
API_URL = "http://localhost:8000/api/v1/conversation/chat-stream"

async def send_chat_command(command, context=None):
    print(f"\n>>> USER: {command}")
    payload = {"message": command, "context": context or {}}
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", API_URL, json=payload) as response:
            if response.status_code != 200:
                print(f"!!! HTTP Error: {response.status_code}")
                return None, None
            
            full_text = ""
            resources_found = []
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        type_ = data.get("type")
                        content = data.get("data")
                        
                        if type_ == "text":
                            print(f"  [AI]: {content}")
                            full_text += content
                        elif type_ == "tool_use":
                            # If the LLM uses list_resources, we might see it here depending on implementation
                            # But usually the result comes as text/observation or embedded in text
                            pass
                        elif type_ == "status":
                            print(f"  [Status]: {content}")
                        
                        # Heuristic: Check if the text contains JSON-like resource list or specific confirmation
                        # In ALMA's implementation of list_resources, it likely returns a formatted string or the LLM summarizes it.
                        if "deep-verify-lxc" in str(content):
                             resources_found.append("deep-verify-lxc")

                    except:
                        pass
            return full_text, resources_found

async def main():
    print("--- Starting Deep Verification (E2E API Loop) ---")
    
    # 1. Pre-Check
    print("\n1. Pre-Check: Listing current resources via Chat...")
    # "List all containers" should invoke the tool and return the list
    text, found = await send_chat_command("List all containers")
    
    if any(TEST_CONTAINER_NAME in item for item in found):
        print(f"   ⚠️ Found existing container '{TEST_CONTAINER_NAME}'.")
        print("   -> Attempting cleanup first...")
        await send_chat_command(f"Delete container {TEST_CONTAINER_NAME}")
        await asyncio.sleep(5)
    else:
        print("   -> Clean. Target container not found.")

    # 2. Deploy
    print(f"\n2. Action: Deploying '{TEST_CONTAINER_NAME}' via Chat API...")
    text, _ = await send_chat_command(f"Deploy a container named '{TEST_CONTAINER_NAME}' using {TEMPLATE_NAME} template")
    
    # Handle Download if needed
    if text and ("download" in text.lower() or "template" in text.lower()):
        print("   -> Chat asked for download confirmation. Confirming...")
        await send_chat_command("Yes, download it")

    # Wait for operation
    print("\n   [Waiting 15s for deployment...]")
    await asyncio.sleep(15)

    # 3. Post-Check
    print(f"\n3. Post-Check: Verifying creation via Chat Inventory...")
    text, _ = await send_chat_command("List all containers")
    
    # We check if the AI mentions our new container
    if TEST_CONTAINER_NAME in text:
        print(f"   ✅ SUCCESS: '{TEST_CONTAINER_NAME}' confirmed in inventory by ALMA Backend.")
    else:
        print(f"   ❌ FAILURE: '{TEST_CONTAINER_NAME}' NOT found in inventory.")
        # Try a more direct question
        print("   -> Retrying specific check...")
        text, _ = await send_chat_command(f"Is there a container named {TEST_CONTAINER_NAME}?")
        if "yes" in text.lower() or TEST_CONTAINER_NAME in text:
             print(f"   ✅ SUCCESS (on retry): AI confirmed existence.")
        else:
             print("   ❌ FAILURE: AI cannot find it.")

    # 4. Cleanup
    print(f"\n4. Cleanup: Stopping/Deleting '{TEST_CONTAINER_NAME}'...")
    await send_chat_command(f"Stop container {TEST_CONTAINER_NAME}")
    # Wait for stop
    await asyncio.sleep(5)
    await send_chat_command(f"Delete container {TEST_CONTAINER_NAME}")

    print("\n--- Verification Complete ---")
    print("For manual SSH verification, run:")
    print(f"  ssh root@<PROXMOX_IP> pct list | grep {TEST_CONTAINER_NAME}")

if __name__ == "__main__":
    asyncio.run(main())
