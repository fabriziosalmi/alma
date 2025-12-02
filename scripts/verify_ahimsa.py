"""
Verification Script for Protocol Ahimsa
=======================================

Tests:
1. Immune System: SQL Injection -> 204 (Silent Drop)
2. Immune System: High Entropy -> 204 (Silent Drop)
3. Error Handling: Panic -> 500 (Medic Persona)
4. Local Fallback: TinyLLM instantiation
"""

import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from alma.api.main import app
from alma.core.llm_service import TinyLLM

client = TestClient(app, raise_server_exceptions=False)

def test_immune_system_sqli():
    print("\n[1] Testing Immune System (SQL Injection)...")
    # Payload with SQL Injection
    payload = {"input": "SELECT * FROM users;"}
    response = client.post("/api/v1/conversation/chat", json=payload)
    
    if response.status_code == 204:
        print("✓ PASS: Malicious SQLi request was silently dropped (204).")
    else:
        print(f"✗ FAIL: Expected 204, got {response.status_code}")
        print(response.text)

def test_immune_system_entropy():
    print("\n[2] Testing Immune System (High Entropy)...")
    # Payload with random noise
    import random
    import string
    noise = "".join(random.choices(string.ascii_letters + string.digits, k=1000))
    payload = {"input": noise}
    response = client.post("/api/v1/conversation/chat", json=payload)
    
    if response.status_code == 204:
        print("✓ PASS: High entropy noise was silently dropped (204).")
    else:
        print(f"✗ FAIL: Expected 204, got {response.status_code}")
        print(response.text)

def test_error_handling():
    print("\n[3] Testing Empathetic Error Handling...")
    # We need an endpoint that crashes. 
    # Since we can't easily modify the app to crash on command without adding a route,
    # we will manually invoke the handler or mock a crash if possible.
    # For now, let's try to hit a non-existent endpoint which gives 404, 
    # but we want 500.
    # Let's mock a route that raises an exception.
    
    @app.get("/test/crash")
    def crash_route():
        raise ValueError("Simulated System Failure")
    
    try:
        response = client.get("/test/crash")
        data = response.json()
        
        if response.status_code == 500 and data.get("persona") == "MEDIC":
            print("✓ PASS: System Panic caught by Medic Persona.")
            print(f"  Message: {data.get('message')}")
        else:
            print(f"✗ FAIL: Expected 500 + Medic, got {response.status_code}")
            print(data)
    except Exception as e:
        print(f"✗ FAIL: Exception leaked: {e}")

def test_local_fallback():
    print("\n[4] Testing Local-First Fallback (TinyLLM)...")
    llm = TinyLLM()
    response = asyncio.run(llm.generate("Hello"))
    
    if "Offline Mode" in response:
        print("✓ PASS: TinyLLM is active and responding.")
    else:
        print(f"✗ FAIL: TinyLLM response incorrect: {response}")

if __name__ == "__main__":
    print("=== Protocol Ahimsa Verification ===")
    test_immune_system_sqli()
    test_immune_system_entropy()
    test_error_handling()
    test_local_fallback()
    print("\n=== Verification Complete ===")
