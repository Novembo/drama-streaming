---
name: data-modeling-postgresql
description: "Design PostgreSQL schemas, constraints, indexes, and query patterns for correctness and scale. Use when modeling relational data or reviewing PostgreSQL performance and integrity."
---

# PostgreSQL Data Modeling

## Workflow
1. Translate business invariants into entities, relationships, lifecycle, retention, and access patterns.
2. Choose data types deliberately; use numeric types for exact money and timezone-aware timestamps for instants.
3. Enforce uniqueness, referential integrity, and valid states with database constraints wherever possible.
4. Design indexes from real query predicates/orderings; verify with `EXPLAIN (ANALYZE, BUFFERS)` on representative data.
5. Consider partial, composite, covering, and expression indexes only when measured query patterns justify them.
6. Plan partitioning only when data volume, retention, or query patterns make it useful.
7. Document transaction isolation and concurrency behavior for critical workflows.

## Rules
- Avoid storing relational data as JSONB by default; use it for genuinely flexible/document-shaped attributes.
- Never assume application-level validation prevents concurrent duplicates.
- Avoid over-indexing write-heavy tables.
- Use UTC-aware timestamps and explicit timezone conversion at presentation boundaries.
- Consider privacy, retention, and deletion requirements in the schema.

## Verification
Test constraints, migrations, query plans, concurrent writes, and backup/restore against representative data.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
