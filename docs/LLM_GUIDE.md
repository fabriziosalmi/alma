# ALMA LLM Integration Guide

This guide explains how to configure and use the LLM integration in ALMA for conversational infrastructure management.

## Overview

ALMA supports configurable LLM backends (defaulting to `Qwen/Qwen2.5-0.5B-Instruct` for local inference) to provide:
- **Natural language to infrastructure** - Describe what you want, get a blueprint
- **Infrastructure to natural language** - Understand what your blueprints do
- **Improvement suggestions** - Get recommendations for improvements
- **Security audits** - Identify security issues in blueprints
- **Resource sizing** - Get resource recommendations
- **Intent classification** - Understand user requests

## Installation

### Prerequisites

```bash
# Install ALMA with LLM support
pip install -e ".[dev,llm]"

# This installs:
# - transformers>=4.36.0
# - torch>=2.1.0
```

### Configuration

Configure the LLM in your `.env` file:

```bash
# LLM Configuration
LLM_MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
LLM_DEVICE=cpu  # cpu, cuda, or mps (Apple Silicon)
LLM_MAX_TOKENS=512

# Optional: Disable LLM (use rule-based fallback)
# LLM_DEVICE=none
```

### Device Selection

- **CPU**: Works everywhere, slower
- **CUDA**: NVIDIA GPUs, fastest
- **MPS**: Apple Silicon (M1/M2/M3), fast

The system will automatically select the best available device if not specified.

## API Endpoints

### 1. Chat with AI

Have a conversation about infrastructure:

```bash
curl -X POST http://localhost:8000/api/v1/conversation/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need to deploy a scalable web application"
  }'
```

**Response:**
```json
{
  "intent": "create_blueprint",
  "confidence": 0.9,
  "response": "I understand you want to create a blueprint. I can help you create an infrastructure blueprint.",
  "blueprint": null
}
```

### 2. Generate Blueprint from Description

Convert natural language to infrastructure code:

```bash
curl -X POST http://localhost:8000/api/v1/conversation/generate-blueprint \
  -H "Content-Type: application/json" \
  -d '{
    "description": "I need a high-availability web application with load balancer, 3 web servers, and a PostgreSQL database cluster"
  }'
```

**Response:**
```yaml
version: "1.0"
name: ha-web-application
description: High-availability web application with load balancer and database
resources:
  - type: compute
    name: web-server-1
    provider: proxmox
    specs:
      cpu: 4
      memory: 8GB
      storage: 50GB
    # ... more servers

  - type: network
    name: load-balancer
    provider: fake
    specs:
      type: http
      algorithm: round-robin
      backends:
        - web-server-1
        - web-server-2
        - web-server-3

  - type: compute
    name: postgres-primary
    provider: proxmox
    specs:
      cpu: 8
      memory: 32GB
      storage: 500GB
```

### 3. Describe Blueprint in Natural Language

Convert infrastructure code to human-readable description:

```bash
curl -X POST http://localhost:8000/api/v1/conversation/describe-blueprint \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint": {
      "name": "my-app",
      "resources": [...]
    }
  }'
```

**Response:**
```json
{
  "description": "This infrastructure 'my-app' provides a highly available web application consisting of:\n\n1. A load balancer distributing traffic across 3 web servers\n2. Three application servers running your web application\n3. A PostgreSQL database cluster with primary and standby nodes\n4. Automated backups configured for disaster recovery\n\nThe setup ensures 99.9% uptime with automatic failover capabilities."
}
```

### 4. Get Improvement Suggestions

Analyze your infrastructure and get recommendations:

```bash
curl -X POST http://localhost:8000/api/v1/conversation/suggest-improvements \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint": {
      "name": "single-server-app",
      "resources": [{
        "type": "compute",
        "name": "web-server",
        "specs": {"cpu": 1, "memory": "512MB"}
      }]
    }
  }'
```

**Response:**
```json
{
  "suggestions": [
    "Add redundant servers for high availability (minimum 2 instances). Current setup has a single point of failure.",
    "Increase resource allocation - 1 CPU and 512MB RAM may be insufficient for production workloads. Recommend at least 2 CPUs and 2GB RAM.",
    "Add a load balancer to distribute traffic and enable horizontal scaling.",
    "Implement backup storage for disaster recovery. No backup solution is currently configured.",
    "Add monitoring and observability tools (e.g., Prometheus, Grafana) to track system health."
  ]
}
```

### 5. Resource Sizing Recommendations

Get resource sizing recommendations for your workload:

```bash
curl -X POST http://localhost:8000/api/v1/conversation/resource-sizing \
  -H "Content-Type: application/json" \
  -d '{
    "workload": "Django web application with PostgreSQL",
    "expected_load": "5000 concurrent users, 100 requests/second"
  }'
```

**Response:**
```json
{
  "cpu": 8,
  "memory": "16GB",
  "storage": "200GB",
  "storage_type": "SSD",
  "network": "1Gbps",
  "reasoning": "For a Django application serving 5000 concurrent users at 100 req/s: 8 CPUs handle request processing, 16GB RAM supports Django processes + database connections, 200GB SSD ensures fast database queries and application response times."
}
```

### 6. Security Audit

Get security analysis of your blueprint:

```bash
curl -X POST http://localhost:8000/api/v1/conversation/security-audit \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint": {
      "name": "web-app",
      "resources": [...]
    }
  }'
```

**Response:**
```json
{
  "findings": [
    {
      "severity": "High",
      "issue": "Database server directly accessible from internet",
      "recommendation": "Place database in private subnet, only accessible from application servers"
    },
    {
      "severity": "Medium",
      "issue": "No SSL/TLS encryption configured for load balancer",
      "recommendation": "Enable HTTPS with valid certificates, redirect HTTP to HTTPS"
    },
    {
      "severity": "Medium",
      "issue": "No firewall rules defined",
      "recommendation": "Implement network segmentation with strict firewall rules"
    }
  ]
}
```

## Python SDK Usage

### Basic Usage

```python
from alma.core.llm_qwen import Qwen3LLM
from alma.core.llm_orchestrator import EnhancedOrchestrator

# Initialize LLM
llm = Qwen3LLM(
    model_name="Qwen/Qwen2.5-0.5B-Instruct",
    device="cpu",  # or "cuda", "mps"
    max_tokens=512
)

# Initialize orchestrator
orchestrator = EnhancedOrchestrator(llm=llm, use_llm=True)

# Generate blueprint
blueprint = await orchestrator.natural_language_to_blueprint(
    "Create a microservices architecture with API gateway, 3 services, and message queue"
)

# Get suggestions
suggestions = await orchestrator.suggest_improvements(blueprint)

# Clean up
await llm.close()
```

### Using Service Layer

```python
from alma.core.llm_service import get_orchestrator

# Get singleton orchestrator (automatically manages LLM lifecycle)
orchestrator = await get_orchestrator()

# Use it
blueprint = await orchestrator.natural_language_to_blueprint(
    "Deploy a CI/CD pipeline"
)
```

## CLI Usage

The CLI uses the LLM for natural language processing:

```bash
# Generate blueprint from natural language
ALMA generate "I need a Kubernetes cluster with 3 nodes"

# This will:
# 1. Use LLM to understand your intent
# 2. Generate appropriate blueprint
# 3. Save it to blueprints/
```

## Performance Considerations

### Model Size vs. Speed

- **Qwen2.5-0.5B**: Fast, good for most tasks (~1-2 seconds per query on CPU)
- **Qwen2.5-1.5B**: Better quality, slower (~3-5 seconds per query on CPU)
- **Qwen2.5-7B**: Best quality, requires GPU (~1-2 seconds on GPU)

### Optimization Tips

1. **Use GPU/MPS** for faster inference
2. **Enable model caching** - first request is slow, subsequent are fast
3. **Batch requests** when possible
4. **Warmup** on startup (automatically done by API server)

### Memory Requirements

- **0.5B model**: ~2GB RAM
- **1.5B model**: ~4GB RAM
- **7B model**: ~16GB RAM (GPU recommended)

## Fallback Behavior

If LLM initialization fails (missing dependencies, insufficient RAM, etc.), ALMA automatically falls back to rule-based processing:

- Blueprint generation uses keyword matching
- Suggestions use predefined rules
- Descriptions use templates

This ensures ALMA always works, even without LLM support.

## Advanced: Custom Prompts

You can customize prompts for specific use cases:

```python
from alma.core.prompts import InfrastructurePrompts

# Use custom prompt for blueprint generation
custom_prompt = f"""
{InfrastructurePrompts.blueprint_generation("my infrastructure")}

Additional constraints:
- Use only open-source technologies
- Optimize for cost efficiency
- Include monitoring from day 1
"""

response = await llm.generate(custom_prompt)
```

## Troubleshooting

### Model Download Issues

```bash
# Pre-download model
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct')"
```

### Out of Memory

1. Use smaller model: `LLM_MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct`
2. Reduce max tokens: `LLM_MAX_TOKENS=256`
3. Use CPU if GPU OOM: `LLM_DEVICE=cpu`

### Slow Performance

1. Use GPU: `LLM_DEVICE=cuda` or `LLM_DEVICE=mps`
2. Reduce max tokens
3. Enable model quantization (advanced)

## Examples

### Example 1: Microservices Platform

```python
description = """
I need a production-ready microservices platform with:
- API Gateway (Kong or similar)
- 3 microservices (auth, users, orders)
- PostgreSQL database
- Redis cache
- RabbitMQ message queue
- Elasticsearch for logging
- Prometheus + Grafana for monitoring
"""

blueprint = await orchestrator.natural_language_to_blueprint(description)
```

### Example 2: Security Hardening

```python
# Get your current blueprint
blueprint = {...}

# Run security audit
findings = await orchestrator.security_audit(blueprint)

# Apply suggestions
suggestions = await orchestrator.suggest_improvements(blueprint)
```

### Example 3: Cost Optimization

```python
# Get resource sizing for your workload
sizing = await orchestrator.estimate_resources(
    workload="E-commerce website with PostgreSQL",
    expected_load="10,000 daily active users, peak 500 concurrent"
)

print(f"Recommended: {sizing['cpu']} CPUs, {sizing['memory']} RAM")
print(f"Reasoning: {sizing['reasoning']}")
```

## Best Practices

1. **Be Specific**: Provide detailed requirements for better results
2. **Iterate**: Use suggestions to improve your blueprints
3. **Validate**: Always review AI-generated blueprints before deployment
4. **Use Dry-Run**: Test deployments before actual execution
5. **Monitor**: Track LLM performance and accuracy

## Limitations

- LLM may occasionally generate invalid YAML (validation will catch this)
- Complex architectures may need manual refinement
- Model has knowledge cutoff (trained on data up to certain date)
- Performance varies by hardware

## Next Steps

- [Quick Start Guide](QUICKSTART.md)
- [API Documentation](http://localhost:8000/docs)
- [Example Blueprints](../examples/blueprints/)
- [Contributing Guide](../CONTRIBUTING.md)
