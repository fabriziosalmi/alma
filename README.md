# ALMA: Infrastructure as Conversation

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/alma.svg)](https://pypi.org/project/alma/)
[![Status](https://img.shields.io/badge/Status-Sentient_Beta-purple.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/alma.svg)](https://pypi.org/project/alma/)

**Stop writing YAML. Start conversing.**
ALMA is the first **Cognitive Infrastructure Platform**. It doesn't just execute commands; it understands context, assesses risk, and adapts its persona to your emotional state.

## Key Features

### Cognitive Engine
ALMA is not a stateless chatbot. It has a "Brain":
- **Risk Assessment**: Detects frustration + high-risk commands (e.g., "DELETE DB") and activates safety overrides.
- **Context Awareness**: Understands if you are shifting topics (e.g., from Network to Storage) and adjusts focus.
- **Adaptive Persona**: Switches dynamically between **Architect** (Creative), **Operator** (Precise), and **Medic** (Troubleshooter) based on your intent.

### TUI Dashboard
Real-time terminal UI (`ALMA monitor`) featuring:
- **Live Neural Status**: Watch the LLM think in real-time.
- **Deployment Tracking**: Progress bars for your infrastructure rollouts.
- **System Health**: API latency, tokens/sec, and resource usage.

### Core Capabilities
- **Natural Language**: "Deploy a K8s cluster with monitoring" -> Done.
- **IPR System**: Infrastructure Pull Requests for human-in-the-loop safety.
- **Streaming**: Real-time responses (SSE) for instant feedback.
- **Templates**: 10+ production-ready blueprints included.

## Installation

### From PyPI (Recommended)

```bash
pip install alma
```

### From GitHub Releases

Download the latest wheel for your platform from [GitHub Releases](https://github.com/fabriziosalmi/alma/releases):

```bash
# Linux/macOS
pip install https://github.com/fabriziosalmi/alma/releases/download/v0.1.0/alma-0.1.0-py3-none-any.whl

# Or download and install locally
wget https://github.com/fabriziosalmi/alma/releases/download/v0.1.0/alma-0.1.0-py3-none-any.whl
pip install alma-0.1.0-py3-none-any.whl
```

### Development Installation

For contributing or local development:

```bash
git clone https://github.com/fabriziosalmi/alma.git
cd alma
pip install -e '.[dev]'
```

This installs ALMA in editable mode with development dependencies (pytest, black, ruff, mypy).

## Architecture

```
┌──────────────────────────────────────────────────────┐
│ L5: User Experience (Sentient Interface) │
│ TUI Dashboard | CLI | Web UI │
└──────────────┬───────────────────────────────────────┘
│
┌──────────────▼───────────────────────────────────────┐
│ L4: Cognitive Layer (The Brain) │
│ Risk Guard • Context Tracker • Persona Switcher │
└──────────────┬───────────────────────────────────────┘
│
┌──────────────▼───────────────────────────────────────┐
│ L3: Reasoning Layer (LLM) │
│ Qwen/Sonnet + Function Calling (13 Tools) │
└──────────────┬───────────────────────────────────────┘
│
┌──────────────▼───────────────────────────────────────┐
│ L2: Modeling & L1 Execution │
│ Blueprints (YAML) -> Engines (K8s, Proxmox, Docker) │
└──────────────────────────────────────────────────────┘
```

## Quick Start

### Installation
```bash
git clone https://github.com/fabriziosalmi/alma.git
cd alma
pip install -e .
```

### Launch the Brain
Start the API Server:
```bash
python run_server.py
```

Open the Dashboard (New terminal):
```bash
python -m alma.cli.dashboard
```

### Interact
```bash
# Ask for a design (Architect Persona activates)
ALMA chat "Design a high-availability redis cluster"

# Execute a risky command (Risk Guard activates)
ALMA chat "DESTROY THE PRODUCTION DATABASE NOW"
# Response: "CRITICAL RISK: High frustration detected. Operation blocked."
```

### 📚 Documentation
- **Cognitive Guide** - Deep dive into the AI Brain.
- **User Guide** - Complete manual.
- **API Reference** - Endpoints & Schemas.

### 🤝 Contributing
We are building the future of Ops. Join us.
See `CONTRIBUTING.md`.