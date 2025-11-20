# Contributing to ALMA

Thank you for your interest in contributing to ALMA! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Maintain a professional environment

## Getting Started

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/alma.git
   cd alma
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Development Workflow

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests:
   ```bash
   pytest
   ```

4. Run code quality checks:
   ```bash
   black .
   ruff check .
   mypy alma
   bandit -r alma
   ```

5. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a Pull Request

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add Proxmox engine plugin
fix: resolve blueprint validation error
docs: update API documentation
test: add tests for FakeEngine rollback
```

## Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting (line length: 100)
- **Ruff**: Fast Python linter
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability scanning

All of these run automatically via pre-commit hooks.

### Type Hints

Always use type hints:

```python
def deploy(self, blueprint: Dict[str, Any]) -> DeploymentResult:
    """Deploy resources according to the blueprint."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def validate_blueprint(self, blueprint: Dict[str, Any]) -> bool:
    """
    Validate a blueprint before deployment.

    Args:
        blueprint: The system blueprint to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If blueprint is invalid
    """
    pass
```

## Testing

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Place e2e tests in `tests/e2e/`
- Aim for >80% code coverage
- Use descriptive test names
- Follow the AAA pattern (Arrange, Act, Assert)

Example:

```python
async def test_deploy_success(self, engine: FakeEngine, sample_blueprint: dict) -> None:
    """Test successful deployment."""
    # Arrange
    # (setup done in fixtures)

    # Act
    result = await engine.deploy(sample_blueprint)

    # Assert
    assert result.status == DeploymentStatus.COMPLETED
    assert len(result.resources_created) == 1
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=alma --cov-report=html

# Run specific test
pytest tests/unit/test_fake_engine.py::TestFakeEngine::test_deploy_success

# Run tests in parallel
pytest -n auto
```

## Adding New Engines

To add support for a new infrastructure provider:

1. Create a new file in `alma/engines/`:
   ```python
   from alma.engines.base import Engine, DeploymentResult

   class MyEngine(Engine):
       async def deploy(self, blueprint: Dict[str, Any]) -> DeploymentResult:
           # Implementation
           pass
   ```

2. Implement all required methods from the `Engine` base class

3. Add tests in `tests/unit/test_my_engine.py`

4. Update documentation

5. Add configuration options to `alma/core/config.py`

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update documentation
3. Add tests for new functionality
4. Ensure all tests pass
5. Ensure code quality checks pass
6. Update CHANGELOG.md (if we have one)
7. Request review from maintainers

### PR Template

When creating a PR, please include:

- Description of changes
- Related issue (if applicable)
- Testing performed
- Screenshots (if UI changes)
- Breaking changes (if any)

## Project Structure

```
alma/
├── api/          # FastAPI endpoints
├── core/         # Core business logic
├── engines/      # Infrastructure engine plugins
├── models/       # SQLAlchemy database models
├── schemas/      # Pydantic schemas
├── cli/          # CLI interface
└── utils/        # Utility functions

tests/
├── unit/         # Unit tests
├── integration/  # Integration tests
└── e2e/          # End-to-end tests
```

## Documentation

- Update docstrings for all public APIs
- Add usage examples
- Update README.md if needed
- Add entries to docs/ for major features

## Questions?

- Open an issue for discussion
- Join our Discord (coming soon)
- Check existing issues and PRs

Thank you for contributing to ALMA!
