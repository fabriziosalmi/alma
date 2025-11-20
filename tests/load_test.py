"""Load testing and integration tests for rate limiting and metrics."""
import time
import asyncio
import httpx
from typing import List, Dict, Any


async def test_rate_limiting():
    """Test rate limiting with concurrent requests."""
    print("\n🔬 Testing Rate Limiting...")
    print("=" * 60)

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Test 1: Sequential requests to measure rate limiting
        print("\n📊 Test 1: Sequential Requests (should hit rate limit)")
        responses = []
        for i in range(70):
            try:
                response = await client.get(
                    "/api/v1/blueprints",
                    headers={"X-Forwarded-For": "192.168.1.100"},  # Consistent client IP
                )
                status = response.status_code
                headers = response.headers

                if status == 429:
                    print(f"  Request {i+1}: ❌ RATE LIMITED (429)")
                    print(f"    Retry-After: {headers.get('Retry-After', 'N/A')} seconds")
                    break
                else:
                    limit = headers.get("X-RateLimit-Limit", "N/A")
                    remaining = headers.get("X-RateLimit-Remaining", "N/A")
                    if i % 10 == 0:
                        print(
                            f"  Request {i+1}: ✅ {status} (Limit: {limit}, Remaining: {remaining})"
                        )

                responses.append(status)
                await asyncio.sleep(0.05)  # Small delay between requests

            except Exception as e:
                print(f"  Request {i+1}: ⚠️  Error: {e}")

        rate_limited = responses.count(429)
        successful = responses.count(200) + responses.count(404)

        print(f"\n  Summary:")
        print(f"    Total requests: {len(responses)}")
        print(f"    Successful: {successful}")
        print(f"    Rate limited: {rate_limited}")

        # Test 2: Burst requests
        print("\n📊 Test 2: Burst Requests (10 simultaneous)")
        tasks = []
        for i in range(10):
            task = client.get(
                "/api/v1/blueprints", headers={"X-Forwarded-For": f"192.168.1.{i}"}  # Different IPs
            )
            tasks.append(task)

        burst_responses = await asyncio.gather(*tasks, return_exceptions=True)

        burst_success = sum(
            1
            for r in burst_responses
            if not isinstance(r, Exception) and r.status_code in [200, 404]
        )
        burst_limited = sum(
            1 for r in burst_responses if not isinstance(r, Exception) and r.status_code == 429
        )

        print(f"  Burst success: {burst_success}/10")
        print(f"  Burst limited: {burst_limited}/10")


async def test_metrics_collection():
    """Test metrics are being collected properly."""
    print("\n\n📈 Testing Metrics Collection...")
    print("=" * 60)

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Generate some traffic
        print("\n  Generating traffic...")
        for _ in range(20):
            try:
                await client.get("/api/v1/blueprints")
            except:
                pass

        # Check Prometheus metrics
        print("\n📊 Prometheus Metrics Endpoint (/metrics)")
        try:
            response = await client.get("/metrics")
            if response.status_code == 200:
                metrics_text = response.text

                # Count different metric types
                http_metrics = metrics_text.count("http_requests_total")
                llm_metrics = metrics_text.count("llm_requests_total")
                rate_limit_metrics = metrics_text.count("rate_limit_hits_total")

                print(f"  ✅ Metrics endpoint accessible")
                print(f"  HTTP metrics found: {http_metrics > 0}")
                print(f"  LLM metrics found: {llm_metrics > 0}")
                print(f"  Rate limit metrics found: {rate_limit_metrics > 0}")

                # Show sample metrics
                lines = metrics_text.split("\n")
                print("\n  Sample metrics (first 10 counters):")
                counter_count = 0
                for line in lines:
                    if "http_requests_total{" in line or "rate_limit" in line:
                        print(f"    {line}")
                        counter_count += 1
                        if counter_count >= 10:
                            break
            else:
                print(f"  ❌ Failed to fetch metrics: {response.status_code}")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")

        # Check monitoring endpoints
        print("\n📊 Monitoring Endpoints")

        # Metrics summary
        try:
            response = await client.get("/api/v1/monitoring/metrics/summary")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ /api/v1/monitoring/metrics/summary")
                print(f"    {data}")
            else:
                print(f"  ⚠️  /api/v1/monitoring/metrics/summary returned {response.status_code}")
        except Exception as e:
            print(f"  ⚠️  Error fetching metrics summary: {e}")

        # Rate limit stats
        try:
            response = await client.get("/api/v1/monitoring/rate-limit/stats")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ /api/v1/monitoring/rate-limit/stats")
                print(f"    {data}")
            else:
                print(f"  ⚠️  /api/v1/monitoring/rate-limit/stats returned {response.status_code}")
        except Exception as e:
            print(f"  ⚠️  Error fetching rate limit stats: {e}")


async def test_performance():
    """Test performance under load."""
    print("\n\n⚡ Performance Testing...")
    print("=" * 60)

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Test latency with middleware
        print("\n📊 Latency Test (100 requests)")
        latencies = []

        for i in range(100):
            start = time.time()
            try:
                response = await client.get(
                    "/api/v1/blueprints", headers={"X-Forwarded-For": f"192.168.100.{i % 50}"}
                )
                latency = (time.time() - start) * 1000  # Convert to ms
                latencies.append(latency)
            except Exception as e:
                pass

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

            print(f"  Average latency: {avg_latency:.2f}ms")
            print(f"  Min latency: {min_latency:.2f}ms")
            print(f"  Max latency: {max_latency:.2f}ms")
            print(f"  P95 latency: {p95_latency:.2f}ms")

            # Check middleware overhead
            middleware_overhead = avg_latency - 10  # Assuming ~10ms base latency
            print(f"\n  Estimated middleware overhead: ~{middleware_overhead:.2f}ms")
            if middleware_overhead < 5:
                print(f"  ✅ Excellent performance (<5ms overhead)")
            elif middleware_overhead < 10:
                print(f"  ✅ Good performance (<10ms overhead)")
            else:
                print(f"  ⚠️  High overhead (>{middleware_overhead:.0f}ms)")


async def test_end_to_end():
    """End-to-end integration test."""
    print("\n\n🔄 End-to-End Integration Test...")
    print("=" * 60)

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        print("\n1️⃣  Making requests to generate metrics...")

        # Make various requests
        endpoints = [
            "/api/v1/blueprints",
            "/api/v1/iprs",
            "/api/v1/templates",
        ]

        for endpoint in endpoints:
            try:
                response = await client.get(endpoint)
                print(f"  {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"  {endpoint}: Error - {e}")

        print("\n2️⃣  Checking metrics were recorded...")

        try:
            response = await client.get("/metrics")
            if response.status_code == 200 and "http_requests_total" in response.text:
                print(f"  ✅ HTTP metrics recorded")
            else:
                print(f"  ⚠️  HTTP metrics not found")
        except Exception as e:
            print(f"  ❌ Error: {e}")

        print("\n3️⃣  Testing rate limiting...")

        # Rapid fire requests
        limited_count = 0
        for i in range(100):
            try:
                response = await client.get(
                    "/api/v1/blueprints", headers={"X-Forwarded-For": "10.0.0.1"}
                )
                if response.status_code == 429:
                    limited_count += 1
            except:
                pass

        if limited_count > 0:
            print(f"  ✅ Rate limiting active ({limited_count}/100 requests limited)")
        else:
            print(f"  ⚠️  No rate limiting detected (may need higher request rate)")

        print("\n4️⃣  Checking rate limit headers...")

        try:
            response = await client.get("/api/v1/blueprints")
            headers = response.headers

            has_limit = "X-RateLimit-Limit" in headers
            has_remaining = "X-RateLimit-Remaining" in headers
            has_reset = "X-RateLimit-Reset" in headers

            print(
                f"  X-RateLimit-Limit: {'✅' if has_limit else '❌'} {headers.get('X-RateLimit-Limit', 'Missing')}"
            )
            print(
                f"  X-RateLimit-Remaining: {'✅' if has_remaining else '❌'} {headers.get('X-RateLimit-Remaining', 'Missing')}"
            )
            print(
                f"  X-RateLimit-Reset: {'✅' if has_reset else '❌'} {headers.get('X-RateLimit-Reset', 'Missing')}"
            )
        except Exception as e:
            print(f"  ❌ Error: {e}")

        print("\n✅ End-to-end test complete!")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  ALMA Rate Limiting & Metrics - Load Testing Suite")
    print("=" * 60)
    print("\n⚠️  Make sure the server is running: python run_server.py")
    print("\nPress Ctrl+C to stop\n")

    await asyncio.sleep(2)

    try:
        await test_rate_limiting()
        await test_metrics_collection()
        await test_performance()
        await test_end_to_end()

        print("\n" + "=" * 60)
        print("  ✅ All Tests Complete!")
        print("=" * 60)

        print("\n📚 Next Steps:")
        print("  1. Check Prometheus: http://localhost:9090")
        print("  2. Check Grafana dashboard: http://localhost:3000")
        print("  3. View raw metrics: curl http://localhost:8000/metrics")
        print(
            "  4. Check monitoring API: curl http://localhost:8000/api/v1/monitoring/metrics/summary"
        )

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")


if __name__ == "__main__":
    asyncio.run(main())
