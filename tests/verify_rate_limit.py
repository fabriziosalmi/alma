import sys
import asyncio
from unittest.mock import MagicMock, patch
from fastapi import Request

# Add project root to path
sys.path.append(".")

from alma.middleware.rate_limit import RateLimiter, EndpointRateLimiter

async def test_rate_limiter():
    print("\n--- Testing Rate Limiter ---")
    
    # 1. Test In-Memory Fallback
    print("Testing In-Memory Fallback...")
    limiter = RateLimiter(redis_url="redis://nonexistent:6379", enabled=True)
    # Force initialization failure to trigger fallback
    await limiter.initialize()
    
    assert limiter._redis_available == False, "Redis should be unavailable"
    
    # Mock request
    scope = {
        "type": "http", 
        "client": ("127.0.0.1", 12345), 
        "path": "/test",
        "headers": [],
        "scheme": "http",
        "method": "GET",
        "query_string": b""
    }
    request = Request(scope)
    
    # Consume tokens
    limiter.set_limit("127.0.0.1", 2, 1.0) # 2 burst, 1 req/s
    
    is_limited, _ = await limiter.is_rate_limited(request)
    assert not is_limited, "Request 1 should pass"
    
    is_limited, _ = await limiter.is_rate_limited(request)
    assert not is_limited, "Request 2 should pass"
    
    is_limited, retry = await limiter.is_rate_limited(request)
    assert is_limited, "Request 3 should be limited"
    print(f"Rate limited as expected. Retry after: {retry:.2f}s")
    
    # 2. Test EndpointRateLimiter
    print("\nTesting EndpointRateLimiter...")
    endpoint_limiter = EndpointRateLimiter(default_rpm=60)
    endpoint_limiter.set_endpoint_limit("/api/v1/heavy", 10) # 10 RPM
    
    # Default endpoint
    req_default = Request({
        "type": "http", 
        "client": ("127.0.0.1", 12345), 
        "path": "/api/v1/normal",
        "headers": [],
        "scheme": "http",
        "method": "GET",
        "query_string": b""
    })
    l_default = endpoint_limiter._get_limiter(req_default)
    # Default RPM 60 -> 1 req/s refill, burst ~10
    assert l_default.default_limits[1] == 1.0 
    
    # Heavy endpoint
    req_heavy = Request({
        "type": "http", 
        "client": ("127.0.0.1", 12345), 
        "path": "/api/v1/heavy/action",
        "headers": [],
        "scheme": "http",
        "method": "GET",
        "query_string": b""
    })
    l_heavy = endpoint_limiter._get_limiter(req_heavy)
    # 10 RPM -> 0.166 req/s
    assert abs(l_heavy.default_limits[1] - (10/60.0)) < 0.01
    
    print("✓ Rate Limiter Logic Verified")

if __name__ == "__main__":
    asyncio.run(test_rate_limiter())
