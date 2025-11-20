# API Reference - ALMA

> **ALMA** - Autonomous Language Model Architecture  
> Infrastructure as Conversation Platform

Complete API documentation for the ALMA platform, enabling natural language infrastructure management through advanced AI capabilities.

## Base URL

```
http://localhost:8000/api/v1
```

**Production Environment:**
```
https://api.alma.dev/v1
```

## Authentication

ALMA implements **header-based API Key authentication** to secure critical infrastructure operations.

### API Key Authentication

**Status:** ✅ **Active** (as of v0.4.3)

All write operations (POST, PUT, DELETE) on critical endpoints require a valid API key passed via the `X-API-Key` header.

#### Configuration

Authentication is controlled via environment variables:

```bash
# Enable authentication (default: true in production)
export ALMA_AUTH_ENABLED=true

# Comma-separated list of valid API keys
export ALMA_API_KEYS="prod-key-abc123,backup-key-xyz789"

# Disable authentication (development only)
export ALMA_AUTH_ENABLED=false
```

#### Usage Example

```bash
# With authentication
curl -X POST http://localhost:8000/api/v1/blueprints/ \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"version": "1.0", "name": "my-infrastructure", "resources": []}'
```

#### Protected Endpoints

The following endpoints **require authentication**:

**Blueprints:**
- `POST /api/v1/blueprints/` - Create blueprint
- `POST /api/v1/blueprints/{id}/deploy` - Deploy blueprint

**Infrastructure Pull Requests:**
- `POST /api/v1/ipr/` - Create IPR

**Tools:**
- `POST /api/v1/tools/execute` - Execute tool
- `POST /api/v1/tools/execute-direct` - Execute tool directly

#### Public Endpoints

The following endpoints remain **public** (no authentication required):

- `GET /api/v1/monitoring/health` - Basic health check
- `GET /api/v1/monitoring/health/detailed` - Detailed health status
- `GET /api/v1/monitoring/metrics` - Prometheus metrics
- `GET /api/v1/monitoring/metrics/summary` - Metrics summary
- All **GET** operations on blueprints, IPRs, templates

#### Authentication Responses

**Success (authenticated):**
```http
HTTP/1.1 201 Created
```

**Missing or invalid API key:**
```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "Invalid API key"
}
```

### Future Authentication Features

Planned enhancements for future releases:

- **OAuth2 / JWT Tokens** - Industry-standard authorization
- **Role-Based Access Control (RBAC)** - Granular permission management
- **Multi-Factor Authentication (MFA)** - Enhanced security layer
- **API Key Rotation** - Automated key management
- **Per-Key Rate Limits** - Fine-grained access control

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

🔒 **Requires Authentication** - Include `X-API-Key` header

**Headers:**
```
X-API-Key: your-api-key-here
Content-Type: application/json
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
- `403 Forbidden`: Invalid or missing API key
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
    "generated_by": "ALMA-llm",
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
POST /api/v1/ipr
```

🔒 **Requires Authentication** - Include `X-API-Key` header

**Headers:**
```
X-API-Key: your-api-key-here
Content-Type: application/json
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
- `403 Forbidden`: Invalid or missing API key
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

🔒 **Requires Authentication** - Include `X-API-Key` header

**Headers:**
```
X-API-Key: your-api-key-here
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "Estimate resources for high traffic web application",
  "context": {
    "blueprint_id": 5,
    "usage_pattern": "high_traffic",
    "peak_users": 10000
  }
}
```

**Response:**
```json
{
  "success": true,
  "tool": "estimate_resources",
  "result": {
    "cpu_cores": 48,
    "memory_gb": 128,
    "storage_tb": 2,
    "estimated_cost_monthly": 850
  },
  "timestamp": "2025-11-20T10:30:00Z"
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
- `403 Forbidden`: Invalid or missing API key
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
- `401 Unauthorized`: Authentication required (reserved for future use)
- `403 Forbidden`: Invalid or missing API key
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily down

### Authentication Error Examples

**Missing API Key:**
```json
{
  "detail": "Invalid API key"
}
```

**Invalid API Key:**
```json
{
  "detail": "Invalid API key"
}
```

**Authentication Disabled (Development):**
When `ALMA_AUTH_ENABLED=false`, all endpoints are accessible without authentication. This should **only** be used in development environments.

---

## Examples

### Create and Deploy Infrastructure

```bash
# Set API key as environment variable
export API_KEY="your-api-key-here"

# 1. Generate blueprint with AI
curl -X POST http://localhost:8000/api/v1/blueprints/generate-blueprint \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Production web app with HA database",
    "constraints": {"max_cost": 1000}
  }'

# 2. Create IPR for review
curl -X POST http://localhost:8000/api/v1/ipr/ \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Production web app deployment",
    "blueprint_id": 1
  }'

# 3. Review and approve (public endpoint)
curl -X POST http://localhost:8000/api/v1/ipr/1/review \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "reviewer": "ops-team"
  }'

# 4. Deploy (requires auth)
curl -X POST http://localhost:8000/api/v1/ipr/1/deploy \
  -H "X-API-Key: $API_KEY" \
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

## WebSocket API (Beta)

Real-time infrastructure monitoring and deployment status updates via WebSocket connections.

### Connection Endpoint

```
ws://localhost:8000/ws/deployments
wss://api.alma.dev/ws/deployments  # Production (Secure)
```

### Example Implementation

```javascript
// Establish WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/deployments');

// Handle connection events
ws.onopen = () => {
  console.log('Connected to ALMA deployment stream');
  
  // Subscribe to specific deployment
  ws.send(JSON.stringify({
    action: 'subscribe',
    deployment_id: 'deploy-abc123'
  }));
};

// Receive real-time updates
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  
  switch(update.type) {
    case 'status_change':
      console.log(`Status: ${update.status}`);
      break;
    case 'progress':
      console.log(`Progress: ${update.percentage}%`);
      break;
    case 'error':
      console.error(`Error: ${update.message}`);
      break;
    case 'complete':
      console.log('Deployment completed successfully');
      ws.close();
      break;
  }
};

// Handle connection errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Handle disconnections
ws.onclose = () => {
  console.log('Disconnected from deployment stream');
};
```

### Message Types

| Type | Description | Payload Example |
|------|-------------|-----------------|
| `status_change` | Deployment status updated | `{"status": "in_progress"}` |
| `progress` | Progress percentage | `{"percentage": 45, "step": "provisioning"}` |
| `log` | Real-time log entry | `{"message": "Creating VM...", "level": "info"}` |
| `error` | Error occurred | `{"message": "Failed to allocate IP", "code": "NET_001"}` |
| `complete` | Deployment finished | `{"duration_seconds": 342, "resources_created": 5}` |

---

## SDK Examples

### Python SDK

```python
import httpx
import os

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
API_KEY = os.getenv("ALMA_API_KEY", "your-api-key-here")

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

async def create_infrastructure():
    async with httpx.AsyncClient() as client:
        # Create blueprint
        blueprint_response = await client.post(
            f"{BASE_URL}/blueprints/",
            json={
                "version": "1.0",
                "name": "production-web-app",
                "description": "HA web application",
                "resources": [
                    {
                        "name": "web-server-1",
                        "type": "vm",
                        "specs": {"cpu": 4, "memory": "8GB"}
                    }
                ]
            },
            headers=headers
        )
        blueprint = blueprint_response.json()
        print(f"Created blueprint: {blueprint['id']}")
        
        # Create IPR
        ipr_response = await client.post(
            f"{BASE_URL}/ipr/",
            json={
                "title": "Deploy production infrastructure",
                "blueprint_id": blueprint["id"]
            },
            headers=headers
        )
        ipr = ipr_response.json()
        
        # Deploy (with authentication)
        deploy_response = await client.post(
            f"{BASE_URL}/ipr/{ipr['id']}/deploy",
            json={"engine": "proxmox", "dry_run": False},
            headers=headers
        )
        
        return deploy_response.json()

# Run deployment
import asyncio
result = asyncio.run(create_infrastructure())
print(f"Deployment status: {result['status']}")
```

### JavaScript/TypeScript SDK

```typescript
const BASE_URL = 'http://localhost:8000/api/v1';
const API_KEY = process.env.ALMA_API_KEY || 'your-api-key-here';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Create blueprint with authentication
async function createBlueprint() {
  const response = await fetch(`${BASE_URL}/blueprints/`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      version: '1.0',
      name: 'microservices-k8s',
      description: 'Kubernetes microservices architecture',
      resources: [
        {
          name: 'k8s-cluster',
          type: 'kubernetes',
          specs: { nodes: 5, cpu_per_node: 4 }
        }
      ]
    })
  });
  
  if (response.status === 403) {
    throw new Error('Invalid API key');
  }
  
  return response.json();
}

// Execute tool with authentication
async function executeTool(query: string, context: object) {
  const response = await fetch(`${BASE_URL}/tools/execute`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ query, context })
  });
  
  return response.json();
}

// Example usage
const blueprint = await createBlueprint();
console.log('Blueprint created:', blueprint.id);

const resources = await executeTool(
  'Estimate resources for this blueprint',
  { blueprint_id: blueprint.id }
);
console.log('Resource estimate:', resources.result);
```

---

## Versioning

ALMA API follows semantic versioning principles through URL path versioning:

- **Current Stable:** `/api/v1/` (Production Ready)
- **Future Releases:** `/api/v2/`, `/api/v3/`, etc.

### Backwards Compatibility Policy

- All stable API versions maintain **backwards compatibility for minimum 12 months**
- Deprecated features receive advance notice with migration guides
- Breaking changes are introduced only in major version increments
- Legacy endpoints remain accessible during deprecation period

### Version History

| Version | Status | Release Date | End of Support |
|---------|--------|--------------|----------------|
| v1      | Stable | 2025-01-01   | Active         |

---

## Support & Resources

### Developer Support

- **Documentation Portal**: https://alma-docs.dev
- **GitHub Repository**: https://github.com/fabriziosalmi/alma
- **Issue Tracker**: https://github.com/fabriziosalmi/alma/issues
- **Community Discussions**: https://github.com/fabriziosalmi/alma/discussions

### Enterprise Support

For production deployments and enterprise licensing:
- **Email**: enterprise@alma.dev
- **SLA Response Times**: 4-hour critical, 24-hour standard
- **Dedicated Support Channel**: Available on request

### Contributing

ALMA is open-source and welcomes community contributions:
- Review our [Contributing Guidelines](../CONTRIBUTING.md)
- Submit pull requests for bug fixes and features
- Report security vulnerabilities responsibly
- Join our developer community

---

## Legal & Compliance

- **License**: MIT (Open Source)
- **Privacy Policy**: https://alma.dev/privacy
- **Terms of Service**: https://alma.dev/terms
- **Security Disclosures**: security@alma.dev

---

**Last Updated**: November 2025  
**API Version**: 1.0.0  
**Documentation Version**: 1.0.0
