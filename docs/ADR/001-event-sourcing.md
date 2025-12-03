# ADR-001: Event Sourcing for Infrastructure Changes

**Status**: Accepted  
**Date**: 2025-12-03  
**Deciders**: ALMA Core Team  
**Context**: Code review feedback questioned if Event Sourcing is over-engineered for an "API wrapper"

---

## Context and Problem Statement

ALMA implements Event Sourcing to track all infrastructure changes as immutable events. The code review feedback suggested this might be over-engineered for what is essentially an API wrapper around infrastructure tools (Terraform, Ansible, Docker, etc.).

**Question**: Do we really need Event Sourcing, or is it academic fluff?

---

## Decision Drivers

1. **Audit Trail Requirements**: Infrastructure changes need complete audit history for compliance
2. **Debugging**: Need to replay state to understand how infrastructure got into current state
3. **Compliance**: Many industries (finance, healthcare) require immutable audit logs
4. **Blame Assignment**: When infrastructure breaks, need to know who changed what and when
5. **Rollback Capability**: Need to reconstruct previous states for rollback

---

## Considered Options

### Option 1: Remove Event Sourcing (Simple CRUD)
**Pros**:
- Simpler code
- Faster development
- Less storage overhead

**Cons**:
- No audit trail
- Can't replay state
- Compliance issues
- Hard to debug "how did we get here?"

### Option 2: Keep Event Sourcing (Current)
**Pros**:
- Complete audit trail
- Can replay any state
- Compliance-ready
- Debugging is easier

**Cons**:
- More complex code
- Storage overhead
- Requires event versioning

### Option 3: Hybrid (Events for critical operations only)
**Pros**:
- Balance complexity and auditability
- Less storage overhead

**Cons**:
- Inconsistent audit trail
- Hard to decide what's "critical"

---

## Decision Outcome

**Chosen option**: **Option 2 - Keep Event Sourcing**

### Rationale

Infrastructure is **NOT** just an API wrapper. It's **stateful, critical, and regulated**:

1. **Compliance**: Many users operate in regulated industries (finance, healthcare, government)
   - GDPR requires audit trails
   - SOC2 requires change tracking
   - HIPAA requires access logs

2. **Infrastructure is Stateful**: Unlike typical APIs, infrastructure changes have long-term consequences
   - A deleted database can't be recovered without audit trail
   - Need to know "who deleted production DB at 3am?"

3. **Debugging Production Issues**:
   - "Why is the load balancer routing to the wrong servers?"
   - Answer: Replay events to see configuration drift

4. **Rollback Requirements**:
   - Infrastructure changes often need rollback
   - Event Sourcing makes rollback deterministic

5. **Multi-Step Operations**:
   - Infrastructure changes are rarely atomic
   - Need to track partial completions

---

## Implementation Details

### What We Store as Events

```python
class InfrastructureEvent(BaseModel):
    event_id: UUID
    aggregate_id: UUID  # Resource ID
    event_type: str     # "ResourceCreated", "ResourceUpdated", etc.
    timestamp: datetime
    user_id: str
    payload: dict       # The actual change
    metadata: dict      # Context (IP, session, etc.)
```

### Example Event Stream

```
1. ResourceCreated(type="database", size="large")
2. ResourceScaled(size="xlarge")
3. ResourceDeleted()
```

From this stream, we can:
- Reconstruct current state
- Audit who made changes
- Rollback to any point
- Generate compliance reports

---

## Consequences

### Positive
- ✅ Complete audit trail for compliance
- ✅ Can replay state for debugging
- ✅ Rollback is deterministic
- ✅ Blame assignment is clear
- ✅ Production-ready for regulated industries

### Negative
- ❌ More complex than simple CRUD
- ❌ Storage overhead (mitigated by event compaction)
- ❌ Requires event versioning strategy

### Mitigation Strategies
- Event compaction after 90 days
- Event versioning with schema migration
- Read models (CQRS) for fast queries

---

## Validation

Event Sourcing is **NOT** over-engineering for infrastructure because:

1. **Terraform** has state files (similar concept)
2. **Kubernetes** has etcd (event log)
3. **AWS CloudTrail** is event sourcing for AWS
4. **Git** is event sourcing for code

If AWS, Kubernetes, and Git use event sourcing, it's a proven pattern for infrastructure.

---

## References

- [Martin Fowler - Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- [AWS CloudTrail](https://aws.amazon.com/cloudtrail/)
- [Kubernetes Event-Driven Architecture](https://kubernetes.io/docs/reference/using-api/api-concepts/)
- [GDPR Audit Trail Requirements](https://gdpr.eu/article-30-record-of-processing-activities/)

---

## Related ADRs

- [ADR-002: Saga Pattern](./002-saga-pattern.md)
