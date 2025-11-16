# API Reference - AI-CDN

Complete API documentation for AI-CDN Infrastructure as Conversation platform.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, AI-CDN uses IP-based rate limiting. Future versions will include:
- API Key authentication
- OAuth2 / JWT tokens
- Role-based access control (RBAC)

---

## Blueprints API

Manage infrastructure blueprints (YAML configurations).

### List Blueprints

```http
GET /api/v1/blueprints
```

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Max records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "version": "1.0",
    "name": "web-app-production",
    "description": "Production web application infrastructure",
    "resources": [...],
    "metadata": {...},
    "created_at": "2025-11-16T10:30:00Z",
    "updated_at": "2025-11-16T10:30:00Z"
  }
]
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Database error

---

### Get Blueprint

```http
GET /api/v1/blueprints/{blueprint_id}
```

**Path Parameters:**
- `blueprint_id` (integer): Blueprint ID

**Response:**
```json
{
  "id": 1,
  "version": "1.0",
  "name": "web-app-production",
  "description": "Production web application infrastructure",
  "resources": [
    {
      "name": "web-server-1",
      "type": "vm",
      "specs": {
        "cpu": 4,
        "memory": "8GB",
        "disk": "100GB"
      }
    }
  ],
  "metadata": {
    "environment": "production",
    "owner": "devops-team"
  },
  "created_at": "2025-11-16T10:30:00Z",
  "updated_at": "2025-11-16T10:30:00Z"
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Blueprint not found
- `500 Internal Server Error`: Database error

---

### Create Blueprint

```http
POST /api/v1/blueprints
```

**Request Body:**
```json
{
  "version": "1.0",
  "name": "web-app-production",
  "description": "Production web application infrastructure",
  "resources": [
    {
      "name": "web-server-1",
      "type": "vm",
      "specs": {
        "cpu": 4,
        "memory": "8GB",
        "disk": "100GB"
      }
    }
  ],
  "metadata": {
    "environment": "production",
    "owner": "devops-team"
  }
}
```

**Response:** Same as Get Blueprint

**Status Codes:**
- `201 Created`: Blueprint created successfully
- `400 Bad Request`: Invalid blueprint format
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Database error

---

### Update Blueprint

```http
PUT /api/v1/blueprints/{blueprint_id}
```

**Path Parameters:**
- `blueprint_id` (integer): Blueprint ID

**Request Body:** Same as Create Blueprint

**Response:** Updated blueprint

**Status Codes:**
- `200 OK`: Updated successfully
- `404 Not Found`: Blueprint not found
- `422 Unprocessable Entity`: Validation error

---

### Delete Blueprint

```http
DELETE /api/v1/blueprints/{blueprint_id}
```

**Path Parameters:**
- `blueprint_id` (integer): Blueprint ID

**Response:**
```json
{
  "message": "Blueprint deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Deleted successfully
- `404 Not Found`: Blueprint not found

---

### Generate Blueprint (AI)

```http
POST /api/v1/blueprints/generate-blueprint
```

**Request Body:**
```json
{
  "description": "I need a highly available web application with 3 servers, load balancer, and PostgreSQL database",
  "constraints": {
    "max_cost": 500,
    "region": "us-east-1",
    "environment": "production"
  }
}
```

**Response:**
```json
{
  "version": "1.0",
  "name": "ha-web-application",
  "description": "High availability web application infrastructure",
  "resources": [...],
  "metadata": {
    "generated_by": "ai-cdn-llm",
    "estimated_cost": 450,
    "complexity_score": 7.5
  }
}
```

**Status Codes:**
- `200 OK`: Blueprint generated
- `400 Bad Request`: Invalid input
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: LLM error

---

### Generate Blueprint Stream (AI)

```http
POST /api/v1/blueprints/generate-blueprint-stream
```

**Request Body:** Same as Generate Blueprint

**Response:** Server-Sent Events (SSE) stream

```
data: {"type": "thinking", "content": "Analyzing requirements..."}

data: {"type": "progress", "content": "Designing network topology..."}

data: {"type": "resource", "content": {"name": "web-server-1", "type": "vm"}}

data: {"type": "complete", "blueprint": {...}}
```

**Status Codes:**
- `200 OK`: Stream started
- `400 Bad Request`: Invalid input
- `429 Too Many Requests`: Rate limit exceeded

---

## Conversation API

Natural language interface for infrastructure management.

### Chat

```http
POST /api/v1/conversation/chat
```

**Request Body:**
```json
{
  "message": "Create a Kubernetes cluster with 3 nodes",
  "context": {
    "conversation_id": "conv-123",
    "previous_blueprints": [1, 2, 3]
  }
}
```

**Response:**
```json
{
  "response": "I'll create a Kubernetes cluster with 3 worker nodes. Here's the blueprint...",
  "blueprint": {...},
  "suggested_actions": [
    "Review blueprint",
    "Estimate costs",
    "Deploy infrastructure"
  ]
}
```

**Status Codes:**
- `200 OK`: Response generated
- `400 Bad Request`: Invalid message
- `429 Too Many Requests`: Rate limit exceeded (20 RPM)

---

### Chat Stream

```http
POST /api/v1/conversation/chat-stream
```

**Request Body:** Same as Chat

**Response:** SSE stream with real-time tokens

```
data: {"type": "token", "content": "I'll"}

data: {"type": "token", "content": " create"}

data: {"type": "token", "content": " a"}

data: {"type": "complete", "full_response": "I'll create a Kubernetes cluster..."}
```

**Status Codes:**
- `200 OK`: Stream started
- `429 Too Many Requests`: Rate limit exceeded (20 RPM)

---

## Infrastructure Pull Requests (IPR)

Review and approve infrastructure changes.

### List IPRs

```http
GET /api/v1/iprs
```

**Query Parameters:**
- `skip` (integer): Pagination offset
- `limit` (integer): Max results
- `status` (string): Filter by status (pending, approved, rejected, deployed)

**Response:**
```json
[
  {
    "id": 1,
    "title": "Add load balancer to production",
    "description": "Scale web tier with ALB",
    "blueprint_id": 5,
    "status": "pending",
    "created_by": "john.doe",
    "created_at": "2025-11-16T10:00:00Z"
  }
]
```

---

### Create IPR

```http
POST /api/v1/iprs
```

**Request Body:**
```json
{
  "title": "Add Redis cache cluster",
  "description": "Improve performance with distributed caching",
  "blueprint_id": 10,
  "changes_summary": {
    "added": ["redis-cluster-1", "redis-cluster-2"],
    "removed": [],
    "modified": ["web-server-config"]
  }
}
```

**Response:** Created IPR object

**Status Codes:**
- `201 Created`: IPR created
- `400 Bad Request`: Invalid data
- `404 Not Found`: Blueprint not found

---

### Review IPR

```http
POST /api/v1/iprs/{ipr_id}/review
```

**Request Body:**
```json
{
  "action": "approve",
  "comments": "LGTM, ready for deployment",
  "reviewer": "jane.smith"
}
```

**Actions:**
- `approve`: Approve changes
- `reject`: Reject changes
- `request_changes`: Request modifications

**Response:** Updated IPR with new status

---

### Deploy IPR

```http
POST /api/v1/iprs/{ipr_id}/deploy
```

**Request Body:**
```json
{
  "engine": "proxmox",
  "dry_run": false
}
```

**Response:**
```json
{
  "deployment_id": "deploy-abc123",
  "status": "in_progress",
  "estimated_duration": "15 minutes"
}
```

---

## Tools API

LLM function calling tools for infrastructure operations.

### List Tools

```http
GET /api/v1/tools
```

**Response:**
```json
{
  "tools": [
    {
      "name": "create_blueprint",
      "description": "Create a new infrastructure blueprint",
      "parameters": {...}
    },
    {
      "name": "estimate_resources",
      "description": "Estimate resource requirements",
      "parameters": {...}
    }
  ],
  "count": 13
}
```

---

### Execute Tool

```http
POST /api/v1/tools/execute
```

**Request Body:**
```json
{
  "tool_name": "estimate_resources",
  "parameters": {
    "blueprint_id": 5,
    "usage_pattern": "high_traffic",
    "peak_users": 10000
  }
}
```

**Response:**
```json
{
  "result": {
    "cpu_cores": 48,
    "memory_gb": 128,
    "storage_tb": 2,
    "estimated_cost_monthly": 850
  },
  "execution_time": 0.45,
  "status": "success"
}
```

**Available Tools:**
1. `create_blueprint` - Create new blueprint
2. `validate_blueprint` - Validate blueprint syntax
3. `estimate_resources` - Calculate resource needs
4. `optimize_costs` - Reduce infrastructure costs
5. `security_audit` - Security compliance check
6. `generate_deployment_plan` - Step-by-step deployment
7. `troubleshoot_issue` - Diagnose problems
8. `compare_blueprints` - Diff two blueprints
9. `suggest_architecture` - Architecture recommendations
10. `calculate_capacity` - Capacity planning
11. `migrate_infrastructure` - Migration planning
12. `check_compliance` - Compliance verification
13. `forecast_metrics` - Predictive analytics

**Status Codes:**
- `200 OK`: Tool executed
- `400 Bad Request`: Invalid tool or parameters
- `404 Not Found`: Tool not found
- `429 Too Many Requests`: Rate limit (40 RPM)

---

## Templates API

Pre-built infrastructure templates.

### List Templates

```http
GET /api/v1/templates
```

**Response:**
```json
{
  "templates": [
    {
      "id": "simple-web-app",
      "name": "Simple Web Application",
      "description": "Single server web app",
      "complexity": "low",
      "estimated_cost": "$100-200/month"
    }
  ],
  "count": 10
}
```

**Complexity Levels:**
- `low`: Simple, 1-3 resources
- `medium`: Moderate, 4-10 resources
- `high`: Complex, 11+ resources

---

### Get Template

```http
GET /api/v1/templates/{template_id}
```

**Response:** Full blueprint template

---

### Customize Template

```http
POST /api/v1/templates/{template_id}/customize
```

**Request Body:**
```json
{
  "parameters": {
    "instance_count": 3,
    "cpu_per_instance": 4,
    "memory_per_instance": "8GB",
    "environment": "production"
  }
}
```

**Response:** Customized blueprint ready for deployment

---

## Monitoring API

Metrics, health checks, and rate limit statistics.

### Metrics Summary

```http
GET /api/v1/monitoring/metrics/summary
```

**Response:**
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

### Rate Limit Stats

```http
GET /api/v1/monitoring/rate-limit/stats
```

**Response:**
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

### Health Check

```http
GET /api/v1/monitoring/health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "database": "up",
    "llm_service": "up",
    "cache": "up"
  },
  "uptime_seconds": 345678,
  "version": "0.1.0"
}
```

---

### Prometheus Metrics

```http
GET /metrics
```

**Response:** Prometheus exposition format

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/blueprints",status="200"} 1234.0

# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/blueprints",le="0.1"} 800.0
...
```

---

## Rate Limiting

All endpoints are rate-limited to ensure fair usage.

### Default Limits

- **Global**: 60 requests/minute per IP
- **Burst**: 10 requests (token bucket)

### Per-Endpoint Limits

| Endpoint | Limit (RPM) | Burst | Reason |
|----------|-------------|-------|--------|
| `/conversation/chat-stream` | 20 | 5 | LLM expensive |
| `/blueprints/generate-blueprint` | 30 | 8 | LLM + validation |
| `/tools/execute` | 40 | 10 | Variable complexity |
| `/blueprints` (CRUD) | 100 | 15 | Database ops |

### Rate Limit Headers

Every response includes:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700140800
```

### Rate Limited Response

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30

{
  "detail": "Rate limit exceeded. Try again in 30 seconds."
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "BLUEPRINT_NOT_FOUND",
  "timestamp": "2025-11-16T10:30:00Z"
}
```

### Common Status Codes

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Authentication required (future)
- `403 Forbidden`: Insufficient permissions (future)
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily down

---

## Examples

### Create and Deploy Infrastructure

```bash
# 1. Generate blueprint with AI
curl -X POST http://localhost:8000/api/v1/blueprints/generate-blueprint \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Production web app with HA database",
    "constraints": {"max_cost": 1000}
  }'

# 2. Create IPR for review
curl -X POST http://localhost:8000/api/v1/iprs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Production web app deployment",
    "blueprint_id": 1
  }'

# 3. Review and approve
curl -X POST http://localhost:8000/api/v1/iprs/1/review \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "reviewer": "ops-team"
  }'

# 4. Deploy
curl -X POST http://localhost:8000/api/v1/iprs/1/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "engine": "proxmox",
    "dry_run": false
  }'
```

### Stream Blueprint Generation

```bash
curl -N http://localhost:8000/api/v1/blueprints/generate-blueprint-stream \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Kubernetes cluster with 5 nodes"
  }'
```

### Use Template

```bash
# Get template
curl http://localhost:8000/api/v1/templates/ha-web-app

# Customize
curl -X POST http://localhost:8000/api/v1/templates/ha-web-app/customize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "instance_count": 5,
      "environment": "production"
    }
  }'
```

---

## WebSocket API (Future)

Real-time updates for deployments and monitoring.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/deployments');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Deployment status:', update);
};
```

---

## SDK Examples

### Python

```python
from aicdn import AIClient

client = AIClient(base_url="http://localhost:8000")

# Generate blueprint
blueprint = client.blueprints.generate(
    description="High availability web application",
    constraints={"max_cost": 500}
)

# Create IPR
ipr = client.iprs.create(
    title="Add load balancer",
    blueprint_id=blueprint.id
)

# Deploy
deployment = client.iprs.deploy(ipr.id, engine="proxmox")
```

### JavaScript

```javascript
import { AIClient } from 'aicdn-js';

const client = new AIClient({ baseURL: 'http://localhost:8000' });

// Stream blueprint generation
const stream = await client.blueprints.generateStream({
  description: 'Microservices architecture',
});

for await (const chunk of stream) {
  console.log(chunk);
}
```

---

## Versioning

API versioning through URL path: `/api/v1/`, `/api/v2/`, etc.

Current version: **v1** (stable)

Future versions will maintain backward compatibility for at least 12 months.

---

## Support

- **Documentation**: https://docs.ai-cdn.dev
- **GitHub**: https://github.com/fabriziosalmi/cdn-sdk
- **Issues**: https://github.com/fabriziosalmi/cdn-sdk/issues
- **Discord**: https://discord.gg/ai-cdn
