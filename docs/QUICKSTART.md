# Quick Start Guide

This guide will help you get started with ALMA in 5 minutes.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd alma

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Initialize Database

```bash
# The database will be automatically initialized when you first run the API
# For SQLite (default), no additional setup is needed
```

## Start the API Server

```bash
# Start the development server
ALMA serve --reload

# Or using uvicorn directly
uvicorn alma.api.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

## Deploy Your First Blueprint

### Using the CLI

```bash
# Create a new project
ALMA init my-infrastructure

# Deploy the example blueprint
cd my-infrastructure
ALMA deploy blueprints/example.yaml

# Dry-run (validation only)
ALMA deploy blueprints/example.yaml --dry-run
```

### Using the API

```bash
# Create a blueprint
curl -X POST "http://localhost:8000/api/v1/blueprints/" \
  -H "Content-Type: application/json" \
  -d @examples/blueprints/simple-web-app.yaml

# Deploy the blueprint
curl -X POST "http://localhost:8000/api/v1/blueprints/1/deploy" \
  -H "Content-Type: application/json" \
  -d '{"blueprint_id": 1, "dry_run": false}'
```

## Example Blueprint

Create a file `my-blueprint.yaml`:

```yaml
version: "1.0"
name: "my-first-infrastructure"
description: "My first ALMA blueprint"

resources:
  - type: compute
    name: web-server
    provider: fake
    specs:
      cpu: 2
      memory: 4GB
      storage: 50GB

  - type: network
    name: load-balancer
    provider: fake
    specs:
      type: http
      backends:
        - web-server
    dependencies:
      - web-server
```

Deploy it:

```bash
ALMA deploy my-blueprint.yaml
```

## Check Infrastructure Status

```bash
# Using CLI
ALMA status

# Using API
curl http://localhost:8000/api/v1/blueprints/
```

## Run Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/test_fake_engine.py

# Run with verbose output
pytest -v
```

## Next Steps

- Read the [Architecture Guide](ARCHITECTURE.md)
- Learn about [Engines](ENGINES.md)
- Explore [Advanced Features](ADVANCED.md)
- Check out [Example Blueprints](../examples/blueprints/)

## Troubleshooting

### Database Issues

If you encounter database issues, try:

```bash
# Remove the database file
rm alma.db

# Restart the API server
ALMA serve --reload
```

### Import Errors

Make sure you've installed the package in editable mode:

```bash
pip install -e ".[dev]"
```

### Pre-commit Hook Failures

If pre-commit hooks fail, you can run them manually:

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
black .
ruff check .
mypy alma
```

## Getting Help

- Check the [documentation](../README.md)
- Open an issue on GitHub
- Join our community Discord (coming soon)
