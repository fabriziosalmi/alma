---
layout: home

hero:
  name: ALMA
  text: Autonomous Language Model Architecture
  tagline: Infrastructure as Conversation - Manage your infrastructure using natural language
  image:
    src: /alma/terminal.svg
    alt: ALMA Terminal Demo
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
    details: Describe your infrastructure needs in plain English and let ALMA generate blueprints based on your input.
  
  - title: Multi-Provider Support
    details: Deploy to Kubernetes, Proxmox, or Docker through a unified interface.
  
  - title: Infrastructure Approval
    details: Review, approve, and track deployment requests with a built-in approval workflow.
  
  - title: LLM-Powered Orchestration
    details: Leverage configurable LLM backends for intent parsing, resource suggestions, and security auditing.
  
  - title: Real-time Monitoring
    details: Track deployments, metrics, and system health with Prometheus integration and streaming updates.
  
  - title: Modern Stack
    details: Built with FastAPI, LangGraph, and Pydantic. Designed for reliability and type safety.
---

## Quick Example

Conversational Infrastructure Management:

```bash
# 1. Clone & Configure
git clone https://github.com/fabriziosalmi/alma.git
cd alma
cp .env.example .env

# 2. Start ALMA Stack (API + Web + Redis)
docker compose up -d

# 3. Chat with your Infrastructure
# Open http://localhost:3000
```

## Core Features
 
### Quick Wins (v0.8.5 - v0.8.8)
- **Docker Engine**: Native support for managing containers with robust logging.
- **Live Dashboard**: Visualize system resources (VMs, Containers) in real-time.
- **Resilience**: Implemented Circuit Breaker and Retry patterns for core system stability.
- **Test Coverage**: Significantly improved unit test coverage (~30%) for Core, Engines, and API.
- **The Council**: Multi-Agent system where specialized AI agents (Architect, SecOps, FinOps) debate infrastructure decisions.
- **GraphQL API**: Flexible data querying (`/graphql`) powered by Strawberry.

### LangGraph Orchestration
ALMA uses a state machine to handle complex deployment workflows, error recovery, and verification loops.

### MCP Native
Built on the **Model Context Protocol**, allowing integration with Claude Desktop, Cursor, and other AI agents.

### Proxmox Engine
Engine with task-aware waiting (no more race conditions), dual SSH/API modes, and automatic template management.

### Security
Built-in security auditing, compliance checking, and best practices enforcement for production deployments.

### Scalable Architecture

Horizontally scalable design with support for distributed deployments and high-throughput workloads.

## Roadmap

### Intelligent Orchestration (In Progress)
- **Multi-Agent Architecture**: Specialized agents for Architecture, Security, and Cost.
- **Proactive Security**: Pre-deployment vulnerability scanning in IPRs.

### Predictive Operations (Planned)
- **Anomaly Detection**: ML-based resource usage analysis.
- **Capacity Forecasting**: Historical data-driven scaling predictions.
- **Auto-Remediation**: Automated recovery runbooks.

### Universal Abstraction (Planned)
- **Cloud Portability**: Abstracted blueprints for AWS/Azure/GCP migration.
- **Hybrid Deployment**: Unified management for On-Prem and Cloud.

## Getting Started

<div class="vp-doc">

1. **[Quick Start Guide](/QUICKSTART)** - Get up and running quickly
2. **[Architecture Overview](/ARCHITECTURE)** - Understand ALMA's design
3. **[API Reference](/API_REFERENCE)** - Complete API documentation
4. **[Production Deployment](/PRODUCTION_DEPLOYMENT)** - Deploy to production

</div>

## Community & Support

- [GitHub Discussions](https://github.com/fabriziosalmi/alma/discussions)
- [Issue Tracker](https://github.com/fabriziosalmi/alma/issues)
