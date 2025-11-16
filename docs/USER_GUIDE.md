# User Guide - AI-CDN

Welcome to AI-CDN! This guide will help you get started with Infrastructure as Conversation.

## Table of Contents

1. [What is AI-CDN?](#what-is-ai-cdn)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Common Use Cases](#common-use-cases)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## What is AI-CDN?

AI-CDN transforms infrastructure management from code-based IaC (Infrastructure as Code) to **conversation-based infrastructure**. Instead of writing YAML/Terraform, you describe what you need in natural language.

### Key Benefits

✅ **Natural Language**: "I need a highly available web app" → Complete infrastructure  
✅ **AI-Powered**: LLM understands intent, suggests optimizations  
✅ **Review Process**: Infrastructure Pull Requests (IPRs) like code reviews  
✅ **Production Ready**: Rate limiting, metrics, streaming responses  
✅ **Template Library**: 10+ pre-built templates for common scenarios  

### Architecture

```
┌─────────────────┐
│  Natural        │
│  Language       │
│  Input          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Layer      │ ← Qwen2.5-0.5B-Instruct
│  (Intent →      │   + Function Calling
│   Blueprint)    │   + 13 Tools
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validation     │
│  & Review       │ ← IPR System
│  (Human in      │   + Security Audits
│   the Loop)     │   + Cost Estimation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Execution      │
│  Engine         │ ← Proxmox, Docker, K8s
│  (Deploy)       │   + Fake Engine (testing)
└─────────────────┘
```

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/fabriziosalmi/cdn-sdk.git
cd cdn-sdk

# Install dependencies
pip install -e .

# Start server
python run_server.py
```

Server runs at: **http://localhost:8000**

API Docs: **http://localhost:8000/docs**

### Your First Blueprint

#### Option 1: Natural Language (Chat)

```bash
curl -X POST http://localhost:8000/api/v1/conversation/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need a simple web application with 2 servers and a database"
  }'
```

**Response:**
```json
{
  "response": "I'll create a web application with 2 application servers and a PostgreSQL database...",
  "blueprint": {
    "name": "simple-web-app",
    "resources": [
      {"name": "web-1", "type": "vm", "specs": {"cpu": 2, "memory": "4GB"}},
      {"name": "web-2", "type": "vm", "specs": {"cpu": 2, "memory": "4GB"}},
      {"name": "db-1", "type": "database", "engine": "postgresql"}
    ]
  }
}
```

#### Option 2: Use Template

```bash
# List available templates
curl http://localhost:8000/api/v1/templates

# Get specific template
curl http://localhost:8000/api/v1/templates/simple-web-app

# Customize template
curl -X POST http://localhost:8000/api/v1/templates/simple-web-app/customize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "instance_count": 3,
      "environment": "production"
    }
  }'
```

#### Option 3: AI Generation

```bash
curl -X POST http://localhost:8000/api/v1/blueprints/generate-blueprint \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Highly available e-commerce platform",
    "constraints": {
      "max_cost": 1000,
      "region": "us-east-1"
    }
  }'
```

---

## Core Concepts

### 1. Blueprints

**What**: YAML-based infrastructure definitions  
**Why**: Version control, reproducibility, automation

**Example Blueprint:**

```yaml
version: "1.0"
name: web-app-production
description: Production web application

resources:
  - name: web-server-1
    type: vm
    specs:
      cpu: 4
      memory: 8GB
      disk: 100GB
    network:
      private_ip: 10.0.1.10
      public_ip: true
  
  - name: database-1
    type: database
    engine: postgresql
    version: "15"
    specs:
      cpu: 8
      memory: 16GB
      storage: 500GB
    backup:
      enabled: true
      retention_days: 30

metadata:
  environment: production
  owner: devops-team
  cost_center: engineering
```

### 2. Infrastructure Pull Requests (IPRs)

Like GitHub Pull Requests, but for infrastructure changes.

**Workflow:**

1. **Create**: Propose infrastructure change
2. **Review**: Team reviews blueprint, estimates costs, checks security
3. **Approve**: Authorized person approves
4. **Deploy**: Execute deployment
5. **Monitor**: Track deployment progress

**Example:**

```bash
# 1. Create IPR
curl -X POST http://localhost:8000/api/v1/iprs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Scale web tier from 2 to 5 servers",
    "description": "Handle increased traffic from marketing campaign",
    "blueprint_id": 10
  }'

# 2. Review
curl -X POST http://localhost:8000/api/v1/iprs/1/review \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "comments": "Looks good, cost is within budget",
    "reviewer": "jane.smith@company.com"
  }'

# 3. Deploy
curl -X POST http://localhost:8000/api/v1/iprs/1/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "engine": "proxmox",
    "dry_run": false
  }'
```

### 3. LLM Tools

13 specialized tools the LLM can call:

| Tool | Purpose | Example |
|------|---------|---------|
| `create_blueprint` | Generate infrastructure | "Create a K8s cluster" |
| `validate_blueprint` | Check syntax/errors | Validate before deploy |
| `estimate_resources` | Calculate needs | "How much CPU needed?" |
| `optimize_costs` | Reduce expenses | "Cut costs by 30%" |
| `security_audit` | Find vulnerabilities | Pre-deployment check |
| `generate_deployment_plan` | Step-by-step guide | Deployment runbook |
| `troubleshoot_issue` | Diagnose problems | "Server won't start" |
| `compare_blueprints` | Diff two versions | Before/after comparison |
| `suggest_architecture` | Best practices | Architecture review |
| `calculate_capacity` | Capacity planning | "Handle 1M users?" |
| `migrate_infrastructure` | Migration plan | AWS → Azure migration |
| `check_compliance` | Compliance audit | GDPR/SOC2/PCI-DSS |
| `forecast_metrics` | Predictive analytics | Future resource needs |

**Example - Cost Optimization:**

```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "optimize_costs",
    "parameters": {
      "blueprint_id": 5,
      "target_reduction": 0.30,
      "preserve_performance": true
    }
  }'
```

**Response:**
```json
{
  "result": {
    "original_cost": 1500,
    "optimized_cost": 1050,
    "savings": 450,
    "savings_percentage": 30,
    "recommendations": [
      "Use spot instances for non-critical workloads (-$200/mo)",
      "Right-size database from 16GB to 8GB RAM (-$150/mo)",
      "Enable auto-scaling to reduce idle capacity (-$100/mo)"
    ]
  }
}
```

### 4. Templates

Pre-built blueprints for common scenarios:

| Template | Complexity | Cost/Month | Use Case |
|----------|------------|------------|----------|
| `simple-web-app` | Low | $100-200 | Basic website |
| `ha-web-app` | Medium | $300-500 | Production web app |
| `microservices-k8s` | High | $800-1500 | Microservices platform |
| `postgres-ha` | Medium | $400-700 | HA database cluster |
| `data-pipeline` | High | $600-1200 | ETL/data processing |
| `ml-training` | High | $1000-3000 | ML model training |
| `zero-trust-network` | Medium | $500-800 | Security-first network |
| `observability-stack` | Medium | $300-600 | Prometheus + Grafana |
| `api-gateway` | Low | $200-400 | API management |
| `redis-cluster` | Medium | $300-500 | Distributed cache |

---

## Common Use Cases

### Use Case 1: Deploy Web Application

**Scenario**: Deploy a production web app with load balancing and database.

```bash
# Step 1: Use template
curl http://localhost:8000/api/v1/templates/ha-web-app

# Step 2: Customize
curl -X POST http://localhost:8000/api/v1/templates/ha-web-app/customize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "instance_count": 3,
      "cpu_per_instance": 4,
      "memory_per_instance": "8GB",
      "database_size": "50GB",
      "backup_enabled": true,
      "environment": "production"
    }
  }' > my-blueprint.json

# Step 3: Create blueprint
curl -X POST http://localhost:8000/api/v1/blueprints \
  -H "Content-Type: application/json" \
  -d @my-blueprint.json

# Step 4: Create IPR
curl -X POST http://localhost:8000/api/v1/iprs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Production web app deployment",
    "description": "Initial deployment for product launch",
    "blueprint_id": 1
  }'

# Step 5: Review and deploy (after approval)
curl -X POST http://localhost:8000/api/v1/iprs/1/deploy \
  -d '{"engine": "proxmox"}'
```

### Use Case 2: Cost Optimization

**Scenario**: Reduce infrastructure costs by 25%.

```bash
# Step 1: Analyze current infrastructure
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "estimate_resources",
    "parameters": {
      "blueprint_id": 5
    }
  }'

# Step 2: Get optimization recommendations
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "optimize_costs",
    "parameters": {
      "blueprint_id": 5,
      "target_reduction": 0.25
    }
  }'

# Step 3: Apply recommendations (creates new blueprint)
# Step 4: Create IPR with cost comparison
# Step 5: Deploy after approval
```

### Use Case 3: Security Audit

**Scenario**: Audit infrastructure before production deployment.

```bash
# Run security audit
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "security_audit",
    "parameters": {
      "blueprint_id": 10,
      "check_compliance": ["SOC2", "GDPR"]
    }
  }'
```

**Response:**
```json
{
  "result": {
    "security_score": 7.5,
    "vulnerabilities": [
      {
        "severity": "high",
        "issue": "Database port 5432 exposed to internet",
        "recommendation": "Use private subnet and VPN access"
      },
      {
        "severity": "medium",
        "issue": "No encryption at rest for storage volumes",
        "recommendation": "Enable disk encryption"
      }
    ],
    "compliance": {
      "SOC2": "partial",
      "GDPR": "compliant"
    }
  }
}
```

### Use Case 4: Conversational Infrastructure

**Scenario**: Iterative refinement through conversation.

```bash
# Round 1: Initial request
curl -X POST http://localhost:8000/api/v1/conversation/chat \
  -d '{
    "message": "I need a Kubernetes cluster"
  }'

# Round 2: Add requirements
curl -X POST http://localhost:8000/api/v1/conversation/chat \
  -d '{
    "message": "Make it highly available with 5 nodes",
    "context": {"conversation_id": "conv-123"}
  }'

# Round 3: Cost constraints
curl -X POST http://localhost:8000/api/v1/conversation/chat \
  -d '{
    "message": "Keep monthly cost under $800",
    "context": {"conversation_id": "conv-123"}
  }'

# Round 4: Security requirements
curl -X POST http://localhost:8000/api/v1/conversation/chat \
  -d '{
    "message": "Add network policies and pod security standards",
    "context": {"conversation_id": "conv-123"}
  }'
```

---

## Best Practices

### 1. Always Use IPRs

✅ **DO**: Create IPR for any infrastructure change  
❌ **DON'T**: Deploy directly without review

**Why**: Prevents costly mistakes, ensures compliance, creates audit trail.

### 2. Estimate Costs Before Deploying

```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -d '{
    "tool_name": "estimate_resources",
    "parameters": {"blueprint_id": 5}
  }'
```

### 3. Run Security Audits

Before production deployment:

```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -d '{
    "tool_name": "security_audit",
    "parameters": {"blueprint_id": 5}
  }'
```

### 4. Use Templates as Starting Points

Don't create blueprints from scratch. Customize templates:

```bash
# Start with template
curl http://localhost:8000/api/v1/templates/ha-web-app

# Customize to your needs
curl -X POST http://localhost:8000/api/v1/templates/ha-web-app/customize \
  -d '{"parameters": {...}}'
```

### 5. Version Control Blueprints

Store blueprints in Git:

```bash
# Export blueprint
curl http://localhost:8000/api/v1/blueprints/5 > infrastructure.yaml

# Commit to Git
git add infrastructure.yaml
git commit -m "Add production web app infrastructure"
git push
```

### 6. Monitor Metrics

Check metrics regularly:

```bash
# System health
curl http://localhost:8000/api/v1/monitoring/health/detailed

# Resource usage
curl http://localhost:8000/api/v1/monitoring/metrics/summary

# Rate limiting
curl http://localhost:8000/api/v1/monitoring/rate-limit/stats
```

### 7. Use Streaming for Large Operations

For slow operations (LLM generation), use streaming:

```bash
curl -N http://localhost:8000/api/v1/conversation/chat-stream \
  -d '{"message": "Create complex microservices architecture"}'
```

**Benefits**:
- 96% faster time-to-first-byte
- Real-time progress updates
- Better user experience

---

## Troubleshooting

### Problem: Rate Limit Exceeded

**Error:**
```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

**Solution:**
- Wait for rate limit reset (check `Retry-After` header)
- Reduce request frequency
- Contact admin to increase limits

### Problem: Blueprint Validation Failed

**Error:**
```json
{
  "detail": "Invalid blueprint format",
  "errors": [
    "resources.0.specs.memory: invalid format"
  ]
}
```

**Solution:**
1. Check blueprint syntax
2. Use validation tool:
```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -d '{
    "tool_name": "validate_blueprint",
    "parameters": {"blueprint_id": 5}
  }'
```

### Problem: Deployment Failed

**Check deployment logs:**
```bash
curl http://localhost:8000/api/v1/iprs/1
```

**Common causes:**
- Insufficient resources
- Network connectivity issues
- Authentication problems with engine (Proxmox/Docker)

**Solution**: Use troubleshooting tool:
```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -d '{
    "tool_name": "troubleshoot_issue",
    "parameters": {
      "blueprint_id": 5,
      "error_message": "VM creation failed"
    }
  }'
```

### Problem: High Costs

**Check cost estimation:**
```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -d '{
    "tool_name": "estimate_resources",
    "parameters": {"blueprint_id": 5}
  }'
```

**Get optimization recommendations:**
```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -d '{
    "tool_name": "optimize_costs",
    "parameters": {
      "blueprint_id": 5,
      "target_reduction": 0.30
    }
  }'
```

### Problem: Server Not Responding

**Check health:**
```bash
curl http://localhost:8000/api/v1/monitoring/health/detailed
```

**Check logs:**
```bash
tail -f logs/aicdn.log
```

**Restart server:**
```bash
python run_server.py
```

---

## Advanced Topics

### Custom Tool Development

Create your own LLM tools:

```python
# ai_cdn/core/custom_tools.py
from ai_cdn.core.tools import InfrastructureTools

class CustomTools(InfrastructureTools):
    def _my_custom_tool(self, params: dict) -> dict:
        """Custom tool implementation."""
        return {
            "result": "Custom logic here",
            "status": "success"
        }
    
    @classmethod
    def get_available_tools(cls) -> List[dict]:
        tools = super().get_available_tools()
        tools.append({
            "name": "my_custom_tool",
            "description": "Does something custom",
            "parameters": {...}
        })
        return tools
```

### Multi-Cloud Deployment

Deploy same blueprint to multiple clouds:

```bash
# Deploy to Proxmox
curl -X POST http://localhost:8000/api/v1/iprs/1/deploy \
  -d '{"engine": "proxmox"}'

# Deploy to Docker
curl -X POST http://localhost:8000/api/v1/iprs/2/deploy \
  -d '{"engine": "docker"}'

# Future: AWS, Azure, GCP
```

### Metrics and Monitoring

Set up full observability stack:

```bash
# Start Prometheus + Grafana
docker-compose -f docker-compose.metrics.yml up -d

# Access Grafana: http://localhost:3000
# Default dashboard pre-loaded
```

**Custom Prometheus queries:**

```promql
# Request rate by endpoint
rate(http_requests_total[5m])

# LLM token throughput
rate(llm_tokens_generated_total[1m])

# P95 latency
histogram_quantile(0.95, http_request_duration_seconds)
```

---

## Next Steps

1. **Explore API**: http://localhost:8000/docs
2. **Try Templates**: `curl http://localhost:8000/api/v1/templates`
3. **Read Architecture**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
4. **Production Deploy**: [docs/PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
5. **Join Community**: https://discord.gg/ai-cdn

---

## Support

- **Documentation**: All docs in `docs/` folder
- **GitHub Issues**: Report bugs or request features
- **Discord**: Community support and discussions
- **Email**: support@ai-cdn.dev (for enterprise customers)

Happy infrastructure management! 🚀
