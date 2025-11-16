# Infrastructure Engines

Engines are pluggable modules that interface with infrastructure providers to deploy and manage resources.

## Overview

AI-CDN uses a **plugin architecture** for infrastructure providers. Each engine implements a common interface, allowing the core system to work with any provider.

## Available Engines

| Engine | Provider | Status | Resources Supported |
|--------|----------|--------|---------------------|
| **FakeEngine** | Testing | ✅ Complete | All types (simulated) |
| **ProxmoxEngine** | Proxmox VE | 🚧 In Progress | compute, storage |
| DockerEngine | Docker | 📅 Planned | compute, network |
| AnsibleEngine | Ansible | 📅 Planned | compute, configure |
| MikroTikEngine | MikroTik | 📅 Planned | network |
| KubernetesEngine | K8s | 📅 Planned | All types |

## Engine Interface

All engines must implement the `Engine` abstract base class:

```python
from ai_cdn.engines.base import Engine, DeploymentResult, ResourceState

class MyEngine(Engine):
    async def validate_blueprint(self, blueprint: Dict[str, Any]) -> bool:
        """Validate blueprint for this provider."""
        pass

    async def deploy(self, blueprint: Dict[str, Any]) -> DeploymentResult:
        """Deploy infrastructure."""
        pass

    async def get_state(self, resource_id: str) -> ResourceState:
        """Get current resource state."""
        pass

    async def destroy(self, resource_id: str) -> bool:
        """Destroy a resource."""
        pass

    async def rollback(self, deployment_id: str, target_state: Optional[str] = None) -> bool:
        """Rollback deployment."""
        pass

    async def health_check(self) -> bool:
        """Check engine health."""
        pass

    def get_supported_resource_types(self) -> List[str]:
        """Return supported resource types."""
        return ["compute", "network", "storage"]
```

## FakeEngine

**Purpose**: Testing and development

**Location**: `ai_cdn/engines/fake.py`

**Features**:
- Simulates all infrastructure operations
- Instant deployment (no actual resources)
- Configurable failure modes
- Perfect for testing

**Configuration**:
```python
engine = FakeEngine(config={
    "fail_on_deploy": False,  # Simulate failures
})
```

**Example**:
```python
from ai_cdn.engines.fake import FakeEngine

engine = FakeEngine()

blueprint = {
    "version": "1.0",
    "name": "test",
    "resources": [...]
}

# Deploy (simulated)
result = await engine.deploy(blueprint)
print(f"Status: {result.status}")
print(f"Resources: {result.resources_created}")
```

## ProxmoxEngine

**Purpose**: Proxmox Virtual Environment integration

**Location**: `ai_cdn/engines/proxmox.py`

**Status**: 🚧 In Development

**Supported Resources**:
- ✅ `compute`: Virtual machines
- 🚧 `storage`: Storage volumes
- 📅 `network`: Networks and VLANs

**Configuration**:
```python
engine = ProxmoxEngine(config={
    "host": "https://proxmox.example.com:8006",
    "username": "root@pam",
    "password": "your-password",
    "node": "pve",
    "verify_ssl": True,
})
```

**Example Blueprint**:
```yaml
version: "1.0"
name: proxmox-vm
resources:
  - type: compute
    name: web-server-01
    provider: proxmox
    specs:
      cpu: 4
      memory: 8GB
      storage: 100GB
      os: ubuntu-22.04
    metadata:
      node: pve
      pool: production
```

**API Documentation**:
- [Proxmox API Docs](https://pve.proxmox.com/pve-docs/api-viewer/)

## Creating Custom Engines

### 1. Create Engine Class

```python
# ai_cdn/engines/myengine.py
from ai_cdn.engines.base import Engine, DeploymentResult, DeploymentStatus

class MyEngine(Engine):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_url = config.get("api_url")
        self.api_key = config.get("api_key")

    async def validate_blueprint(self, blueprint: Dict[str, Any]) -> bool:
        # Validate blueprint structure
        if "resources" not in blueprint:
            raise ValueError("Missing resources")
        return True

    async def deploy(self, blueprint: Dict[str, Any]) -> DeploymentResult:
        # Deploy infrastructure
        resources_created = []

        for resource in blueprint["resources"]:
            # Create resource via provider API
            resource_id = await self._create_resource(resource)
            resources_created.append(resource["name"])

        return DeploymentResult(
            status=DeploymentStatus.COMPLETED,
            message=f"Deployed {len(resources_created)} resources",
            resources_created=resources_created,
        )
```

### 2. Register Engine

Add to `ai_cdn/engines/__init__.py`:

```python
from ai_cdn.engines.myengine import MyEngine

__all__ = ["Engine", "FakeEngine", "ProxmoxEngine", "MyEngine"]
```

### 3. Add Tests

```python
# tests/unit/test_myengine.py
import pytest
from ai_cdn.engines.myengine import MyEngine

@pytest.fixture
def engine():
    return MyEngine(config={"api_url": "https://api.example.com"})

async def test_deploy(engine):
    blueprint = {...}
    result = await engine.deploy(blueprint)
    assert result.status == DeploymentStatus.COMPLETED
```

### 4. Document Provider

Add provider documentation with:
- Supported resource types
- Configuration options
- Example blueprints
- API requirements

## Best Practices

### Error Handling

```python
async def deploy(self, blueprint):
    try:
        # Deployment logic
        pass
    except ProviderAPIError as e:
        return DeploymentResult(
            status=DeploymentStatus.FAILED,
            message=f"API error: {e}",
            resources_failed=[...],
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### Idempotency

```python
async def deploy(self, blueprint):
    for resource in blueprint["resources"]:
        existing = await self._check_exists(resource["name"])

        if existing:
            # Update existing resource
            await self._update_resource(existing.id, resource)
        else:
            # Create new resource
            await self._create_resource(resource)
```

### State Management

```python
async def get_state(self, resource_id):
    # Query provider API
    provider_state = await self.api.get_resource(resource_id)

    # Map to standard state
    return ResourceState(
        resource_id=resource_id,
        resource_type=provider_state.type,
        status=self._map_status(provider_state.status),
        properties=provider_state.config,
    )
```

### Resource Cleanup

```python
async def rollback(self, deployment_id):
    # Get resources for deployment
    resources = await self._get_deployment_resources(deployment_id)

    # Destroy in reverse order (handle dependencies)
    for resource in reversed(resources):
        try:
            await self.destroy(resource.id)
        except Exception as e:
            logger.error(f"Failed to destroy {resource.id}: {e}")

    return True
```

## Testing Engines

### Unit Tests

```python
@pytest.mark.asyncio
async def test_validate_blueprint():
    engine = MyEngine()

    valid_blueprint = {...}
    assert await engine.validate_blueprint(valid_blueprint)

    invalid_blueprint = {}
    with pytest.raises(ValueError):
        await engine.validate_blueprint(invalid_blueprint)
```

### Integration Tests

```python
@pytest.mark.integration
async def test_full_deployment():
    # Requires actual provider access
    engine = MyEngine(config=test_config)

    blueprint = load_test_blueprint()
    result = await engine.deploy(blueprint)

    assert result.status == DeploymentStatus.COMPLETED

    # Cleanup
    for resource in result.resources_created:
        await engine.destroy(resource)
```

### Mock Tests

```python
@patch("ai_cdn.engines.myengine.ProviderAPI")
async def test_deploy_mocked(mock_api):
    mock_api.create_vm.return_value = {"id": "vm-123"}

    engine = MyEngine()
    result = await engine.deploy(blueprint)

    assert "vm-123" in result.resources_created
    mock_api.create_vm.assert_called_once()
```

## Engine Configuration

Engines can be configured via:

### 1. Environment Variables

```bash
# .env
PROXMOX_HOST=https://proxmox.example.com:8006
PROXMOX_USERNAME=root@pam
PROXMOX_PASSWORD=secret
```

### 2. Config Files

```yaml
# config/engines.yaml
engines:
  proxmox:
    host: https://proxmox.example.com:8006
    username: root@pam
    node: pve
```

### 3. Blueprint Metadata

```yaml
version: "1.0"
name: my-infra
metadata:
  engine_config:
    proxmox:
      node: pve-node-02
resources: [...]
```

## Provider-Specific Guides

- [Proxmox Setup](engines/PROXMOX.md)
- [Docker Setup](engines/DOCKER.md)
- [Ansible Setup](engines/ANSIBLE.md)

---

**Next**: [API Reference](API.md)
