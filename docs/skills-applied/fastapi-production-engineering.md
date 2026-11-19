---
name: fastapi-production-engineering
description: "Harden FastAPI services for production lifecycle, configuration, observability, graceful shutdown, and deployment. Use when preparing a FastAPI API for production or reviewing operational readiness."
---

# FastAPI Production Engineering

## Workflow
1. Inspect app factory, lifespan, router composition, settings, logging, database lifecycle, and deployment topology.
2. Use validated environment-based settings and fail fast on missing required configuration.
3. Initialize shared resources in lifespan and close them deterministically; avoid module-import side effects.
4. Define readiness and liveness semantics separately. Readiness should reflect dependencies required to serve traffic; liveness should not trigger restart loops for transient downstream outages.
5. Configure request IDs, structured logs, metrics, tracing, and redaction of credentials and personal data.
6. Set explicit inbound/outbound timeouts, payload limits, concurrency bounds, and graceful shutdown behavior.
7. Validate worker count, connection pool sizes, CPU/memory limits, and async blocking behavior against the deployment platform.

## Rules
- Do not expose debug mode, interactive docs, stack traces, or internal exception details unintentionally.
- Do not run migrations independently in every web worker; use a controlled release step.
- Avoid calling synchronous blocking I/O from async handlers without an intentional threadpool boundary.
- Treat health checks as operational contracts and document dependency semantics.
- Add smoke tests against the built artifact/container.

## Verification
Exercise startup, readiness, shutdown, dependency failure, timeout, and graceful termination in a production-like environment.

## Related

Language-neutral design vs implementation, or adjacent scope: `fastapi-development`, `python-fastapi-enterprise-patterns`. Load the one that matches the task; load several only when the work spans them.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
