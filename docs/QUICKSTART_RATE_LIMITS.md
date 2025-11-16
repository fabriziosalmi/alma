# Quick Start - Testing Rate Limiting & Metrics

This guide helps you quickly verify that rate limiting and metrics are working.

## 1. Start the Application

```bash
# Install dependencies
pip install -e .

# Run the server
python run_server.py
```

## 2. Test Rate Limiting

### Test Default Rate Limit

Make rapid requests to see rate limiting in action:

```bash
# Bash script to make 70 requests
for i in {1..70}; do
  echo "Request $i:"
  curl -w "Status: %{http_code}\n" \
       -H "X-Client-IP: test-client-1" \
       http://localhost:8000/api/v1/blueprints
done
```

**Expected behavior:**
- First ~60 requests: HTTP 200 (or 404 if no blueprints)
- After ~60 requests: HTTP 429 (Too Many Requests)
- Response headers show rate limit info:
  ```
  X-RateLimit-Limit: 60
  X-RateLimit-Remaining: 45
  X-RateLimit-Reset: 1234567890
  Retry-After: 30  (only on 429 responses)
  ```

### Test Per-Endpoint Limits

LLM streaming endpoint has stricter limit (20 RPM):

```bash
# Should hit rate limit faster
for i in {1..30}; do
  echo "Stream request $i:"
  curl -w "Status: %{http_code}\n" \
       -X POST \
       -H "Content-Type: application/json" \
       -d '{"message":"test"}' \
       http://localhost:8000/api/v1/conversation/chat-stream
done
```

**Expected:** HTTP 429 after ~20 requests

## 3. Test Metrics Collection

### View Prometheus Metrics

```bash
# Get all metrics
curl http://localhost:8000/metrics

# Filter for HTTP metrics
curl http://localhost:8000/metrics | grep http_requests_total

# Filter for LLM metrics
curl http://localhost:8000/metrics | grep llm_
```

**Expected output:**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/blueprints",status="200"} 45.0
http_requests_total{method="POST",endpoint="/api/v1/conversation/chat",status="200"} 12.0
...
```

### View Human-Readable Metrics

```bash
# Metrics summary
curl http://localhost:8000/monitoring/metrics/summary | jq

# Rate limit stats
curl http://localhost:8000/monitoring/rate-limit/stats | jq

# System health
curl http://localhost:8000/monitoring/health/detailed | jq
```

**Example output:**
```json
{
  "http": {
    "total_requests": 245,
    "avg_latency_ms": 145,
    "error_rate": 0.02
  },
  "llm": {
    "total_generations": 32,
    "avg_tokens_per_request": 450
  }
}
```

## 4. Start Full Metrics Stack (Optional)

For full Prometheus + Grafana visualization:

```bash
# Start all services
docker-compose -f docker-compose.metrics.yml up -d

# Check status
docker-compose -f docker-compose.metrics.yml ps
```

**Access:**
- AI-CDN API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### View Dashboard

1. Open Grafana: http://localhost:3000
2. Login: admin/admin
3. Go to Dashboards → AI-CDN Metrics
4. Dashboard auto-loads with 9 panels

**Generate traffic** to see live data:

```bash
# Generate varied traffic
for i in {1..100}; do
  curl http://localhost:8000/api/v1/blueprints &
  curl -X POST http://localhost:8000/api/v1/conversation/chat \
       -H "Content-Type: application/json" \
       -d '{"message":"test"}' &
  sleep 0.1
done
```

## 5. Verify Everything Works

### Checklist

- [ ] Rate limiting kicks in after ~60 requests/minute
- [ ] `/metrics` endpoint returns Prometheus format
- [ ] `/monitoring/metrics/summary` shows request counts
- [ ] Rate limit headers appear in responses
- [ ] HTTP 429 includes `Retry-After` header
- [ ] Prometheus scrapes metrics successfully (check http://localhost:9090/targets)
- [ ] Grafana dashboard displays data

### Troubleshooting

**Problem:** No rate limiting happening

```bash
# Check middleware is loaded
curl http://localhost:8000/api/v1/blueprints -v | grep X-RateLimit

# Should see headers like:
# X-RateLimit-Limit: 60
# X-RateLimit-Remaining: 59
```

**Problem:** Metrics empty

```bash
# Generate traffic first
curl http://localhost:8000/api/v1/blueprints

# Then check
curl http://localhost:8000/metrics | grep http_requests_total
```

**Problem:** Grafana shows no data

1. Check Prometheus targets: http://localhost:9090/targets
   - `ai-cdn-api` should be "UP"
2. Generate traffic to create metrics
3. Set Grafana time range to "Last 5 minutes"

## 6. Advanced Testing

### Load Testing

```bash
# Install hey (HTTP load generator)
brew install hey  # macOS
# or: go install github.com/rakyll/hey@latest

# Load test with 10 concurrent users, 1000 requests
hey -n 1000 -c 10 http://localhost:8000/api/v1/blueprints

# Check rate limiting behavior
curl http://localhost:8000/monitoring/rate-limit/stats | jq
```

### Custom Metrics

Test custom metrics collection in Python:

```python
from ai_cdn.middleware.metrics import get_metrics_collector

collector = get_metrics_collector()

# Record custom event
collector.http_requests_total.labels(
    method="CUSTOM",
    endpoint="/test",
    status="200"
).inc()

# Check it appears
import requests
metrics = requests.get("http://localhost:8000/metrics").text
assert 'method="CUSTOM"' in metrics
```

## Next Steps

- **Customize limits**: Edit `ai_cdn/middleware/rate_limit.py`
- **Add metrics**: Use `MetricsCollector` in your code
- **Create alerts**: Add Prometheus alerting rules
- **Production deploy**: Use real Prometheus + Grafana instances

See full documentation: [docs/RATE_LIMITING_AND_METRICS.md](../docs/RATE_LIMITING_AND_METRICS.md)
