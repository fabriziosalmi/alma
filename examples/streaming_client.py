"""Client example for streaming API responses."""

import asyncio
import httpx
import json


async def stream_chat():
    """Example: Stream chat responses."""
    url = "http://localhost:8000/api/v1/conversation/chat-stream"
    
    data = {
        "message": "I need a high-availability web application with autoscaling",
        "context": {}
    }
    
    print("🤖 ALMA Streaming Chat Demo\n")
    print(f"User: {data['message']}\n")
    print("Assistant: ", end="", flush=True)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=data) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = line[6:]  # Remove "data: " prefix
                    
                    try:
                        event = json.loads(event_data)
                        event_type = event.get("type")
                        
                        if event_type == "intent":
                            intent = event["data"]["intent"]
                            confidence = event["data"]["confidence"]
                            print(f"\n[Intent: {intent} ({confidence:.0%} confidence)]\n")
                            print("Response: ", end="", flush=True)
                        
                        elif event_type == "text":
                            # Print text chunks as they arrive
                            print(event["data"], end="", flush=True)
                        
                        elif event_type == "error":
                            print(f"\n❌ Error: {event['data']}")
                        
                        elif event_type == "done":
                            print("\n\n✅ Stream complete")
                    
                    except json.JSONDecodeError:
                        pass


async def stream_blueprint_generation():
    """Example: Stream blueprint generation."""
    url = "http://localhost:8000/api/v1/conversation/generate-blueprint-stream"
    
    data = {
        "description": "Kubernetes microservices platform with service mesh, monitoring, and CI/CD"
    }
    
    print("\n" + "="*80)
    print("🏗️  ALMA Streaming Blueprint Generation Demo\n")
    print(f"Description: {data['description']}\n")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=data) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = line[6:]
                    
                    try:
                        event = json.loads(event_data)
                        event_type = event.get("type")
                        
                        if event_type == "status":
                            print(f"📊 {event['data']}")
                        
                        elif event_type == "text":
                            print(event["data"], end="", flush=True)
                        
                        elif event_type == "blueprint":
                            print("\n\n📋 Generated Blueprint:")
                            print(json.dumps(event["data"], indent=2))
                        
                        elif event_type == "warning":
                            print(f"\n⚠️  {event['data']}")
                        
                        elif event_type == "error":
                            print(f"\n❌ Error: {event['data']}")
                        
                        elif event_type == "done":
                            print("\n\n✅ Blueprint generation complete")
                    
                    except json.JSONDecodeError:
                        pass


async def compare_streaming_vs_blocking():
    """Compare streaming vs blocking response times."""
    import time
    
    print("\n" + "="*80)
    print("⚡ Streaming vs Blocking Performance Comparison\n")
    
    # Test blocking endpoint
    print("Testing blocking endpoint...")
    start = time.time()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:8000/api/v1/conversation/generate-blueprint",
            json={"description": "Simple web application with database"}
        )
        blocking_time = time.time() - start
        print(f"✓ Blocking response: {blocking_time:.2f}s")
        print(f"  Time to first byte: {blocking_time:.2f}s (waited for full response)")
    
    # Test streaming endpoint
    print("\nTesting streaming endpoint...")
    start = time.time()
    first_byte_time = None
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/conversation/generate-blueprint-stream",
            json={"description": "Simple web application with database"}
        ) as response:
            async for line in response.aiter_lines():
                if first_byte_time is None:
                    first_byte_time = time.time() - start
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "done":
                            break
                    except:
                        pass
    
    streaming_time = time.time() - start
    print(f"✓ Streaming response: {streaming_time:.2f}s total")
    print(f"  Time to first byte: {first_byte_time:.2f}s")
    print(f"\n📈 Improvement: {((blocking_time - first_byte_time) / blocking_time * 100):.0f}% faster perceived response time")


async def interactive_chat():
    """Interactive streaming chat session."""
    print("\n" + "="*80)
    print("💬 Interactive ALMA Chat (Streaming)")
    print("Type 'quit' to exit\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye! 👋")
            break
        
        if not user_input:
            continue
        
        print("AI: ", end="", flush=True)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    "http://localhost:8000/api/v1/conversation/chat-stream",
                    json={"message": user_input}
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                event = json.loads(line[6:])
                                if event.get("type") == "text":
                                    print(event["data"], end="", flush=True)
                                elif event.get("type") == "done":
                                    print("\n")
                            except:
                                pass
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


async def main():
    """Run all examples."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    ALMA Streaming API Examples                          ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Example 1: Stream chat
    await stream_chat()
    
    await asyncio.sleep(1)
    
    # Example 2: Stream blueprint generation
    await stream_blueprint_generation()
    
    await asyncio.sleep(1)
    
    # Example 3: Performance comparison
    # await compare_streaming_vs_blocking()
    
    # Example 4: Interactive chat (uncomment to use)
    # await interactive_chat()


if __name__ == "__main__":
    asyncio.run(main())
