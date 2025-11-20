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

### Black - Code Formatting

**Configuration** (automatic via `pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.venv
  | build
  | dist
)/
'''
```

**Usage**:
```bash
# Format all files
black .

# Check without modifying
black --check .

# Format specific file
black alma/core/llm.py
```

### Ruff - Fast Python Linter

**Configuration** (`pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # unused imports
"tests/**/*.py" = ["S101"]  # assert usage
```

**Usage**:
```bash
# Lint all files
ruff check .

# Auto-fix issues
ruff check --fix .

# Lint specific file
ruff check alma/api/routes.py
```

### MyPy - Static Type Checking

**Configuration** (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "kubernetes_asyncio.*",
    "prometheus_client.*",
]
ignore_missing_imports = true
```

**Usage**:
```bash
# Type check entire project
mypy alma

# Check specific module
mypy alma/core

# Show error codes
mypy --show-error-codes alma
```

### Pytest - Testing Standards

**Configuration** (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov=alma",
    "--cov-report=term-missing",
    "--cov-report=html",
]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]
```

**Writing Tests**:
```python
import pytest
from alma.core.blueprint import Blueprint

class TestBlueprint:
    """Test suite for Blueprint class."""
    
    def test_create_blueprint(self):
        """Test blueprint creation with valid data."""
        blueprint = Blueprint(
            version="1.0",
            name="test-blueprint",
            description="Test description"
        )
        assert blueprint.name == "test-blueprint"
    
    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test asynchronous blueprint operation."""
        result = await some_async_function()
        assert result is not None
```

### Code Quality Checklist

Before submitting a PR, ensure:

- [ ] Code formatted with Black (`black .`)
- [ ] No linting errors (`ruff check .`)
- [ ] Type hints added (`mypy alma`)
- [ ] Tests written and passing (`pytest`)
- [ ] Test coverage > 75% (`pytest --cov`)
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] No security issues (`bandit -r alma`)
- [ ] No sensitive data in code
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
