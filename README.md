# AI-CDN: Infrastructure as Conversation

AI-CDN is an infrastructure orchestration platform that transforms the paradigm from "Infrastructure as Code" to "Infrastructure as Conversation". Manage your entire infrastructure stack through natural language interactions powered by AI.

## Key Concepts

### Abstraction Full-Stack
Unified management of network, hardware, and services through a conversational AI interface.

### 4-Layer Architecture

- **L4 Intent**: CLI/UI conversational interface
- **L3 Reasoning**: LLM (Qwen2-0.5B) with function calling
- **L2 Modeling**: Declarative SystemBlueprint (YAML)
- **L1 Execution**: Controller + Plugin-based Engine

### Human-in-the-Loop
IPR (Infrastructure Pull Request) system for pre-deployment review and approval.

### Composable Engines
Plugin architecture for every technology (Proxmox, MikroTik, Ansible, Docker, etc.)

## Features

### Time Traveler
Intelligent rollback of configurations with state management.

### Infrastructure Synthesizer
Clone and transform environments across different platforms.

### Observability-Driven
Auto-optimization based on SLO metrics and observability data.

## Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL (or SQLite for development)

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd cdn-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## Project Structure

```
ai_cdn/
├── api/          # FastAPI endpoints
├── core/         # Core business logic
├── engines/      # Infrastructure engine plugins
├── models/       # SQLAlchemy models
├── schemas/      # Pydantic schemas
├── cli/          # CLI interface
└── utils/        # Utility functions

tests/
├── unit/         # Unit tests
├── integration/  # Integration tests
└── e2e/          # End-to-end tests
```

## Development

### Code Quality

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability scanning
- **Pytest**: Testing framework

All these tools run automatically via pre-commit hooks.

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/test_blueprint.py

# Run with verbose output
pytest -v
```

### CI/CD

GitHub Actions automatically runs:
- Code quality checks (black, ruff, mypy, bandit)
- Tests across Python 3.10, 3.11, and 3.12
- Coverage reporting

## Usage

### CLI

```bash
# Start the AI-CDN CLI
ai-cdn

# Deploy a blueprint
ai-cdn deploy blueprint.yaml

# Check infrastructure status
ai-cdn status

# Rollback to previous state
ai-cdn rollback --to <commit-id>
```

### API

```bash
# Start the API server
uvicorn ai_cdn.api.main:app --reload

# Access API documentation
# http://localhost:8000/docs
```

## Architecture

### System Blueprint

SystemBlueprints are declarative YAML files that describe your infrastructure:

```yaml
version: "1.0"
name: "production-cluster"
resources:
  - type: compute
    name: web-server-01
    provider: proxmox
    specs:
      cpu: 4
      memory: 8GB
      storage: 100GB
```

### Engine Plugins

Each infrastructure provider is implemented as a plugin implementing the `Engine` interface:

```python
from ai_cdn.engines.base import Engine

class ProxmoxEngine(Engine):
    async def deploy(self, blueprint: SystemBlueprint) -> DeploymentResult:
        # Implementation
        pass
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT

## Roadmap

### Week 1: Foundations
- [x] Project scaffolding
- [ ] Database setup
- [ ] Base models
- [ ] Controller API

### Week 2: Core Features
- [ ] Blueprint parser
- [ ] Engine interface
- [ ] First engine implementation (FakeEngine)
- [ ] CLI basics

### Week 3: Integration
- [ ] Real engine plugin (e.g., Proxmox)
- [ ] IPR system
- [ ] Observability hooks
- [ ] Documentation

## Support

For questions and support, please open an issue on GitHub.
