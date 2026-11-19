---
name: fullstack-project-delivery
description: "Coordinate end-to-end implementation across backend, frontend, database, tests, and deployment. Use when delivering a feature end to end across API, database, UI, tests, and deployment."
---

# Full-Stack Project Delivery

## Delivery workflow
1. Clarify actors, workflows, acceptance criteria, non-functional requirements, and out-of-scope items.
2. Inspect repository structure and identify backend/frontend/mobile boundaries.
3. Define API contracts and data ownership before parallel implementation.
4. Plan vertical slices that deliver working user journeys.
5. Implement backend validation, authorization, persistence, and tests before wiring UI behavior.
6. Implement responsive accessible UI with loading/error/empty states.
7. Add integration/E2E tests and verify migrations/configuration.
8. Prepare deployment, observability, backup, security review, and rollback.
9. Provide a release checklist and honest verification report.

## Rules
- Do not build frontend-only security.
- Keep API contracts synchronized and version changes deliberately.
- Avoid generating the entire application in one unreviewed batch.
- Use milestones and acceptance tests.
- Do not mark a feature complete if only its happy path works.
- Make the smallest coherent change and preserve existing project conventions.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
