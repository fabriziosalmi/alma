# ALMA: Infrastructure as Conversation

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/alma.svg)](https://pypi.org/project/alma/)
[![Status](https://img.shields.io/badge/Status-Resilient_Beta-purple.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Policy](https://img.shields.io/badge/Policy-Resiliency-green.svg)](SECURITY.md)

**Stop writing YAML. Start conversing.**
ALMA (Autonomous Language Model Architecture) is a production-ready infrastructure orchestration platform that combines natural language interfaces with robust execution engines.

## Core Principles

1. **Security First**: Argon2id authentication, input validation, rate limiting
2. **Type Safety**: Pydantic models throughout, strict validation
3. **Auditability**: Event Sourcing for complete audit trail (compliance-ready)
4. **Reliability**: Saga Pattern for automatic rollback on failures

## Key Features

## Why ALMA?

1.  **Production-Ready Security**: Standard WAF patterns (SQL injection, XSS, path traversal) with input size limits and rate limiting.
2.  **Type-Safe Architecture**: Pydantic models throughout, proper exception handling, and strict validation.
3.  **Real Cloud Integration**: Actual pricing APIs (Infracost, AWS) instead of hardcoded estimates.

### Zero-Energy Defense

Input validation before it reaches the core:

- **L0 (Regex Guard)**: Blocks known malicious patterns (SQL injection, XSS, path traversal, code injection).
- **L2 (Size Limits)**: 2KB query parameters, 1MB request body.
- **L3 (Rate Limiting)**: Redis-backed rate limiting per IP/API key.

### Developer-Friendly Error Handling

ALMA provides clear error messages with proper debugging support:
- **Debug Mode**: Use `--debug` flag for full stack traces
- **Production Mode**: User-friendly error messages without exposing internals
- **Proper Logging**: All errors logged with full context for ops teams

### TUI Dashboard
Real-time terminal UI (`ALMA monitor`) featuring:
- **Live Neural Status**: Watch the switch between Cloud and Local brain.
- **Immune Activity**: See blocked threats in real-time.
- **System Health**: Latency, tokens/sec, and resource usage.

## Architecture

```mermaid
graph TD
    User[User / CLI] --> API[ALMA API FastAPI]
    API --> Immune[Immune System L0/L0.5]
    Immune --> Auth[Auth and Rate Limit]
    Auth --> Orch[Cognitive Orchestrator L4]
    
    subgraph "The Brain L3"
        Orch --> Cloud[Tier 1: Cloud LLM]
        Orch --> Local[Tier 2: Local Mesh]
        Orch --> Panic[Tier 3: Panic Mode]
    end
    
    Orch --> Tools[Infrastructure Tools]
    Tools --> Engines[Execution Layer L1]
    Engines --> K8s[Kubernetes]
    Engines --> Prox[Proxmox]
    Engines --> Docker[Docker]
```

## Quick Start

### Prerequisites
- Python 3.10+
- Docker (for metrics stack)
- LM Studio (optional, for local fallback)

### Installation

1.  **Install via PyPI**:
    ```bash
    pip install alma
    ```

2.  **Initialize the Brain**:
    ```bash
    # Start the API Server
    alma start-server
    ```

3.  **Launch the Dashboard**:
    ```bash
    # In a new terminal
    alma monitor
    ```

## Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Complete manual for daily usage.
- **[API Reference](docs/API_REFERENCE.md)**: Detailed endpoint documentation.
- **[Security Policy](SECURITY.md)**: Vulnerability reporting and security features.
- **[Contributing](CONTRIBUTING.md)**: Setup guide for developers.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment and submit Pull Requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.