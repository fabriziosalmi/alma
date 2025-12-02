# ALMA: Infrastructure as Conversation

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/alma.svg)](https://pypi.org/project/alma/)
[![Status](https://img.shields.io/badge/Status-Resilient_Beta-purple.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Protocol](https://img.shields.io/badge/Protocol-Ahimsa-green.svg)](SECURITY.md)

**Stop writing YAML. Start conversing.**
ALMA is the first **Cognitive & Resilient Infrastructure Platform**.
It doesn't just execute commands; it protects resources, understands context, works offline, and adapts its persona to your emotional state.

## 🛡️ Protocol Ahimsa: The Core Philosophy
ALMA is built on the **Non-Violence** principle.
1.  **Silent Defense**: It doesn't fight attacks; it renders them irrelevant via Information Theory (Entropy & Compression filters).
2.  **Resource Respect**: It never wastes energy (LLM tokens) if a lighter solution (Regex/Local Model) suffices.
3.  **Local Sovereignty**: It refuses to die when the Cloud disconnects.

## Key Features

### 🧠 3-Tier Neural Brain (Local-First)
ALMA possesses a redundant cognitive architecture to ensure 100% uptime:
- **Tier 1 (Cloud)**: Uses primary models (OpenAI/Anthropic) for maximum reasoning power.
- **Tier 2 (Local Mesh)**: Automatically falls back to **local Qwen3** (via LM Studio) if internet fails. Maintains tool-use capabilities without data leaving your perimeter.
- **Tier 3 (Panic Mode)**: Degrades gracefully to a static "Medic" mode if all intelligence fails.

### 🛡️ Immune System (Powered by SILENCE)
Zero-energy defense mechanism that filters input before it touches the Brain:
- **L0 (Regex Guard)**: Blocks known malicious patterns (SQLi, Injection).
- **L0.5 (Entropy Guard)**: Uses Shannon Entropy to silently drop chaotic payloads (fuzzing/encryption).
- **L0.5 (Compression Trap)**: Detects and drops repetitive spam anomalies.

### ❤️ Empathetic Error Handling
ALMA eliminates "Cognitive Violence" (scary stacktraces):
- **Medic Persona**: Intercepts system crashes and translates technical errors into calm, diagnostic dialogue.
- **Risk Guard**: Detects user frustration and blocks destructive commands (e.g., "DELETE DB") until emotional stability returns.

### TUI Dashboard
Real-time terminal UI (`ALMA monitor`) featuring:
- **Live Neural Status**: Watch the switch between Cloud and Local brain.
- **Immune Activity**: See blocked threats in real-time.
- **System Health**: Latency, tokens/sec, and resource usage.

## Architecture

```mermaid
graph TD
    User[User / CLI] --> API[ALMA API (FastAPI)]
    API --> Immune[Immune System (L0/L0.5)]
    Immune --> Auth[Auth & Rate Limit]
    Auth --> Orch[Cognitive Orchestrator (L4)]
    
    subgraph "The Brain (L3)"
        Orch --> Cloud[Tier 1: Cloud LLM (Qwen/OpenAI)]
        Orch --> Local[Tier 2: Local Mesh (LM Studio)]
        Orch --> Panic[Tier 3: Panic Mode (TinyLLM)]
    end
    
    Orch --> Tools[Infrastructure Tools]
    Tools --> Engines[Execution Layer (L1)]
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