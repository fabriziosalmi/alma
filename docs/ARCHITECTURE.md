# ALMA Architecture

This document provides a comprehensive overview of ALMA's architecture, design principles, and implementation details.

## Table of Contents

- [Overview](#overview)
- [4-Layer Architecture](#4-layer-architecture)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Design Principles](#design-principles)
- [Technology Stack](#technology-stack)

## Overview

ALMA follows a **4-layer architecture** that separates concerns and enables clean abstractions:

```
┌───────────────────────────────────────────────────────────┐
│                   L4: Intent Layer                        │
│           User interfaces (CLI, API, Web UI)              │
└─────────────────────┬─────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────────┐
│             L3: Reasoning & Orchestration                 │
│   1. Intent Parsing (Qwen/LLM)                            │
│   2. Resilient Workflow (LangGraph State Machine)         │
│      [Validate -> Check -> Heal -> Execute -> Verify]     │
└─────────────────────┬─────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────────┐
│                L2: Interface Layer                        │
│             Model Context Protocol (MCP) Server           │
│      Standardized Tooling for LLMs (List, Deploy, etc.)   │
└─────────────────────┬─────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────────┐
│               L1: Execution Layer                         │
│     ProxmoxEngine (Task-Aware) + Docker + K8s             │
└───────────────────────────────────────────────────────────┘
```

## 4-Layer Architecture

### Layer 4: Intent Layer

**Purpose**: User interaction and interface management

**Components**:
- **CLI** (`alma/cli/`): Command-line interface using Typer
- **REST API** (`alma/api/`): FastAPI-based HTTP API
- **Web UI** (`alma-web/`): React-based browser dashboard

**Key Features**:
- Multiple input formats (natural language, YAML, JSON)
- Rich output formatting (tables, progress bars)
- Interactive mode for complex workflows
- API key authentication (configurable)

**Example CLI Commands**:
```bash
alma deploy blueprint.yaml
alma council convene "web app with database"
alma templates list
alma dashboard
```

**Example API Calls**:
```http
POST /api/v1/conversation/generate-blueprint
POST /api/v1/blueprints/
POST /api/v1/ipr/
GET /api/v1/blueprints/{id}/deploy
```

### Layer 3.5: Cognitive Layer (The Brain)

**Purpose**: Acts as a middleware between raw user intent and LLM execution. It provides safety, context, and personality.

**Component**: `alma/core/cognitive.py`

**Key Sub-Systems:**

1.  **Context Tracker (FocusContext)**
    *   *Responsibility*: Remembers what resource we are talking about.
    *   *Logic*: If user says "Scale it to 5", the tracker resolves "it" to the `active_resource_id` (e.g., `vm-web-01`). Handles context switching detection.

2.  **Risk Guard (RiskProfile)**
    *   *Responsibility*: Prevents catastrophic errors driven by emotion or haste.
    *   *Matrix*:
        *   `High Frustration` + `Destructive Intent` = **BLOCK**
        *   `Low Frustration` + `Destructive Intent` = **CONFIRMATION REQUIRED**
        *   `Any Emotion` + `Read Intent` = **ALLOW**

3.  **Adaptive Persona Engine**
    *   *Responsibility*: Modulates the tone of voice.
    *   *Modes*:
        *   **ARCHITECT**: Verbose, explanatory, suggests best practices. (Trigger: `create`, `design`)
        *   **OPERATOR**: Concise, JSON-heavy, status-focused. (Trigger: `deploy`, `scale`)
        *   **MEDIC**: Systematic, inquisitive, reassuring. (Trigger: `troubleshoot`, `fix`)



### Layer 2: Modeling Layer

**Purpose**: Declarative infrastructure representation

**Components**:
- **Schemas** (`alma/schemas/`): Pydantic models for validation
- **Database Models** (`alma/models/`): SQLAlchemy ORM models
- **Blueprint Parser**: YAML ↔ Python object conversion

**Blueprint Structure**:
```yaml
version: "1.0"
name: my-infrastructure
description: "Production web application"

resources:
  - type: compute | network | storage | service
    name: resource-name
    provider: proxmox | docker | fake
    specs:
      # Provider-specific specifications
    dependencies:
      - other-resource-name
    metadata:
      # Additional metadata

metadata:
  environment: production
  owner: platform-team
```

**Validation**:
- Schema validation (Pydantic)
- Dependency graph validation
- Provider compatibility checks
- Resource quota checks

### Layer 1: Execution Layer

**Purpose**: Actual infrastructure provisioning and management

**Components**:
- **Engine Interface** (`alma/engines/base.py`): Abstract base class
- **Engine Plugins**: Provider-specific implementations
  - FakeEngine: Testing and development
  - ProxmoxEngine: Proxmox VE integration
  - (Future) DockerEngine, AnsibleEngine, etc.
- **Controller**: Orchestrates deployment workflow
- **State Manager**: Tracks resource state

**Engine Interface**:
```python
class Engine(ABC):
    async def validate_blueprint(blueprint) -> bool
    async def deploy(blueprint) -> DeploymentResult
    async def get_state(resource_id) -> ResourceState
    async def destroy(resource_id) -> bool
    async def rollback(deployment_id) -> bool
    async def health_check() -> bool
```

**Deployment Flow**:
```
1. Validate blueprint
2. Resolve dependencies
3. For each resource in topological order:
   a. Check if exists
   b. Create or update
   c. Verify state
   d. Update database
4. Return deployment result
```

## Component Details

### Database Layer

**Technology**: PostgreSQL (production) / SQLite (development)

**Tables**:
- `system_blueprints`: Stores blueprint definitions
- `infrastructure_pull_requests`: IPR workflow
- (Future) `deployments`: Deployment history
- (Future) `resource_states`: Current infrastructure state

**Migrations**: Alembic for schema versioning

**Example Schema**:
```sql
CREATE TABLE system_blueprints (
    id INTEGER PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    resources JSON NOT NULL,
    metadata JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### API Layer

**Framework**: FastAPI

**Routes**:
```
/                          # Health check
/api/v1/blueprints/*       # Blueprint CRUD
/api/v1/ipr/*              # IPR workflow
/api/v1/conversation/*     # AI chat
```

**Features**:
- OpenAPI documentation (`/docs`)
- Async request handling
- CORS support
- Dependency injection
- Automatic validation

### LLM Integration

**Model**: Configurable (defaults to `Qwen/Qwen2.5-0.5B-Instruct` when using local Transformers; any OpenAI-compatible endpoint is also supported)

**Architecture**:
```
User Input
    ↓
Prompt Template
    ↓
LLM Processing (Qwen2.5)
    ↓
Response Parsing
    ↓
Structured Output
```

**Prompt Engineering**:
- System prompts define AI role
- Few-shot examples for consistency
- JSON/YAML extraction
- Temperature control for creativity

## Data Flow

### Blueprint Creation Flow

```
1. User Request (CLI/API)
   ↓
2. Intent Classification (LLM)
   ↓
3. Blueprint Generation (LLM + Templates)
   ↓
4. Validation (Pydantic schemas)
   ↓
5. Save to Database (SQLAlchemy)
   ↓
6. Return Blueprint ID
```

### Deployment Flow

```
1. Create IPR (optional)
   ↓
2. Review & Approval (human)
   ↓
3. Load Blueprint
   ↓
4. Select Engine (based on provider)
   ↓
5. Validate with Engine
   ↓
6. Resolve Dependencies
   ↓
7. Deploy Resources (topological order)
   ↓
8. Update State
   ↓
9. Return Deployment Result
```

### Rollback Flow

```
1. Identify Deployment
   ↓
2. Load Target State
   ↓
3. Calculate Diff
   ↓
4. Generate Rollback Plan
   ↓
5. Execute Rollback (reverse order)
   ↓
6. Verify State
   ↓
7. Update Database
```

## Design Principles

### 1. Separation of Concerns

Each layer has a single, well-defined responsibility:
- **Intent**: User interaction
- **Reasoning**: Intelligence
- **Modeling**: Data representation
- **Execution**: Infrastructure operations

### 2. Plugin Architecture

Engines are pluggable modules that implement a common interface:
- Easy to add new providers
- Testable with FakeEngine
- Provider-agnostic core logic

### 3. Declarative Infrastructure

Blueprints describe **what**, not **how**:
- Idempotent operations
- Version-controlled
- Provider-independent (mostly)

### 4. Human-in-the-Loop

Critical operations require human approval:
- IPR system for deployments
- Dry-run mode for testing
- Rollback capabilities

### 5. Async Everything

All I/O operations are async:
- Better resource utilization
- Handles concurrent requests
- Non-blocking LLM inference

### 6. Type Safety

Strong typing throughout:
- Pydantic for runtime validation
- MyPy for static type checking
- Explicit contracts between layers

## Technology Stack

### Core
- **Python 3.10+**: Modern async/await
- **FastAPI**: High-performance API framework
- **Pydantic**: Data validation
- **SQLAlchemy 2.0**: Async ORM
- **Alembic**: Database migrations

### AI/ML
- **Transformers** (optional): Hugging Face library for local LLM inference
- **PyTorch** (optional): Required when using local Transformers models
- **LangGraph / LangChain**: Workflow orchestration and LLM tooling

### CLI
- **Typer**: CLI framework
- **Rich**: Terminal formatting
- **PyYAML**: YAML processing

### Database
- **PostgreSQL**: Production database
- **SQLite**: Development database (default)
- **AsyncPG**: Async PostgreSQL driver

### Testing
- **Pytest**: Test framework
- **HTTPX**: Async HTTP client
- **Coverage**: Code coverage

### DevOps
- **Docker**: Containerization
- **GitHub Actions**: CI/CD
- **Pre-commit**: Code quality hooks

## Performance Considerations

### LLM Optimization
- Singleton pattern for model caching
- Warmup on startup
- Thread pool for inference
- Device selection (CPU/GPU/MPS)

### Database Optimization
- Connection pooling
- Async queries
- Indexes on foreign keys
- JSON field indexing (PostgreSQL)

### API Optimization
- Async request handling
- Response caching (future)
- Pagination for large results
- Streaming for long operations

## Security

### Authentication
- API key authentication (configurable via `ALMA_API_KEY` environment variable)
- OAuth2 integration (planned)
- Role-based access control (planned)

### Data Protection
- Environment variables for secrets
- No secrets in blueprints
- Encrypted database connections

### Audit Trail
- All changes logged
- IPR approval workflow
- Deployment history

## Scalability

### Horizontal Scaling
- Stateless API servers
- Shared database
- Load balancer ready

### Vertical Scaling
- Async I/O handles many connections
- LLM model size configurable
- Database connection pooling

## Current Status and Roadmap

### Completed
- [x] Prometheus metrics (`alma/middleware/metrics.py`)
- [x] Web UI — React-based dashboard (`alma-web/`)
- [x] Event sourcing (`alma/core/events.py`)
- [x] CQRS pattern (`alma/core/cqrs.py`)
- [x] Docker engine (`alma/engines/docker.py`)
- [x] WebSocket support for real-time updates (`/ws/deployments`)
- [x] GraphQL API (`/graphql`) — basic system status queries
- [x] API key authentication

### Planned
- [ ] Multi-tenancy
- [ ] RBAC (Role-Based Access Control)
- [ ] Native Terraform Provider (Go wrapper)
- [ ] Kubernetes Operator (CRD Controller)

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [Transformers](https://huggingface.co/docs/transformers/)

---

**Next**: [Engines Documentation](ENGINES.md)
