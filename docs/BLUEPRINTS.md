# Blueprint Guide

Complete guide to creating and managing infrastructure blueprints.

## What is a Blueprint?

A **Blueprint** is a declarative YAML file that describes your infrastructure.
It specifies WHAT you want, not HOW to create it.

## Blueprint Structure

```yaml
version: "1.0"              # Blueprint version
name: my-infrastructure     # Unique name
description: "Optional description"

resources:                  # List of resources
  - type: compute          # Resource type
    name: web-server       # Resource name
    provider: proxmox      # Infrastructure provider
    specs:                 # Provider-specific specs
      cpu: 4
      memory: 8GB
      storage: 100GB
    dependencies: []       # Resource dependencies
    metadata: {}           # Additional metadata

metadata:                  # Blueprint-level metadata
  environment: production
  owner: platform-team
```

## Resource Types

### Compute
Virtual machines, containers, bare metal servers.

```yaml
- type: compute
  name: app-server
  provider: proxmox
  specs:
    cpu: 4
    memory: 8GB
    storage: 50GB
    os: ubuntu-22.04
```

### Network
Load balancers, VPNs, firewalls, networks.

```yaml
- type: network
  name: load-balancer
  provider: fake
  specs:
    type: http
    algorithm: round-robin
    backends: [web-1, web-2]
```

### Storage
Volumes, object storage, backups.

```yaml
- type: storage
  name: data-volume
  provider: proxmox
  specs:
    size: 500GB
    type: ssd
    encryption: true
```

### Service
Databases, message queues, caches.

```yaml
- type: service
  name: postgres
  provider: docker
  specs:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
```

## Dependencies

Resources can depend on other resources:

```yaml
resources:
  - type: compute
    name: database
    # No dependencies

  - type: compute
    name: app-server
    dependencies:
      - database  # Waits for database

  - type: network
    name: load-balancer
    dependencies:
      - app-server  # Waits for app server
```

## Examples

See `examples/blueprints/` for complete examples:
- `simple-web-app.yaml` - Basic web application
- `microservices-cluster.yaml` - Complex microservices

## Validation

Blueprints are validated before deployment:
- Schema validation (Pydantic)
- Dependency graph validation
- Provider compatibility checks

## Best Practices

1. **Use descriptive names**: `web-server-prod-01` not `server1`
2. **Document with metadata**: Add environment, owner, purpose
3. **Version control**: Store blueprints in git
4. **Test with dry-run**: Use `--dry-run` flag
5. **Start small**: Build incrementally

---

**Next**: [Deployment Guide](DEPLOYMENT.md)
