import asyncio
import sys
from fastapi import Request, Response
from starlette.datastructures import Headers

# Add project root to path
sys.path.append(".")


async def test_bloom_filter():
    print("\n--- Testing Bloom Filter ---")
    from alma.core.immune_system import BloomFilter, ImmuneResponse

    bf = BloomFilter()

    # Test known bad
    res = bf.check("malicious_bot_user_agent")
    print(f"Check 'malicious_bot_user_agent': Blocked={res.blocked} (Expected: True)")
    assert res.blocked == True

    # Test good
    res = bf.check("normal_user_agent")
    print(f"Check 'normal_user_agent': Blocked={res.blocked} (Expected: False)")
    assert res.blocked == False

    print("✓ Bloom Filter Verified")


async def test_idempotency():
    print("\n--- Testing Idempotency Middleware ---")
    from alma.middleware.idempotency import IdempotencyMiddleware

    # Mock App
    async def mock_app(scope, receive, send):
        assert scope["type"] == "http"
        # Return a timestamp to prove caching
        import time

        body = str(time.time()).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )

    middleware = IdempotencyMiddleware(mock_app)

    # Helper to simulate request
    async def call_middleware(key=None):
        scope = {
            "type": "http",
            "headers": [[b"idempotency-key", key.encode()]] if key else [],
        }
        response_body = b""

        async def receive():
            return {"type": "http.request"}

        async def send(message):
            nonlocal response_body
            if message["type"] == "http.response.body":
                response_body += message.get("body", b"")

        await middleware(scope, receive, send)
        return response_body

    # 1. First call with key
    resp1 = await call_middleware("key1")
    print(f"Resp 1: {resp1}")

    # 2. Second call with same key (should be cached -> same timestamp)
    resp2 = await call_middleware("key1")
    print(f"Resp 2: {resp2}")

    assert resp1 == resp2
    print("✓ Idempotency Verified (Responses Match)")

    # 3. Call with different key
    resp3 = await call_middleware("key2")
    print(f"Resp 3: {resp3}")
    assert resp1 != resp3
    print("✓ Idempotency Verified (Different Keys -> Different Responses)")


async def test_circuit_breaker():
    print("\n--- Testing Circuit Breaker ---")
    from alma.core.resilience import CircuitBreaker, CircuitBreakerOpenException

    cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=1)

    # 1. Success
    async def success_func():
        return "success"

    await cb.call(success_func)
    print("✓ Success call passed")

    # 2. Failures
    async def fail_func():
        raise ValueError("Fail")

    try:
        await cb.call(fail_func)
    except ValueError:
        pass

    try:
        await cb.call(fail_func)
    except ValueError:
        pass

    # 3. Circuit should be OPEN now
    try:
        await cb.call(success_func)
        print("❌ Circuit failed to open!")
    except CircuitBreakerOpenException:
        print("✓ Circuit OPEN caught correctly")


async def main():
    await test_bloom_filter()
    await test_idempotency()
    await test_circuit_breaker()


if __name__ == "__main__":
    asyncio.run(main())
