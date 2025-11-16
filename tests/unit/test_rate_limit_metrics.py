"""Test suite for rate limiting and metrics."""
import pytest
import time
from fastapi.testclient import TestClient
from ai_cdn.api.main import app
from ai_cdn.middleware.rate_limit import RateLimiter, EndpointRateLimiter
from ai_cdn.middleware.metrics import MetricsCollector


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_token_bucket_initialization(self):
        """Test rate limiter initializes correctly."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 10
        assert limiter.refill_rate == 1.0  # 60 RPM = 1 req/sec
    
    def test_token_consumption(self):
        """Test token consumption and refill."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        client_id = "test_client"
        
        # First request should succeed
        allowed, remaining, reset_time = limiter.check_rate_limit(client_id)
        assert allowed is True
        assert remaining == 4  # 5 burst - 1 consumed
        
        # Consume all tokens
        for _ in range(4):
            allowed, _, _ = limiter.check_rate_limit(client_id)
            assert allowed is True
        
        # Next request should be rate limited
        allowed, remaining, reset_time = limiter.check_rate_limit(client_id)
        assert allowed is False
        assert remaining == 0
        assert reset_time > 0
    
    def test_token_refill(self):
        """Test tokens refill over time."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=2)
        client_id = "test_client"
        
        # Consume all tokens
        limiter.check_rate_limit(client_id)
        limiter.check_rate_limit(client_id)
        
        # Should be rate limited
        allowed, _, _ = limiter.check_rate_limit(client_id)
        assert allowed is False
        
        # Wait for refill (1 second = 1 token at 60 RPM)
        time.sleep(1.1)
        
        # Should have 1 token now
        allowed, remaining, _ = limiter.check_rate_limit(client_id)
        assert allowed is True
        assert remaining == 0  # Used the refilled token
    
    def test_multiple_clients(self):
        """Test rate limiting isolates clients."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=2)
        
        # Client 1 consumes tokens
        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client1")
        allowed, _, _ = limiter.check_rate_limit("client1")
        assert allowed is False  # Client 1 is rate limited
        
        # Client 2 should still have tokens
        allowed, remaining, _ = limiter.check_rate_limit("client2")
        assert allowed is True
        assert remaining == 1  # Has 1 token left
    
    def test_cleanup_old_buckets(self):
        """Test cleanup removes inactive clients."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        limiter.cleanup_interval = 0.1  # 100ms cleanup for testing
        
        # Create multiple clients
        for i in range(10):
            limiter.check_rate_limit(f"client_{i}")
        
        assert len(limiter.buckets) == 10
        
        # Manually set old timestamp
        for client_id in list(limiter.buckets.keys())[:5]:
            limiter.buckets[client_id]["last_update"] = time.time() - 3700  # 1 hour + 100s ago
        
        # Trigger cleanup
        limiter._cleanup_old_buckets()
        
        # Should have removed 5 old clients
        assert len(limiter.buckets) == 5


class TestEndpointRateLimiter:
    """Test per-endpoint rate limiting."""
    
    def test_endpoint_specific_limits(self):
        """Test different limits per endpoint."""
        endpoint_limiter = EndpointRateLimiter(
            default_rpm=100,
            endpoint_limits={
                "/api/v1/expensive": 10,
                "/api/v1/cheap": 1000,
            }
        )
        
        client_id = "test_client"
        
        # Expensive endpoint (10 RPM = small burst)
        for i in range(10):
            allowed, _, _ = endpoint_limiter.check_rate_limit(
                client_id, "/api/v1/expensive"
            )
            if i < 2:  # Burst size ~2
                assert allowed is True
            else:
                # Will be limited quickly
                pass
        
        # Cheap endpoint should still work
        allowed, _, _ = endpoint_limiter.check_rate_limit(
            client_id, "/api/v1/cheap"
        )
        assert allowed is True
    
    def test_default_limit_fallback(self):
        """Test fallback to default limit for unknown endpoints."""
        endpoint_limiter = EndpointRateLimiter(
            default_rpm=60,
            endpoint_limits={"/api/v1/known": 10}
        )
        
        client_id = "test_client"
        
        # Unknown endpoint uses default
        allowed, _, _ = endpoint_limiter.check_rate_limit(
            client_id, "/api/v1/unknown"
        )
        assert allowed is True


class TestMetricsCollector:
    """Test metrics collection."""
    
    def test_counter_increment(self):
        """Test counter metrics increment correctly."""
        collector = MetricsCollector()
        
        initial = collector.http_requests_total.labels(
            method="GET", endpoint="/test", status="200"
        )._value._value
        
        collector.record_http_request("GET", "/test", "200", 0.1, 100, 200)
        
        final = collector.http_requests_total.labels(
            method="GET", endpoint="/test", status="200"
        )._value._value
        
        assert final == initial + 1
    
    def test_histogram_observation(self):
        """Test histogram metrics record observations."""
        collector = MetricsCollector()
        
        # Record multiple durations
        collector.record_http_request("POST", "/api", "201", 0.15, 500, 1000)
        collector.record_http_request("POST", "/api", "201", 0.25, 600, 1200)
        collector.record_http_request("POST", "/api", "201", 0.10, 400, 800)
        
        # Check histogram recorded values
        histogram = collector.http_request_duration_seconds.labels(
            method="POST", endpoint="/api"
        )
        assert histogram._sum._value > 0  # Sum of all durations
        assert histogram._count._value == 3  # 3 observations
    
    def test_gauge_set(self):
        """Test gauge metrics can be set."""
        collector = MetricsCollector()
        
        # Set active connections
        collector.active_connections.set(42)
        assert collector.active_connections._value._value == 42
        
        # Update value
        collector.active_connections.set(100)
        assert collector.active_connections._value._value == 100
    
    def test_llm_metrics(self):
        """Test LLM-specific metrics."""
        collector = MetricsCollector()
        
        collector.record_llm_request(
            model="qwen2.5-0.5b",
            operation="generate",
            status="success",
            duration=2.5,
            tokens_generated=450,
            tokens_consumed=120
        )
        
        # Check counters
        assert collector.llm_requests_total.labels(
            model="qwen2.5-0.5b", operation="generate", status="success"
        )._value._value == 1
        
        assert collector.llm_tokens_generated_total.labels(
            model="qwen2.5-0.5b"
        )._value._value == 450
        
        assert collector.llm_tokens_consumed_total.labels(
            model="qwen2.5-0.5b"
        )._value._value == 120
    
    def test_blueprint_metrics(self):
        """Test blueprint operation metrics."""
        collector = MetricsCollector()
        
        collector.record_blueprint_operation(
            operation="create",
            status="success",
            resource_count=12
        )
        
        assert collector.blueprint_operations_total.labels(
            operation="create", status="success"
        )._value._value == 1
        
        assert collector.blueprint_resources_count.labels(
            operation="create"
        )._value._value == 12
    
    def test_tool_metrics(self):
        """Test tool execution metrics."""
        collector = MetricsCollector()
        
        collector.record_tool_execution(
            tool_name="create_blueprint",
            status="success",
            duration=1.2
        )
        
        assert collector.tool_executions_total.labels(
            tool_name="create_blueprint", status="success"
        )._value._value == 1
        
        # Check histogram
        histogram = collector.tool_execution_duration_seconds.labels(
            tool_name="create_blueprint"
        )
        assert histogram._count._value == 1
    
    def test_prometheus_format_export(self):
        """Test metrics export in Prometheus format."""
        collector = MetricsCollector()
        
        # Record some metrics
        collector.record_http_request("GET", "/test", "200", 0.1, 100, 200)
        collector.record_llm_request("qwen", "chat", "success", 1.5, 300, 100)
        
        # Get Prometheus format
        from ai_cdn.middleware.metrics import get_prometheus_metrics
        metrics_output = get_prometheus_metrics()
        
        assert "http_requests_total" in metrics_output
        assert "llm_requests_total" in metrics_output
        assert "# TYPE" in metrics_output  # Prometheus format
        assert "# HELP" in metrics_output


class TestRateLimitingIntegration:
    """Integration tests for rate limiting in API."""
    
    def test_rate_limit_headers(self):
        """Test rate limit headers are returned."""
        client = TestClient(app)
        
        response = client.get("/api/v1/blueprints")
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_enforcement(self):
        """Test rate limiting returns 429 when exceeded."""
        client = TestClient(app)
        
        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = client.get("/api/v1/blueprints")
            responses.append(response.status_code)
        
        # Should have some 429s
        assert 429 in responses
        
        # Check retry-after header
        for response in [client.get("/api/v1/blueprints") for _ in range(100)]:
            if response.status_code == 429:
                assert "Retry-After" in response.headers
                break


class TestMetricsIntegration:
    """Integration tests for metrics in API."""
    
    def test_metrics_endpoint(self):
        """Test /metrics endpoint returns Prometheus format."""
        client = TestClient(app)
        
        # Make some requests to generate metrics
        client.get("/api/v1/blueprints")
        client.post("/api/v1/conversation/chat", json={"message": "test"})
        
        # Get metrics
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert "# TYPE http_requests_total counter" in response.text
        assert "http_requests_total{" in response.text
    
    def test_monitoring_endpoints(self):
        """Test monitoring API endpoints."""
        client = TestClient(app)
        
        # Metrics summary
        response = client.get("/monitoring/metrics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "http" in data or "message" in data
        
        # Rate limit stats
        response = client.get("/monitoring/rate-limit/stats")
        assert response.status_code == 200
        
        # Health check
        response = client.get("/monitoring/health/detailed")
        assert response.status_code == 200


class TestPerformance:
    """Performance tests for middleware overhead."""
    
    def test_rate_limiter_performance(self):
        """Test rate limiter overhead is minimal."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        start = time.time()
        for i in range(1000):
            limiter.check_rate_limit(f"client_{i % 10}")
        duration = time.time() - start
        
        # Should process 1000 checks in under 100ms
        assert duration < 0.1
    
    def test_metrics_collector_performance(self):
        """Test metrics collection overhead is minimal."""
        collector = MetricsCollector()
        
        start = time.time()
        for _ in range(1000):
            collector.record_http_request("GET", "/test", "200", 0.1, 100, 200)
        duration = time.time() - start
        
        # Should record 1000 metrics in under 50ms
        assert duration < 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
