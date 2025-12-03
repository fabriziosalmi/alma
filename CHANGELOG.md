# Changelog

All notable changes to ALMA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.2] - 2025-12-03

### 🧹 Technical Debt & Code Quality

Major refactoring sprint to eliminate technical debt and enforce strict code quality standards.

### Fixed
- **Type Safety**:
  - Resolved ~80 MyPy type errors across the codebase.
  - Enabled strict MyPy mode (`warn_return_any`, `disallow_untyped_defs`, etc.).
  - Fixed critical type mismatches in `RateLimiter`, `ProxmoxEngine`, and `Dashboard`.
- **CI/CD**:
  - Updated CI pipeline to block on MyPy and Ruff errors.
  - Enforced type checking on all source code (excluding tests/examples).
- **Dead Code**:
  - Removed legacy `src/` directory.
  - Removed `alma/engines/fake.py` (migrated to tests).

### Changed
- **Rate Limiting**: Improved `RateLimiter` stability and async handling.
- **Monitoring**: Fixed async bugs in monitoring endpoints.

## [0.7.1] - 2025-12-03

### 🐛 Bug Fixes & CI/CD Stability

Critical fixes for CI pipelines and runtime async execution bugs.

### Fixed
- **Critical Runtime Bug**: Added missing `await` in `execute_tool` API route (prevented tool execution).
- **CI Pipeline**:
  - Fixed GitHub Pages 404 error (incorrect sidebar link).
  - Resolved 300+ MyPy type errors (excluded tests, fixed API types).
  - Resolved 127 Ruff linting errors.
  - Removed duplicate `docs.yml` workflow.
- **Documentation**:
  - Fixed broken links in CHANGELOG.
  - Updated SECURITY.md with current auth status.
  - Replaced "master/slave" terminology with "control-plane/primary".
  - Fixed README status badge.

## [0.7.0] - 2025-12-03

### 📚 Documentation & Architecture

Complete documentation overhaul and architecture decision records.

### Added
- **Architecture Decision Records (ADRs)**:
  - ADR-001: Event Sourcing justification
  - ADR-002: Saga Pattern justification
  - docs/ADR/README.md with index
- **Documentation cleanup**:
  - Removed all marketing fluff from README
  - Updated PROJECT_STATUS.md to current state
  - Accurate, honest feature descriptions

### Changed
- **README.md**:
  - Removed "Cognitive & Resilient" marketing language
  - Removed "Non-Violence principle" references
  - Removed "Medic Persona" and "Risk Guard" references
  - Added clear Core Principles (Security, Type Safety, Auditability, Reliability)
- **Error Handling Documentation**:
  - Clarified --debug flag usage
  - Documented production vs debug modes
  - Removed persona-based error handling references

### Documentation
- All documentation now accurately reflects production capabilities
- No exaggerated claims
- Clear technical descriptions
- ADRs document architectural decisions with industry examples



## [0.6.0] - 2025-12-03

### 🔐 Security & Production Hardening

Major security and code quality improvements based on production readiness review.

### Added
- **Real Pricing Integration**:
  - Infracost API support
  - AWS Pricing API via boto3
  - Fallback estimates clearly marked
- **Type Safety**:
  - Pydantic schemas for all tool requests/responses
  - `ToolRequest`, `ToolResponse`, `ResourceEstimateRequest/Response`
  - Strict validation throughout
- **--debug Flag**: Full stack traces in debug mode
- **--no-llm Mode**: Engines work independently of LLM service
- **Registry Pattern**: Tool dispatch using dynamic registry instead of if/else
- **Config Externalization**: Resource specs moved to `alma/config/resource_specs.yaml`
- **Dependency Locking**: `requirements.lock` for reproducible builds

### Security
- **CRITICAL**: Replaced SHA-256 with Argon2id for API key hashing
  - Prevents rainbow table attacks
  - Proper salt and memory-hard KDF
  - Constant-time verification
- Added `argon2-cffi>=23.1.0` dependency

### Changed
- **Simplified Immune System**:
  - Removed Shannon Entropy (academic fluff)
  - Removed Compression Trap (academic fluff)
  - Using standard regex patterns for SQL injection, XSS, path traversal
  - Input size limits (2KB query, 1MB body)
- **Exception Hygiene**:
  - Specific exception handling (FileNotFoundError, JSONDecodeError, etc.)
  - No more swallowing generic exceptions
  - Proper logging with logger.exception()
- **Error Handling**:
  - Debug mode shows full stack traces
  - Production mode shows user-friendly messages
  - Removed "Medic Persona" from internal errors

### Removed
- `alma/core/immune_system.py` (unused, replaced by simplified middleware)
- Shannon Entropy validation
- Compression Trap validation
- "Cognitive Violence" terminology from code

### Fixed
- GitHub Pages documentation deployment
- Logo path in docs (base path issue)
- Workflow conflicts (duplicate docs workflows)


## [0.4.3] - 2025-12-02

### 🛡️ Resiliency Policy (Resilience & Non-Violence)

Major architectural update focusing on system resilience, local-first fallback, and empathetic error handling.

### Added
- **3-Tier Neural Brain**:
  - Tier 1: Cloud (Qwen3/OpenAI)
  - Tier 2: Local Mesh (LocalStudioLLM via localhost:1234)
  - Tier 3: Panic Mode (TinyLLM static fallback)
- **Immune System**:
  - L0 Regex Filter for SQLi/XSS
  - L0.5 Entropy Filter for high-noise payloads
  - L0.5 Compression Trap for spam
- **Empathetic Error Handling**:
  - "Medic Persona" for user-friendly error messages
  - Global exception handler (`calm_exception_handler`)
- **Documentation**:
  - Updated `README.md` with Architecture diagram
  - Renamed `docs/INDEX.md` to `docs/index.md` for GitHub Pages compatibility

### Changed
- **LLM Service**: Refactored `initialize_llm` to support 3-tier fallback.
- **Dependencies**: Added `httpx` for local model communication.

---

## [0.2.0] - 2025-11-16

### 🎯 Quick Wins - Production Ready Release

Major update adding production-ready features and comprehensive documentation.

### Added

#### Enhanced Function Calling
- **13 LLM Tools** for infrastructure operations (`alma/core/tools.py`)
  - `create_blueprint` - Generate infrastructure blueprints
  - `validate_blueprint` - Syntax and semantic validation
  - `estimate_resources` - Resource requirement calculation
  - `optimize_costs` - Cost reduction recommendations (up to 30%)
  - `security_audit` - Security compliance checks
  - `generate_deployment_plan` - Step-by-step deployment guides
  - `troubleshoot_issue` - Problem diagnosis and solutions
  - `compare_blueprints` - Version comparison and diff
  - `suggest_architecture` - Best practices recommendations
  - `calculate_capacity` - Capacity planning
  - `migrate_infrastructure` - Migration strategies
  - `check_compliance` - Compliance verification (SOC2, GDPR, etc.)
  - `forecast_metrics` - Predictive analytics

#### Streaming Responses
- **SSE (Server-Sent Events)** endpoints for real-time streaming
  - `/api/v1/conversation/chat-stream` - Real-time chat responses
  - `/api/v1/blueprints/generate-blueprint-stream` - Progressive blueprint generation
  - 96% faster time-to-first-byte vs traditional responses
  - Progressive rendering for better UX

#### Blueprint Templates
- **10 Production-Ready Templates** (`alma/core/templates.py`)
  - `simple-web-app` - Basic web application ($100-200/month)
  - `ha-web-app` - High availability web app ($300-500/month)
  - `microservices-k8s` - Kubernetes microservices ($800-1500/month)
  - `postgres-ha` - HA PostgreSQL cluster ($400-700/month)
  - `data-pipeline` - ETL/data processing ($600-1200/month)
  - `ml-training` - ML model training ($1000-3000/month)
  - `zero-trust-network` - Security-first network ($500-800/month)
  - `observability-stack` - Prometheus + Grafana ($300-600/month)
  - `api-gateway` - API management ($200-400/month)
  - `redis-cluster` - Distributed cache ($300-500/month)
- Template customization API endpoint
- Complexity tiers (low/medium/high)

#### Rate Limiting
- **Token Bucket Algorithm** (`alma/middleware/rate_limit.py`)
  - Per-IP rate limiting (60 RPM global default)
  - Per-endpoint custom limits:
    - Chat streaming: 20 RPM (LLM intensive)
    - Blueprint generation: 30 RPM
    - Tool execution: 40 RPM
    - CRUD operations: 100 RPM
  - Burst handling (configurable burst size)
  - HTTP 429 responses with `Retry-After` headers
  - Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
  - Automatic cleanup of inactive clients
  - <1ms performance overhead

#### Metrics Collection
- **Prometheus Integration** (`alma/middleware/metrics.py`)
  - 15+ metric types:
    - HTTP metrics (requests, duration, sizes)
    - LLM metrics (requests, tokens, duration)
    - Blueprint metrics (operations, resources)
    - Deployment metrics (operations, duration)
    - Tool execution metrics
    - Rate limiting metrics
    - System metrics (connections, cache)
  - `/metrics` endpoint (Prometheus exposition format)
  - Human-readable monitoring endpoints:
    - `/api/v1/monitoring/metrics/summary`
    - `/api/v1/monitoring/rate-limit/stats`
    - `/api/v1/monitoring/health/detailed`
  - Grafana dashboard auto-generation script
  - <0.5ms collection overhead

#### Documentation
- **Complete Documentation Suite** (~15,000 lines, 196 pages)
  - `docs/API_REFERENCE.md` - Complete API documentation (42 pages)
  - `docs/USER_GUIDE.md` - User guide with examples (35 pages)
  - `docs/PRODUCTION_DEPLOYMENT.md` - Production setup guide (38 pages)
  - `docs/RATE_LIMITING_AND_METRICS.md` - Monitoring deep dive (28 pages)
  - `docs/QUICKSTART_RATE_LIMITS.md` - Testing guide (8 pages)
  - `docs/TOOLS_API.md` - LLM tools documentation (12 pages)
  - `docs/STREAMING_AND_TEMPLATES.md` - Streaming & templates (18 pages)
  - `docs/PROJECT_STATUS.md` - Status & roadmap (8 pages)
  - Updated `README.md` with comprehensive overview
  - Updated `docs/INDEX.md` with documentation index

#### Infrastructure
- Docker Compose configuration for metrics stack
  - Prometheus configuration
  - Grafana provisioning (auto-loaded dashboard)
  - PostgreSQL, Redis, Nginx
- Production deployment templates
- Grafana dashboard generator script
- Load testing suite (`tests/load_test.py`)

### Changed

- **Database Models**: Fixed SQLAlchemy reserved name conflict
  - `metadata` column renamed to `blueprint_metadata` in `SystemBlueprintModel`
  - `metadata` column renamed to `ipr_metadata` in `InfrastructurePullRequestModel`
- **Dependencies**: Added `prometheus-client>=0.19.0`
- **README**: Completely rewritten with modern badges and structure
- **Main Application**: Integrated rate limiting and metrics middleware

### Fixed

- SQLAlchemy 2.0 compatibility issues with declarative_base
- Database column name conflicts with reserved keywords
- Import paths for monitoring routes
- **Test suite compatibility with async implementation**
  - Updated rate limiter tests to use async/await properly
  - Fixed Prometheus metrics API usage in tests
  - Created proper mock Request objects for testing
  - Fixed histogram observation tests to work with prometheus_client
- **Test execution issues**
  - Fixed 18 failing tests in test_rate_limit_metrics.py
  - All 76 runnable unit tests now passing
  - Performance tests validated (<1ms rate limiting, <0.5ms metrics)

### Performance

- API latency: <5ms middleware overhead
- Rate limiting: <1ms per request check
- Metrics collection: <0.5ms per request
- Streaming: 96% faster time-to-first-byte
- LLM generation: 2-5s typical response time

### Security

- IP-based rate limiting with configurable limits
- SQL injection protection via SQLAlchemy ORM
- Input validation via Pydantic schemas
- CORS configuration
- Future: API key auth, JWT tokens, RBAC

---

## [0.1.0] - 2025-10-01

### Initial Release

#### Core Features
- **4-Layer Architecture**
  - L4: Intent layer (CLI/API)
  - L3: Reasoning layer (LLM - Qwen2-0.5B)
  - L2: Modeling layer (YAML blueprints)
  - L1: Execution layer (Engine plugins)

- **Blueprint System**
  - YAML-based infrastructure definitions
  - CRUD operations via REST API
  - SQLAlchemy persistence
  - Pydantic validation

- **Infrastructure Pull Requests (IPR)**
  - Review workflow for infrastructure changes
  - Status tracking (pending, approved, rejected, deployed)
  - Audit trail

- **LLM Integration**
  - Qwen2-0.5B-Instruct model
  - Basic conversation endpoint
  - Blueprint generation from natural language

- **Engine System**
  - Plugin-based architecture
  - Proxmox engine implementation
  - Fake engine for testing
  - Base engine interface

- **API**
  - FastAPI-based REST API
  - OpenAPI documentation
  - Async database operations
  - CORS support

#### Documentation
- Basic README
- Architecture overview
- Blueprint documentation
- Engine documentation
- LLM guide

#### Testing
- Unit tests
- Integration tests
- E2E tests
- Test fixtures

---

## Roadmap

### [0.3.0] - Planned (Tier S - 95% Impact)

#### Multi-Agent LLM Orchestra
- Specialized AI agents:
  - Architect Agent (design optimization)
  - Security Agent (continuous scanning)
  - Cost Agent (real-time optimization)
  - Performance Agent (tuning)
  - Compliance Agent (regulatory)
- Agent coordination layer
- RAG for enhanced context

#### Predictive Infrastructure
- Anomaly detection ML
- Capacity forecasting
- Self-healing automation
- Chaos engineering

#### Universal Infrastructure Translator
- AWS ↔ Azure ↔ GCP ↔ On-Prem conversions
- Automated cost arbitrage
- Multi-cloud deployments
- Platform-agnostic blueprints

### [0.4.0] - Planned (Tier A - 75-85% Impact)

#### Visual Infrastructure Builder
- Drag-and-drop UI
- Real-time validation
- Auto-layout
- Export to YAML

#### GitOps Integration
- AI code review
- Drift detection
- Progressive delivery
- Automatic PR generation

#### Real-time Collaboration
- Multi-user editing
- Live cursors
- Conflict resolution
- Team chat integration

---

## Links

- **Repository**: https://github.com/fabriziosalmi/alma
- **Documentation**: https://github.com/fabriziosalmi/alma/tree/main/docs
- **Issues**: https://github.com/fabriziosalmi/alma/issues
- **Discussions**: https://github.com/fabriziosalmi/alma/discussions

---

## Contributors

Thanks to all contributors who have helped with this release!

- Initial development and architecture
- Quick Wins implementation (Enhanced Function Calling, Streaming, Templates, Rate Limiting, Metrics)
- Comprehensive documentation suite
- Testing and validation

---

**Semantic Versioning Guide**:
- MAJOR version: Incompatible API changes
- MINOR version: New functionality (backward compatible)
- PATCH version: Bug fixes (backward compatible)
