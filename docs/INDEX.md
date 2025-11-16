# AI-CDN Documentation

**Infrastructure as Conversation** - Complete documentation for the AI-CDN platform.

## 📚 Table of Contents

### Getting Started
- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Installation](INSTALLATION.md)** - Detailed installation instructions
- **[Configuration](CONFIGURATION.md)** - Configuration options and best practices

### Core Concepts
- **[Architecture](ARCHITECTURE.md)** - System architecture and design
- **[Blueprints](BLUEPRINTS.md)** - Understanding infrastructure blueprints
- **[Engines](ENGINES.md)** - Infrastructure provider plugins

### Features
- **[LLM Integration](LLM_GUIDE.md)** - AI-powered infrastructure management
- **[IPR System](IPR.md)** - Infrastructure Pull Requests
- **[CLI Reference](CLI.md)** - Command-line interface guide
- **[API Reference](API.md)** - REST API documentation

### Development
- **[Testing Guide](TESTING.md)** - Writing and running tests
- **[Contributing](../CONTRIBUTING.md)** - How to contribute
- **[Plugin Development](PLUGIN_DEVELOPMENT.md)** - Creating engine plugins

### Deployment
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment
- **[Security](SECURITY.md)** - Security best practices
- **[Monitoring](MONITORING.md)** - Observability and metrics

### Advanced
- **[Database Migrations](MIGRATIONS.md)** - Managing schema changes
- **[Performance Tuning](PERFORMANCE.md)** - Optimization tips
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## 🎯 Quick Links

### For Users
- [What is AI-CDN?](#what-is-ai-cdn)
- [Why use AI-CDN?](#why-use-ai-cdn)
- [Quick Start](QUICKSTART.md)
- [Examples](../examples/)

### For Developers
- [Architecture](ARCHITECTURE.md)
- [API Reference](API.md)
- [Contributing](../CONTRIBUTING.md)

### For DevOps
- [Deployment](DEPLOYMENT.md)
- [Monitoring](MONITORING.md)
- [Security](SECURITY.md)

## What is AI-CDN?

AI-CDN is an **infrastructure orchestration platform** that transforms the traditional "Infrastructure as Code" paradigm into "Infrastructure as Conversation". It uses AI to help you design, deploy, and manage infrastructure through natural language interactions.

### Key Features

#### 🤖 AI-Powered
- **Natural Language Understanding**: Describe what you want, get infrastructure
- **Smart Suggestions**: AI-powered improvement recommendations
- **Security Audits**: Automated security analysis
- **Resource Sizing**: Intelligent resource recommendations

#### 🏗️ Infrastructure Management
- **Multi-Provider**: Proxmox, Docker, Ansible, and more
- **Declarative Blueprints**: YAML-based infrastructure definitions
- **Version Control**: Git-friendly infrastructure code
- **State Management**: Track infrastructure state over time

#### 🔒 Safe & Auditable
- **IPR (Infrastructure Pull Requests)**: Human-in-the-loop approvals
- **Rollback Support**: Time-travel to previous states
- **Audit Trail**: Complete change history
- **Dry-Run Mode**: Validate before deploying

#### 🚀 Developer Friendly
- **REST API**: Comprehensive API for automation
- **CLI Tools**: Powerful command-line interface
- **Python SDK**: Programmatic access
- **Extensible**: Plugin architecture for custom engines

## Why Use AI-CDN?

### Traditional Infrastructure Management
```yaml
# You need to know:
# - Exact resource specifications
# - Provider-specific syntax
# - Best practices and patterns
# - Security configurations

resource "proxmox_vm" "web" {
  name = "web-01"
  cores = 4
  memory = 8192
  # ... 50 more lines of configuration
}
```

### With AI-CDN
```bash
# Just describe what you need
ai-cdn generate "I need a high-availability web application"

# AI-CDN will:
# ✓ Design optimal architecture
# ✓ Configure security
# ✓ Add redundancy
# ✓ Set up monitoring
# ✓ Generate complete blueprint
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    L4: Intent Layer                     │
│              CLI / Web UI / REST API                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 L3: Reasoning Layer                     │
│        Qwen3 LLM + Conversational Orchestrator          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 L2: Modeling Layer                      │
│         SystemBlueprints (YAML) + Validation            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                L1: Execution Layer                      │
│    Controller + Engine Plugins (Proxmox, Docker, ...)  │
└─────────────────────────────────────────────────────────┘
```

See [Architecture](ARCHITECTURE.md) for detailed explanation.

## Project Structure

```
ai_cdn/
├── api/                    # FastAPI application
│   ├── routes/            # API endpoints
│   └── main.py            # App initialization
├── cli/                   # CLI interface
│   └── main.py            # CLI commands
├── core/                  # Core functionality
│   ├── config.py          # Configuration
│   ├── database.py        # Database setup
│   ├── llm.py             # LLM base
│   ├── llm_qwen.py        # Qwen3 implementation
│   ├── llm_orchestrator.py # Enhanced orchestrator
│   ├── llm_service.py     # LLM service layer
│   └── prompts.py         # Prompt templates
├── engines/               # Infrastructure engines
│   ├── base.py            # Engine interface
│   ├── fake.py            # Testing engine
│   └── proxmox.py         # Proxmox engine
├── models/                # Database models
│   ├── blueprint.py       # Blueprint model
│   └── ipr.py             # IPR model
└── schemas/               # Pydantic schemas
    ├── blueprint.py       # Blueprint schemas
    └── ipr.py             # IPR schemas
```

## Use Cases

### 1. Development Environments
```bash
ai-cdn generate "Create a development environment for a Django app"
# → Complete stack with PostgreSQL, Redis, and Django container
```

### 2. Production Deployments
```bash
ai-cdn deploy production.yaml --review
# → Creates IPR for team review before deployment
```

### 3. Infrastructure Audits
```bash
ai-cdn audit my-infrastructure.yaml
# → AI-powered security and best practices analysis
```

### 4. Migration Planning
```bash
ai-cdn migrate --from aws --to proxmox current-infra.yaml
# → Generates migration plan and new blueprint
```

## Getting Help

### Documentation
- Read through the guides in order
- Check examples in `examples/` folder
- Review API docs at `/docs` endpoint

### Community
- GitHub Issues: Bug reports and feature requests
- Discussions: Questions and ideas
- Discord: Real-time chat (coming soon)

### Support
- 📧 Email: support@ai-cdn.io
- 💬 Discord: [Join server](https://discord.gg/ai-cdn)
- 🐛 Issues: [GitHub Issues](https://github.com/ai-cdn/ai-cdn/issues)

## Next Steps

### New Users
1. [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
2. [Blueprints Guide](BLUEPRINTS.md) - Learn blueprint syntax
3. [Examples](../examples/) - See real-world blueprints

### Developers
1. [Architecture](ARCHITECTURE.md) - Understand the system
2. [API Reference](API.md) - Explore the API
3. [Contributing](../CONTRIBUTING.md) - Start contributing

### DevOps Engineers
1. [Deployment Guide](DEPLOYMENT.md) - Deploy in production
2. [Security](SECURITY.md) - Secure your deployment
3. [Monitoring](MONITORING.md) - Set up observability

## Version Information

- **Current Version**: 0.1.0
- **Python**: 3.10+
- **License**: MIT
- **Status**: Alpha

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for version history.

---

**AI-CDN** - Infrastructure as Conversation
Made with ❤️ by the AI-CDN Team
