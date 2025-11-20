# API Authentication

## Overview

ALMA implements header-based API Key authentication for securing critical endpoints.

## Configuration

### Environment Variables

- `ALMA_AUTH_ENABLED`: Enable/disable authentication (default: `true`)
- `ALMA_API_KEYS`: Comma-separated list of valid API keys

### Example Configuration

```bash
# Enable authentication (production)
export ALMA_AUTH_ENABLED=true
export ALMA_API_KEYS="prod-key-abc123,backup-key-xyz789"

# Disable authentication (development)
export ALMA_AUTH_ENABLED=false
```

## Protected Endpoints

The following endpoints require authentication:

### Blueprints
- `POST /api/v1/blueprints/` - Create blueprint
- `POST /api/v1/blueprints/{id}/deploy` - Deploy blueprint

### Infrastructure Pull Requests (IPR)
- `POST /api/v1/ipr/` - Create IPR

### Tools
- `POST /api/v1/tools/execute` - Execute tool
- `POST /api/v1/tools/execute-direct` - Execute tool directly

## Public Endpoints

The following endpoints remain public (no authentication required):

- `GET /api/v1/monitoring/health` - Health check
- `GET /api/v1/monitoring/health/detailed` - Detailed health check
- `GET /api/v1/monitoring/metrics` - Prometheus metrics
- `GET /api/v1/monitoring/metrics/summary` - Metrics summary

## Usage Examples

### cURL with API Key

```bash
# Create a blueprint
curl -X POST http://localhost:8000/api/v1/blueprints/ \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"version": "1.0", "name": "my-infrastructure", "resources": []}'
```

### Python with httpx

```python
import httpx

headers = {"X-API-Key": "your-api-key-here"}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/blueprints/",
        json={"version": "1.0", "name": "my-infrastructure", "resources": []},
        headers=headers
    )
    print(response.json())
```

### JavaScript/TypeScript

```typescript
const headers = {
  'X-API-Key': 'your-api-key-here',
  'Content-Type': 'application/json'
};

const response = await fetch('http://localhost:8000/api/v1/blueprints/', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    version: '1.0',
    name: 'my-infrastructure',
    resources: []
  })
});

const data = await response.json();
```

## Testing

### Running Authentication Tests

Authentication tests must be run in isolation to avoid conflicts with other tests that have authentication disabled:

```bash
# Run only authentication tests
pytest tests/unit/test_auth.py -v

# Run all other tests (excluding auth)
pytest tests/ -k "not e2e and not test_auth" -v
```

### Test Environment

Tests disable authentication by default via `tests/conftest.py`. The `test_auth.py` module explicitly enables authentication using a module-scoped fixture.

## Security Best Practices

1. **Never commit API keys to version control**
2. **Rotate keys regularly** in production environments
3. **Use different keys** for different environments (dev, staging, prod)
4. **Monitor authentication failures** via metrics
5. **Enable authentication** in all production deployments

## Troubleshooting

### 403 Forbidden Error

If you receive a 403 error:

1. Check that `X-API-Key` header is present
2. Verify the API key is in `ALMA_API_KEYS` environment variable
3. Confirm `ALMA_AUTH_ENABLED=true`

### Authentication Disabled in Tests

Authentication is automatically disabled for tests (except `test_auth.py`). This is controlled by:

```python
# tests/conftest.py
os.environ.setdefault("ALMA_AUTH_ENABLED", "false")
```

## Implementation Details

- **Middleware**: `alma/middleware/auth.py`
- **Header Name**: `X-API-Key`
- **Validation**: Simple string matching against configured keys
- **Response**: HTTP 403 Forbidden for invalid/missing keys

## Future Enhancements

Potential improvements for future versions:

- [ ] JWT token support
- [ ] OAuth 2.0 integration
- [ ] API key rotation mechanism
- [ ] Per-endpoint permission scopes
- [ ] Rate limiting per API key
- [ ] Audit logging for authentication events
