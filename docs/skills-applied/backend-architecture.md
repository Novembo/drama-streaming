---
name: backend-architecture
description: "Plan or refactor backend architecture, service boundaries, modular monoliths, and domain logic. Use when structuring a backend: modules, service boundaries, layering, domain logic, or splitting a monolith."
---

# Backend Architecture

## Workflow
1. Map current modules, runtime boundaries, data ownership, and dependency direction.
2. Clarify functional requirements and non-functional needs: scale, latency, availability, security, maintainability.
3. Prefer the simplest architecture that satisfies evidenced requirements.
4. Define module responsibilities, interfaces, data ownership, and failure boundaries before broad refactoring.
5. Keep domain rules independent of transport and persistence where practical.
6. Introduce queues, microservices, caches, or event-driven patterns only when justified by concrete constraints.
7. Plan incremental migration and compatibility; avoid big-bang rewrites.
8. Validate architecture with tests and document key decisions.

## Principles
- Separate presentation/transport, application orchestration, domain rules, and infrastructure where complexity warrants it.
- Avoid circular dependencies and shared mutable state.
- Make transactions and consistency boundaries explicit.
- Design APIs around stable contracts and version deliberately.
- Consider observability, deployment, rollback, and operational ownership.
- Do not create layers that only forward calls without adding value.

## Deliverables
Provide a concise architecture diagram or module map when useful, trade-offs, migration steps, and risks.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
