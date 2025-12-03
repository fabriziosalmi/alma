# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for ALMA.

## What is an ADR?

An ADR is a document that captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this structure:
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Date**: When the decision was made
- **Context**: What is the issue we're seeing that is motivating this decision?
- **Decision**: What is the change that we're proposing/doing?
- **Consequences**: What becomes easier or more difficult to do because of this change?

## Index

- [ADR-001: Event Sourcing for Infrastructure Changes](./001-event-sourcing.md)
  - **Decision**: Keep Event Sourcing for audit trail and compliance
  - **Rationale**: Infrastructure is stateful and regulated, needs immutable audit logs

- [ADR-002: Saga Pattern for Multi-Step Operations](./002-saga-pattern.md)
  - **Decision**: Keep Saga Pattern for automatic rollback
  - **Rationale**: Infrastructure operations span multiple systems, need coordinated rollback

## Why These Patterns?

Both Event Sourcing and Saga Pattern were questioned in code review as "over-engineered for an API wrapper."

**Our Response**: Infrastructure is NOT just an API wrapper. It's:
- **Stateful**: Changes have long-term consequences
- **Regulated**: Compliance requires audit trails (GDPR, SOC2, HIPAA)
- **Distributed**: Changes span multiple systems (AWS, Docker, Kubernetes)
- **Critical**: Failures need automatic rollback to prevent orphaned resources

If AWS CloudTrail, Kubernetes, and Terraform use these patterns, they're proven for infrastructure.

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
