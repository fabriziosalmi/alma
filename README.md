# ALMA: Infrastructure as Conversation

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compliant](https://img.shields.io/badge/MCP-Compliant-orange.svg)](https://modelcontextprotocol.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestrated-blueviolet.svg)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Stop writing YAML. Start conversing.**  
ALMA (Autonomous Language Model Architecture) is a resilient, self-healing infrastructure orchestration platform. It combines natural language interfaces with **LangGraph** state machines and the **Model Context Protocol (MCP)** to reliably deploy and manage resources on Proxmox and beyond.

## Core Capabilities

- **🗣️ Natural Language Interface**: Chat with your infrastructure ("Deploy an Alpine LXC named web-01").
- **🧠 Resilient State Machine**: deployments are managed by a **LangGraph** workflow that handles validation, execution, and verification with automatic retries.
- **🛡️ Self-Healing**: Automatically detects missing dependencies (e.g., templates) and resolves them (downloads) without user intervention.
- **🔌 MCP Native**: Exposes infrastructure tools via a standard **Model Context Protocol** server, making it compatible with Anthropic Claude, Google Gemini, and other LLMs.
- **⚡ Proxmox Integration**: Advanced engine with task-aware waiting, SSH/API dual-mode, and robust LXC/VM management.

## Architecture

ALMA uses a layered architecture designed for resilience:

```mermaid
graph TD
    User[User / Chat UI] --> API[FastAPI / Chat Stream]
    API --> Graph[LangGraph Orchestrator]
    
    subgraph Workflow [Resilient Deployment Workflow]
        Graph --> Parse[Parse Intent]
        Parse --> Validate[Validate Params]
        Validate --> Check[Check Resources]
        Check -- Missing Template --> Heal[Self-Healing / Download]
        Check -- Ready --> Exec[Execute Deployment]
        Exec --> Verify[Verify Deployment]
        Verify -- Retry Loop --> Verify
    end

    Exec --> MCP[MCP Server]
    MCP --> Engine[Proxmox Engine]
    Engine --> Proxmox[Proxmox VE API/SSH]
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Proxmox VE (Credentials)
- OpenAI/Anthropic/Google API Key (for LLM features)

### Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/fabriziosalmi/alma.git
    cd alma
    ```

2.  **Configure Environment**:
    ```bash
    cp .env.example .env
    # Edit .env with your Proxmox and LLM credentials
    ```

3.  **Launch with Docker Compose**:
    ```bash
    docker compose up -d --build
    ```

4.  **Access the Dashboard**:
    Open [http://localhost:3000](http://localhost:3000) to start chatting with your infrastructure.

## Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Complete manual for daily usage.
- **[Architecture](docs/ARCHITECTURE.md)**: Deep dive into LangGraph and MCP implementation.
- **[Contributing](CONTRIBUTING.md)**: Development setup.

## Community & Support
- [GitHub Discussions](https://github.com/fabriziosalmi/alma/discussions)
- [Issue Tracker](https://github.com/fabriziosalmi/alma/issues)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.