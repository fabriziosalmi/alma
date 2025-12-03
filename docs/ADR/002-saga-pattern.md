# ADR-002: Saga Pattern for Multi-Step Infrastructure Operations

**Status**: Accepted  
**Date**: 2025-12-03  
**Deciders**: ALMA Core Team  
**Context**: Code review feedback questioned if Saga Pattern is over-engineered for infrastructure orchestration

---

## Context and Problem Statement

ALMA implements the Saga Pattern to coordinate multi-step infrastructure operations with automatic rollback on failure. The code review feedback suggested this might be over-engineered.

**Question**: Do we really need Sagas, or is simple error handling enough?

---

## Decision Drivers

1. **Multi-Step Operations**: Infrastructure changes often span multiple systems
2. **Partial Failures**: Network issues, quota limits, permission errors
3. **Rollback Requirements**: Need to undo partial changes
4. **Distributed Systems**: Changes across Docker, Kubernetes, Terraform, etc.
5. **User Experience**: Don't leave infrastructure in inconsistent state

---

## Considered Options

### Option 1: Remove Saga Pattern (Simple Try/Catch)
**Pros**:
- Simpler code
- Easier to understand
- Less abstraction

**Cons**:
- Manual rollback logic everywhere
- Easy to forget cleanup
- Inconsistent error handling
- Hard to test rollback scenarios

### Option 2: Keep Saga Pattern (Current)
**Pros**:
- Automatic rollback
- Consistent error handling
- Testable rollback logic
- Clear compensation logic

**Cons**:
- More abstraction
- Learning curve
- Overhead for simple operations

### Option 3: Hybrid (Sagas for complex operations only)
**Pros**:
- Balance complexity
- Simple operations stay simple

**Cons**:
- Inconsistent patterns
- Hard to decide what's "complex"

---

## Decision Outcome

**Chosen option**: **Option 2 - Keep Saga Pattern**

### Rationale

Infrastructure orchestration **requires** coordinated multi-step operations:

1. **Real-World Example**: Deploy a web application
   ```
   Step 1: Create database (Terraform)
   Step 2: Create app servers (Docker)
   Step 3: Configure load balancer (Ansible)
   Step 4: Update DNS (API call)
   ```

   **What if Step 3 fails?**
   - Without Saga: Database and servers are orphaned (cost money, security risk)
   - With Saga: Automatic rollback deletes servers and database

2. **Distributed Transactions**:
   - Infrastructure spans multiple systems (AWS, Docker, Kubernetes)
   - No native 2PC (two-phase commit)
   - Saga provides eventual consistency

3. **User Experience**:
   - Users expect "all or nothing"
   - Partial deployments are confusing
   - Saga guarantees clean state

4. **Cost Control**:
   - Orphaned resources cost money
   - Saga ensures cleanup on failure

---

## Implementation Details

### Saga State Machine

```python
class SagaState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPENSATING = "compensating"  # Rolling back
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"    # Rolled back
```

### Example Saga

```python
saga = Saga(name="deploy_web_app")

# Forward steps
saga.add_step(
    action=create_database,
    compensation=delete_database  # Rollback
)
saga.add_step(
    action=create_servers,
    compensation=delete_servers
)
saga.add_step(
    action=configure_lb,
    compensation=remove_lb_config
)

# Execute
await saga.execute()
# If any step fails, compensations run in reverse order
```

### Rollback Guarantees

- **Automatic**: No manual cleanup code
- **Ordered**: Compensations run in reverse
- **Idempotent**: Can retry safely
- **Audited**: All steps logged via Event Sourcing

---

## Consequences

### Positive
- ✅ Automatic rollback on failure
- ✅ Consistent error handling
- ✅ No orphaned resources
- ✅ Testable rollback logic
- ✅ Clear compensation semantics

### Negative
- ❌ More abstraction than simple try/catch
- ❌ Learning curve for developers
- ❌ Overhead for trivial operations

### Mitigation Strategies
- Document Saga pattern clearly
- Provide simple examples
- Allow opt-out for single-step operations
- Use Saga only for multi-step operations

---

## Validation

Saga Pattern is **NOT** over-engineering because:

1. **Kubernetes Operators** use reconciliation loops (similar to Sagas)
2. **Terraform** has `destroy` for rollback (manual Saga)
3. **AWS CloudFormation** has rollback on stack failure (Saga)
4. **Microservices** use Sagas for distributed transactions

If AWS, Kubernetes, and Terraform need rollback, ALMA needs it too.

---

## Real-World Scenario

**Without Saga**:
```python
# Deploy fails at step 3
db = create_database()      # ✅ Created
servers = create_servers()  # ✅ Created
lb = configure_lb()         # ❌ FAILED

# Now what?
# - Database is running (costs $500/month)
# - Servers are running (costs $200/month)
# - User has to manually clean up
# - Security risk (exposed database)
```

**With Saga**:
```python
saga = Saga()
saga.add_step(create_database, delete_database)
saga.add_step(create_servers, delete_servers)
saga.add_step(configure_lb, remove_lb_config)

await saga.execute()
# If configure_lb fails:
# 1. remove_lb_config() (no-op, not created)
# 2. delete_servers() ✅
# 3. delete_database() ✅
# Result: Clean state, no orphaned resources
```

---

## When NOT to Use Saga

- Single-step operations (use simple try/catch)
- Read-only operations (no state change)
- Idempotent operations (can retry safely)

---

## References

- [Microservices Patterns - Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [AWS Step Functions](https://aws.amazon.com/step-functions/) (Saga implementation)
- [Kubernetes Operators](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [Terraform Destroy](https://www.terraform.io/docs/commands/destroy.html)

---

## Related ADRs

- [ADR-001: Event Sourcing](./001-event-sourcing.md)
