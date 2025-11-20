# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

The ALMA team takes security vulnerabilities seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security vulnerabilities by emailing:

**security@alma.dev**

Or use GitHub Security Advisories:
https://github.com/fabriziosalmi/alma/security/advisories/new

### What to Include

Please include the following information in your report:

1. **Description**: Clear description of the vulnerability
2. **Impact**: Potential impact and attack scenario
3. **Reproduction Steps**: Detailed steps to reproduce the issue
4. **Affected Versions**: Which versions are affected
5. **Proof of Concept**: Code or configuration demonstrating the issue (if applicable)
6. **Suggested Fix**: If you have recommendations for addressing the vulnerability

### Example Report

```
Subject: SQL Injection in Blueprint API

Description:
The blueprint name parameter in POST /api/v1/blueprints is vulnerable 
to SQL injection attacks.

Impact:
An attacker could execute arbitrary SQL queries, potentially leading to 
data exfiltration or database corruption.

Reproduction:
1. Send POST request to /api/v1/blueprints
2. Set name parameter to: "test'; DROP TABLE blueprints; --"
3. Observe SQL error in logs

Affected Versions: 0.1.0

Proof of Concept:
[Attach curl command or Python script]

Suggested Fix:
Ensure all database queries use parameterized statements via SQLAlchemy ORM.
```

## Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: 
  - Critical vulnerabilities: 7-14 days
  - High severity: 30 days
  - Medium severity: 60 days
  - Low severity: 90 days

## Disclosure Policy

- We follow **coordinated disclosure** principles
- We will work with you to understand and resolve the issue
- We request that you do not publicly disclose the issue until we've had a chance to address it
- We will credit you in our security advisory unless you prefer to remain anonymous

## Security Features

ALMA implements several security measures:

### Rate Limiting

**Purpose**: Prevent abuse and DoS attacks

- **Global Rate Limit**: 60 requests/minute per IP
- **Endpoint-Specific Limits**:
  - `/conversation/chat-stream`: 20 RPM (LLM operations are expensive)
  - `/blueprints/generate-blueprint`: 30 RPM
  - `/tools/execute`: 40 RPM
  - `/blueprints` (CRUD): 100 RPM

**Headers Returned**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700140800
```

**Implementation**: Token bucket algorithm with per-IP tracking

**Configuration**:
```python
# In alma/middleware/rate_limit.py
DEFAULT_RATE_LIMIT = 60  # requests per minute
DEFAULT_BURST = 10       # burst capacity
```

### Input Validation

**Purpose**: Prevent injection attacks and malformed data

- **Pydantic Models**: All API inputs validated with strict type checking
- **Schema Validation**: Blueprint YAML validated against defined schemas
- **Sanitization**: User inputs sanitized before processing

**Example**:
```python
class BlueprintCreate(BaseModel):
    version: str = Field(..., pattern=r"^\d+\.\d+$")
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
```

### SQL Injection Protection

**Purpose**: Prevent database attacks

- **ORM Usage**: All database operations use SQLAlchemy ORM
- **Parameterized Queries**: No raw SQL with string concatenation
- **Prepared Statements**: Database driver uses prepared statements

### Authentication & Authorization

**Current Status**: IP-based rate limiting only

**Planned Features** (Future Releases):
- API Key Authentication
- OAuth2 / JWT Tokens
- Role-Based Access Control (RBAC)
- Multi-Factor Authentication (MFA)

### Infrastructure Security

**Best Practices**:

1. **Environment Variables**: Sensitive data stored in `.env` files
2. **Secrets Management**: Use secret managers in production (AWS Secrets Manager, Vault)
3. **HTTPS Only**: Force HTTPS in production deployments
4. **CORS Configuration**: Restrict allowed origins
5. **Dependency Scanning**: Regular updates for security patches

**Production Deployment**:
```bash
# Use reverse proxy with TLS
nginx -> ALMA API (internal only)

# Environment isolation
export ALMA_ENV=production
export ALMA_LOG_LEVEL=WARNING
export ALMA_DEBUG=false
```

## Security Checklist for Deployments

- [ ] Use HTTPS/TLS certificates
- [ ] Configure firewall rules (allow only necessary ports)
- [ ] Set up rate limiting at load balancer level
- [ ] Enable database encryption at rest
- [ ] Use secure password policies for database
- [ ] Implement log monitoring and alerting
- [ ] Regular security updates and patches
- [ ] Backup database with encryption
- [ ] Use secrets management for API keys
- [ ] Configure CORS appropriately
- [ ] Disable debug mode in production
- [ ] Implement request logging without sensitive data
- [ ] Set up intrusion detection system (IDS)

## Security Updates

Security updates will be announced via:

1. **GitHub Security Advisories**: https://github.com/fabriziosalmi/alma/security/advisories
2. **Release Notes**: Included in CHANGELOG.md
3. **Email**: For registered users (future feature)

## Known Limitations

Current version has the following security limitations:

1. **No Authentication**: API is publicly accessible
2. **IP-Based Rate Limiting**: Can be bypassed with distributed attacks
3. **No Request Signing**: Requests not cryptographically signed
4. **Limited Audit Logging**: Basic logging only

These will be addressed in future releases.

## Security Contacts

- **Primary**: security@alma.dev
- **GitHub**: [@fabriziosalmi](https://github.com/fabriziosalmi)
- **Project Lead**: Fabrizio Salmi

## Bug Bounty Program

We are planning to launch a bug bounty program in Q2 2026. Stay tuned for details.

---

**Last Updated**: November 2025  
**Security Policy Version**: 1.0
