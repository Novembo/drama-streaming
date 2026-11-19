---
name: senior-engineering-standards
description: "Senior-level quality bar: definition of done, trade-off analysis, risk handling, and non-functional checklists. Use when starting or finishing any feature, design, or review to raise the work to production standard."
---

# Senior Engineering Standards

## Before building
1. Restate the goal, constraints, users, and what is explicitly out of scope. Ask at most 3 blocking questions; otherwise state assumptions.
2. List at least two viable approaches with trade-offs (complexity, cost, risk, reversibility). Prefer the simplest one that meets evidenced requirements.
3. Identify what can go wrong: data loss, security, scale, third-party failure, rollout/rollback.
4. Slice the work into vertical increments that can each be tested, reviewed, and reverted independently.

## Definition of done (all must be true or explicitly waived)
- Behavior matches acceptance criteria; edge cases and failure paths are handled.
- Automated tests cover the new behavior and the bug it prevents from returning.
- Input validated, authorization enforced server-side, secrets absent from code and logs.
- Errors are handled deliberately; logs/metrics make failures diagnosable.
- Migrations are safe and reversible (or a rollback plan exists); config is documented.
- Lint, type checks, tests, and build pass in CI; docs/README/changelog updated.
- Performance considered for the expected load (queries, payload size, N+1, caching).

## Engineering judgment
- Choose boring, well-supported technology unless there is a measured reason not to.
- Make decisions reversible; record significant ones as short ADRs (context, decision, consequences).
- Do not add abstractions, services, or dependencies for hypothetical needs (YAGNI).
- Design for operations: health checks, structured logs, timeouts, graceful shutdown, backups.
- Treat every external input and every dependency as untrusted until validated.

## Communication
Report what changed, why, how it was verified, known limitations, and follow-up risks. Never state that something works unless it was run; say precisely what was and was not verified.

## Senior-level execution and verification

Apply this skill as part of the whole software lifecycle, not as an isolated code-generation task. First inspect the repository and identify the actual framework/runtime versions, architectural boundaries, existing conventions, deployment assumptions and tests. Do not assume a greenfield project or replace working patterns without evidence.

### Delivery workflow

1. Convert the request into observable acceptance criteria, including negative cases and non-functional constraints.
2. Identify affected modules, data contracts, callers, dependencies, security boundaries and operational owners.
3. Propose the smallest coherent implementation plan; identify migration, compatibility and rollback concerns before editing.
4. Implement incrementally, keeping changes focused and reviewable. Preserve public behavior unless a breaking change is explicitly approved.
5. Add or update tests at the appropriate levels. Include boundary, failure, authorization and regression cases where applicable.
6. Run the relevant formatter, linter, type checker, tests, build and security checks available in the project. Report commands and actual outcomes; never fabricate successful execution.
7. Inspect the final diff for accidental changes, debug code, secrets, unsafe defaults, missing documentation and unhandled errors.

### Engineering standards

- Validate untrusted input at system boundaries and enforce authorization at the resource/action boundary, not only in the UI.
- Keep secrets out of source control, logs, examples and test fixtures. Minimize sensitive data collection and retention.
- Make timeouts, retry limits, idempotency and cancellation explicit for network or asynchronous work. Avoid retry storms and duplicate side effects.
- Prefer clear interfaces, cohesive modules, explicit types and observable errors over clever abstractions.
- Measure before optimizing. Consider tail latency, memory, concurrency, database query plans and infrastructure cost when relevant.
- Treat migrations, dependency upgrades, generated code and infrastructure changes as production changes requiring review and rollback planning.
- Document material assumptions, architectural decisions and operational steps close to the code.

### Completion report

State what changed, why, tests/checks actually executed, results, known limitations, deployment or migration steps, and remaining risks. Distinguish implemented, tested, reviewed and deployed; these are different states.
