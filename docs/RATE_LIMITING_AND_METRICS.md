# Rate Limiting & Metrics - Documentation

## Overview

ALMA now includes production-grade rate limiting and comprehensive metrics collection. These features provide abuse prevention, fair usage enforcement, and deep observability into system behavior.

---

## Rate Limiting

### Architecture

Token bucket algorithm with per-client and per-endpoint tracking:

- **Tokens**: Each client gets a bucket with configurable capacity
- **Refill**: Tokens automatically refill at a constant rate (RPM)
- **Burst Handling**: Burst size allows temporary spikes beyond average rate
- **Cleanup**: Inactive clients are removed after 1 hour to prevent memory leaks

### Configuration

Default limits in `alma/middleware/rate_limit.py`:

```python
# Global defaults
DEFAULT_RPM = 60           # 60 requests per minute
DEFAULT_BURST_SIZE = 10    # Allow bursts of 10 requests

# Per-endpoint limits (override global)
ENDPOINT_LIMITS = {
    "/api/v1/conversation/chat-stream": 20,           # LLM streaming
    "/api/v1/blueprints/generate-blueprint": 30,      # Blueprint generation
    "/api/v1/tools/execute": 40,                      # Tool execution
    "/api/v1/blueprints": 100,                        # CRUD operations
}
```

### Response Headers

Rate limit information in every response:

```
X-RateLimit-Limit: 60          # Max requests per minute
X-RateLimit-Remaining: 45      # Requests remaining
X-RateLimit-Reset: 1642345678  # Unix timestamp when limit resets
```

When rate limited (HTTP 429):

```
Retry-After: 30  # Seconds until next token available
```

### Customization

Modify limits in code or via environment variables:

```python
# In alma/middleware/rate_limit.py
rate_limiter = RateLimiter(
    requests_per_minute=120,  # Double the default
    burst_size=20             # Larger burst allowance
)

# Per-endpoint
endpoint_limiter = EndpointRateLimiter(
    "/api/v1/my-expensive-endpoint": 10  # Very restrictive
)
```

### Monitoring

Check rate limit statistics:

```bash
curl http://localhost:8000/monitoring/rate-limit/stats
```

Response:

```json
{
  "total_clients": 45,
  "rate_limited_clients": 3,
  "endpoint_stats": {
    "/api/v1/conversation/chat-stream": {
      "limit": 20,
      "active_clients": 12,
      "total_requests": 2450,
      "rejected_requests": 15
    }
  }
}
```

---

## Metrics Collection

### Prometheus Integration

ALMA exposes Prometheus-compatible metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

### Metric Types

#### HTTP Metrics

- `http_requests_total` (Counter): Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` (Histogram): Request latency distribution
- `http_request_size_bytes` (Histogram): Request body size distribution
- `http_response_size_bytes` (Histogram): Response body size distribution

#### LLM Metrics

- `llm_requests_total` (Counter): LLM requests by model, operation, status
- `llm_generation_duration_seconds` (Histogram): LLM generation time
- `llm_tokens_generated_total` (Counter): Total tokens generated
- `llm_tokens_consumed_total` (Counter): Total tokens consumed (input)

#### Blueprint Metrics

- `blueprint_operations_total` (Counter): Blueprint CRUD operations
- `blueprint_resources_count` (Gauge): Resources per blueprint
- `blueprint_validation_errors_total` (Counter): Validation failures

#### Deployment Metrics

- `deployment_operations_total` (Counter): Deployment create/update/delete
- `deployment_duration_seconds` (Histogram): Time to deploy
- `active_deployments` (Gauge): Currently running deployments

#### Tool Metrics

- `tool_executions_total` (Counter): Tool calls by tool name, status
- `tool_execution_duration_seconds` (Histogram): Tool execution time

#### Rate Limiting Metrics

- `rate_limit_hits_total` (Counter): Rate limit violations by endpoint

#### System Metrics

- `active_connections` (Gauge): Current WebSocket/HTTP connections
- `database_connections` (Gauge): Active DB connections
- `cache_hit_rate` (Gauge): Cache effectiveness

### Human-Readable API

For quick debugging, use the monitoring endpoints:

```bash
# Metrics summary
curl http://localhost:8000/monitoring/metrics/summary

# System overview
curl http://localhost:8000/monitoring/stats/overview

# Health check
curl http://localhost:8000/monitoring/health/detailed
```

Example response:

```json
{
  "http": {
    "total_requests": 15234,
    "avg_latency_ms": 145,
    "error_rate": 0.02
  },
  "llm": {
    "total_generations": 1250,
    "avg_tokens_per_request": 450,
    "total_tokens_generated": 562500
  },
  "blueprints": {
    "total_created": 340,
    "avg_resources": 8,
    "validation_errors": 12
  }
}
```

---

## Visualization with Grafana

### Quick Start

1. **Start the stack:**

```bash
docker-compose -f docker-compose.metrics.yml up -d
```

Services:
- ALMA API: `http://localhost:8000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin)

2. **Dashboard auto-loads** at Grafana → Dashboards → ALMA Metrics

### Dashboard Panels

The auto-generated dashboard includes:

1. **Request Rate**: Requests per second by endpoint
2. **Response Time**: P50/P90/P99 latency percentiles
3. **Error Rate**: HTTP 4xx/5xx over time
4. **LLM Performance**: Generation time and token throughput
5. **Blueprint Operations**: Create/validate/deploy rates
6. **Rate Limit Hits**: Rate limiting violations
7. **Active Connections**: WebSocket and HTTP connections
8. **Tool Executions**: Tool usage distribution
9. **System Health**: CPU, memory, DB connections

### Custom Dashboards

Create custom panels with PromQL queries:

```promql
# Average response time by endpoint
rate(http_request_duration_seconds_sum[5m]) / 
rate(http_request_duration_seconds_count[5m])

# LLM tokens per second
rate(llm_tokens_generated_total[1m])

# Blueprint validation failure rate
rate(blueprint_validation_errors_total[5m]) / 
rate(blueprint_operations_total{operation="validate"}[5m])

# Top rate-limited endpoints
topk(5, rate(rate_limit_hits_total[5m]))
```

---

## Alerting

### Prometheus Alerts

Create `config/alerts/ALMA.yml`:

```yaml
groups:
  - name: ALMA
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "{{ $value }}% of requests failing"

      # Slow LLM responses
      - alert: SlowLLMGeneration
        expr: histogram_quantile(0.95, llm_generation_duration_seconds) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LLM generation slow"
          description: "P95 latency {{ $value }}s"

      # Rate limiting spike
      - alert: RateLimitSpike
        expr: rate(rate_limit_hits_total[5m]) > 10
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Rate limiting spike"
          description: "{{ $value }} requests/sec being rate limited"

      # Too many active deployments
      - alert: DeploymentBacklog
        expr: active_deployments > 50
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Deployment backlog building"
          description: "{{ $value }} active deployments"
```

### Grafana Alerts

Set thresholds directly in dashboard panels:
1. Edit panel → Alert tab
2. Define condition (e.g., `avg() > 5`)
3. Configure notification channel (Slack, PagerDuty, etc.)

---

## Performance Impact

### Rate Limiting Overhead

- **Memory**: ~200 bytes per active client (10K clients = 2MB)
- **CPU**: O(1) token calculation, negligible overhead
- **Latency**: <1ms per request

### Metrics Collection Overhead

- **Memory**: ~5MB for metric registry (grows slowly with label cardinality)
- **CPU**: Counter increment ~50ns, histogram observation ~500ns
- **Latency**: <0.5ms per request (middleware overhead)

### Recommendations

- **Keep label cardinality low**: Avoid high-cardinality labels (user IDs, timestamps)
- **Use histograms sparingly**: Histograms are more expensive than counters
- **Aggregate in Prometheus**: Don't pre-aggregate in application code
- **Set retention limits**: Prometheus default 15 days, configure based on disk space

---

## Production Checklist

- [ ] Configure appropriate rate limits per endpoint
- [ ] Set up Prometheus scraping (every 10-15s)
- [ ] Create Grafana dashboards for key metrics
- [ ] Define alert rules for critical thresholds
- [ ] Configure notification channels (Slack, PagerDuty)
- [ ] Set Prometheus retention policy
- [ ] Enable authentication for Prometheus/Grafana endpoints
- [ ] Monitor metrics collection overhead
- [ ] Document custom metrics and their meaning
- [ ] Set up log aggregation for detailed debugging

---

## Troubleshooting

### Rate Limiting Not Working

1. Check middleware order in `alma/api/main.py`:
   ```python
   app.middleware("http")(metrics_middleware)  # First
   app.middleware("http")(rate_limit_middleware)  # Second
   ```

2. Verify endpoint limits:
   ```python
   # In rate_limit.py
   ENDPOINT_LIMITS = {...}  # Check your endpoint is listed
   ```

3. Test with curl:
   ```bash
   for i in {1..70}; do curl -w "%{http_code}\n" http://localhost:8000/api/v1/blueprints; done
   # Should see 429 after ~60 requests
   ```

### Metrics Not Appearing

1. Check `/metrics` endpoint:
   ```bash
   curl http://localhost:8000/metrics | grep http_requests_total
   # Should see counter values
   ```

2. Verify Prometheus scraping:
   - Open `http://localhost:9090/targets`
   - `ALMA-api` should be "UP"

3. Check Grafana data source:
   - Settings → Data Sources → Prometheus
   - "Save & Test" should succeed

### Dashboard Empty

1. Generate traffic to create metrics:
   ```bash
   # Make some requests
   curl http://localhost:8000/api/v1/blueprints
   curl http://localhost:8000/api/v1/conversation/chat -X POST -H "Content-Type: application/json" -d '{"message":"test"}'
   ```

2. Check time range in Grafana (top right)
   - Set to "Last 5 minutes"

3. Verify queries in panel editor:
   - Edit panel → Query tab
   - Run query manually

---

## Next Steps

1. **Custom Metrics**: Add application-specific metrics
   ```python
   from alma.middleware.metrics import get_metrics_collector
   
   metrics = get_metrics_collector()
   metrics.custom_counter.labels(operation="my_feature").inc()
   ```

2. **Advanced Rate Limiting**: Implement tiered limits (free/pro/enterprise)
   
3. **Distributed Tracing**: Integrate OpenTelemetry for request tracing

4. **Cost Tracking**: Add metrics for infrastructure costs per deployment

5. **SLO/SLI Monitoring**: Define service level objectives and track them
