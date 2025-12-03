---
layout: home

hero:
  name: ALMA
  text: Autonomous Language Model Architecture
  tagline: Infrastructure as Conversation - Manage your infrastructure using natural language
  image:
    src: /alma/logo.svg
    alt: ALMA Logo
  actions:
    - theme: brand
      text: Get Started
      link: /QUICKSTART
    - theme: alt
      text: View on GitHub
      link: https://github.com/fabriziosalmi/alma
    - theme: alt
      text: API Reference
      link: /API_REFERENCE

features:
  - title: Natural Language Interface
    details: Describe your infrastructure needs in plain English and let ALMA's AI generate production-ready blueprints automatically.
  
  - title: Multi-Provider Support
    details: Deploy to Kubernetes, Proxmox, or any infrastructure provider through a unified, conversational interface.
  
  - title: Infrastructure Pull Requests
    details: Review, approve, and track infrastructure changes just like code changes with built-in versioning and rollback.
  
  - title: AI-Powered Orchestration
    details: Leverage advanced LLM capabilities for intelligent resource sizing, cost optimization, and security auditing.
  
  - title: Real-time Monitoring
    details: Track deployments, metrics, and system health with Prometheus integration and streaming updates.
  
  - title: Production Ready
    details: Built with FastAPI, tested extensively, and designed for high-availability production environments.
---

## Quick Example

Transform natural language into infrastructure:

```bash
# Install ALMA
pip install alma

# Start the server
alma serve

# Use the API
curl -X POST http://localhost:8000/api/v1/conversation/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a highly available web application with 3 servers"
  }'
```

## Core Features

### Blueprint Generation

Generate infrastructure blueprints from natural language descriptions with AI-powered optimization and cost estimation.

### Security First

Built-in security auditing, compliance checking, and best practices enforcement for production deployments.

### Scalable Architecture

Horizontally scalable design with support for distributed deployments and high-throughput workloads.

## Getting Started

<div class="vp-doc">

1. **[Quick Start Guide](/QUICKSTART)** - Get up and running in 5 minutes
2. **[Architecture Overview](/ARCHITECTURE)** - Understand ALMA's design
3. **[API Reference](/API_REFERENCE)** - Complete API documentation
4. **[Production Deployment](/PRODUCTION_DEPLOYMENT)** - Deploy to production

</div>

## Community & Support

- [GitHub Discussions](https://github.com/fabriziosalmi/alma/discussions)
- [Issue Tracker](https://github.com/fabriziosalmi/alma/issues)
- [Documentation](https://alma-docs.dev)
- [Enterprise Support](mailto:enterprise@alma.dev)
