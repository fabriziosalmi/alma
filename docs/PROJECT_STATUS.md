# Project Status & Documentation Index

**ALMA: Infrastructure as Conversation**  
*Current Version: 0.8.8*

---

## Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| Enhanced Function Calling | Complete | `alma/core/tools.py` — 13 tools |
| Streaming Responses | Complete | SSE endpoints in `alma/api/routes/conversation.py` |
| Blueprint Templates | Complete | `alma/config/blueprints.yaml` — 10 templates |
| Rate Limiting | Complete | `alma/middleware/rate_limit.py` |
| Metrics Collection | Complete | `alma/middleware/metrics.py` — Prometheus |
| API Key Authentication | Complete | Configurable via `ALMA_API_KEY` env var |
| Web UI | Complete | React-based dashboard in `alma-web/` |
| LangGraph Workflow | Complete | `alma/core/agent/graph.py` |
| Multi-Agent Council | Complete | `alma/core/agent/council.py` |
| WebSocket Updates | Complete | `/ws/deployments` |
| GraphQL API | Partial | Basic system status only (`/graphql`) |
| Kubernetes Engine | Experimental | `alma/engines/kubernetes.py` |
| RBAC | Planned | Not yet implemented |
| Multi-tenancy | Planned | Not yet implemented |

---

## Documentation

### User Documentation

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Project overview, quick start |
| [USER_GUIDE.md](USER_GUIDE.md) | User guide with examples |
| [API_REFERENCE.md](API_REFERENCE.md) | API documentation |

### Technical Documentation

| Document | Purpose |
|----------|---------|
| [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) | Production setup & operations |
| [RATE_LIMITING_AND_METRICS.md](RATE_LIMITING_AND_METRICS.md) | Monitoring reference |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical architecture |
| [TOOLS_API.md](TOOLS_API.md) | LLM tools documentation |
| [STREAMING_AND_TEMPLATES.md](STREAMING_AND_TEMPLATES.md) | Streaming & templates |

---

## Feature Highlights

### 1. Enhanced Function Calling (13 Tools)

The LLM can call these infrastructure tools:

- `create_blueprint` - Generate infrastructure blueprints
- `validate_blueprint` - Syntax and semantic validation
- `estimate_resources` - Resource requirement calculation
- `optimize_costs` - Cost reduction recommendations
- `security_audit` - Security compliance checks
- `generate_deployment_plan` - Step-by-step deployment guides
- `troubleshoot_issue` - Problem diagnosis
- `compare_blueprints` - Version comparison
- `suggest_architecture` - Best practices recommendations
- `calculate_capacity` - Capacity planning
- `migrate_infrastructure` - Migration strategies
- `check_compliance` - Compliance verification
- `forecast_metrics` - Predictive analytics

### 2. Streaming Responses (SSE)

Real-time streaming for LLM operations:

- **Endpoints**: `/chat-stream`, `/generate-blueprint-stream`
- **Implementation**: Server-Sent Events (SSE)

### 3. Blueprint Templates (10 Templates)

Pre-built infrastructure topologies (see `alma/config/blueprints.yaml`):

| Template | Complexity | Resources |
|----------|------------|-----------|
| simple-web-app | Low | 3 |
| ha-web-app | Medium | 8 |
| microservices-k8s | High | 15+ |
| postgres-ha | Medium | 6 |
| data-pipeline | High | 12 |
| ml-training | High | 10 |
| zero-trust-network | Medium | 9 |
| observability-stack | Medium | 7 |
| api-gateway | Low | 4 |
| redis-cluster | Medium | 5 |

### 4. Rate Limiting

Token bucket algorithm with per-endpoint limits:

- **Global**: 60 RPM per IP
- **Burst**: 10 requests (customizable)
- **Per-Endpoint Limits**:
  - Chat streaming: 20 RPM (LLM intensive)
  - Blueprint generation: 30 RPM
  - Tool execution: 40 RPM
  - CRUD operations: 100 RPM
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### 5. Metrics Collection

Prometheus metrics endpoint (`/metrics`) with:

- HTTP requests (total, duration, sizes)
- LLM operations (requests, tokens, duration)
- Blueprint operations (CRUD, validation)
- Deployments (operations, duration)
- Tool executions (by tool, status)
- Rate limiting (hits, clients)
- System metrics (connections, cache)

A pre-configured Grafana dashboard is included in `grafana-dashboard.json`.

---

## Getting Started

### Installation

```bash
git clone https://github.com/fabriziosalmi/alma.git
cd alma
python3 -m venv venv
source venv/bin/activate
pip install -e .
python run_server.py
```

### First API Call

```bash
curl -X POST http://localhost:8000/api/v1/conversation/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a simple web application"}'
```

### Explore Templates

```bash
# List templates
curl http://localhost:8000/api/v1/templates

# Get specific template
curl http://localhost:8000/api/v1/templates/ha-web-app
```

### Check Metrics

```bash
# Prometheus format
curl http://localhost:8000/metrics

# Human-readable
curl http://localhost:8000/api/v1/monitoring/metrics/summary
```

---

## API Endpoints Summary

### Core APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/blueprints` | GET, POST | Blueprint CRUD |
| `/api/v1/blueprints/{id}` | GET, PUT, DELETE | Single blueprint |
| `/api/v1/blueprints/generate-blueprint` | POST | AI generation |
| `/api/v1/blueprints/generate-blueprint-stream` | POST | AI streaming |
| `/api/v1/conversation/chat` | POST | Chat interface |
| `/api/v1/conversation/chat-stream` | POST | Chat streaming |
| `/api/v1/iprs` | GET, POST | IPR management |
| `/api/v1/iprs/{id}/review` | POST | Review IPR |
| `/api/v1/iprs/{id}/deploy` | POST | Deploy IPR |
| `/api/v1/tools` | GET | List tools |
| `/api/v1/tools/execute` | POST | Execute tool |
| `/api/v1/templates` | GET | List templates |
| `/api/v1/templates/{id}` | GET | Get template |
| `/api/v1/templates/{id}/customize` | POST | Customize template |

### Monitoring APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/metrics` | GET | Prometheus metrics |
| `/api/v1/monitoring/metrics/summary` | GET | Metrics summary |
| `/api/v1/monitoring/rate-limit/stats` | GET | Rate limit stats |
| `/api/v1/monitoring/health/detailed` | GET | Health check |

---

## Production Deployment

### Docker Compose (Recommended)

```bash
# Start full stack with monitoring
docker-compose -f docker-compose.metrics.yml up -d
```

**Includes**:
- ALMA API server
- PostgreSQL 15
- Redis 7
- Prometheus
- Grafana (with pre-configured dashboard)

**Access**:
- API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for full setup details.

---

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Test rate limiting
for i in {1..70}; do curl http://localhost:8000/api/v1/blueprints; done

# Test metrics
curl http://localhost:8000/metrics | grep http_requests_total

# Test streaming
curl -N http://localhost:8000/api/v1/conversation/chat-stream \
  -d '{"message": "Create Kubernetes cluster"}'
```

---

## Security

### Implemented
- IP-based rate limiting
- SQL injection protection (SQLAlchemy ORM)
- Input validation (Pydantic)
- CORS configuration
- API key authentication (configurable via `ALMA_API_KEY`)

### Planned
- JWT token support
- RBAC (Role-Based Access Control)
- OAuth2 integration
- Audit logging
- Encryption at rest

---

## Roadmap

### Near Term
- **RBAC**: Fine-grained role-based access control.
- **Native K8s Operator**: CRD-based management instead of API-driven.

### Future
- **Cloud Portability**: Abstracted blueprint definitions for AWS, Azure, GCP.
- **Hybrid Deployment**: Unified management plane for On-Prem and Cloud.
- **Anomaly Detection**: ML-based resource usage monitoring.

---

## Support & Community

- **Documentation**: [docs/](.)
- **GitHub**: https://github.com/fabriziosalmi/alma
- **Issues**: https://github.com/fabriziosalmi/alma/issues
- **Discussions**: https://github.com/fabriziosalmi/alma/discussions

---

## Implementation Status

### Completed

- [x] **Core Engines**: Proxmox (primary), Docker, Kubernetes (experimental), Simulation.
- [x] **IPR Workflow**: Create, Review, Deploy lifecycle.
- [x] **LLM Integration**: Configurable LLM backend with 13 specialized tools.
- [x] **Multi-Agent Council**: Architect, SecOps, FinOps agents for blueprint review.
- [x] **LangGraph Workflow**: State machine for deployment orchestration.
- [x] **Observability**: Prometheus metrics.
- [x] **Rate Limiting**: Token-bucket per-IP limiting.
- [x] **Streaming**: SSE endpoints for real-time LLM output.
- [x] **API Key Authentication**: Configurable auth middleware.
- [x] **Web UI**: React-based dashboard (`alma-web/`).

### Active Development

- [ ] **Native K8s Operator**: CRD-based management.
- [ ] **RBAC**: Fine-grained role-based access control.
- [ ] **Multi-tenancy**: Isolated namespaces per team.
