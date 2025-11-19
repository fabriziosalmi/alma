# Infrastructure Pull Requests (IPR)

Human-in-the-loop approval system for infrastructure changes.

## Overview

**IPR** (Infrastructure Pull Request) is like GitHub Pull Requests, but for infrastructure. It provides:

- **Review workflow**: Changes must be reviewed before deployment
- **Audit trail**: Complete history of who approved what
- **Safety**: Prevent accidental deployments
- **Collaboration**: Team members can review and comment

## Workflow

```
1. CREATE IPR
   Developer creates IPR from blueprint
   ↓
2. REVIEW
   Team reviews proposed changes
   → Approve or Reject
   ↓
3. DEPLOY
   If approved, deploy infrastructure
   ↓
4. TRACK
   Monitor deployment status
```

## Creating an IPR

### Via CLI
```bash
# Create IPR from blueprint
ALMA ipr create my-blueprint.yaml \
  --title "Add production database" \
  --description "PostgreSQL cluster for user data"
```

### Via API
```bash
curl -X POST http://localhost:8000/api/v1/ipr/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add production database",
    "description": "PostgreSQL cluster",
    "blueprint_id": 1,
    "created_by": "john@example.com"
  }'
```

## Reviewing an IPR

### Via CLI
```bash
# Approve
ALMA ipr review 42 --approve \
  --comment "LGTM, approved"

# Reject
ALMA ipr review 42 --reject \
  --comment "Needs more CPU"
```

### Via API
```bash
curl -X POST http://localhost:8000/api/v1/ipr/42/review \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "reviewed_by": "jane@example.com",
    "review_comments": "LGTM"
  }'
```

## Deploying an IPR

Only approved IPRs can be deployed:

```bash
# Deploy approved IPR
ALMA ipr deploy 42
```

## IPR States

- **PENDING**: Awaiting review
- **APPROVED**: Ready to deploy
- **REJECTED**: Changes requested
- **DEPLOYED**: Successfully deployed
- **FAILED**: Deployment failed
- **CANCELLED**: IPR cancelled

## Best Practices

1. **Clear titles**: Describe what changes
2. **Detailed descriptions**: Explain why
3. **Small changes**: One logical change per IPR
4. **Review promptly**: Don't block the team
5. **Test first**: Use dry-run before IPR

## Configuration

```bash
# .env
IPR_ENABLED=true
IPR_AUTO_APPROVE=false  # Require manual approval
IPR_REQUIRE_REVIEW=true
```

---

**Next**: [Deployment Guide](DEPLOYMENT.md)
