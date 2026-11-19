---
name: alembic-migrations
description: "Create safe, reviewable Alembic migrations with autogeneration checks, data migrations, and production rollout strategy. Use when changing SQLAlchemy schemas or deploying database changes."
---

# Alembic Migrations

## Workflow
1. Inspect `env.py`, metadata imports, naming conventions, version table, and deployment migration command.
2. Generate a candidate revision, then manually review every operation; autogenerate is not authoritative.
3. Separate schema changes from large data backfills when lock duration or deploy safety matters.
4. Use expand-and-contract for changes that must coexist with old and new application versions.
5. Add indexes concurrently where supported and account for database-specific transaction restrictions.
6. Make data migrations bounded, resumable, observable, and safe to rerun where possible.
7. Define rollback or forward-fix strategy before production execution.

## Rules
- Never edit an already-applied migration in shared environments.
- Never drop/rename a production column in the same release that first stops using it.
- Avoid loading entire tables into Python for large backfills.
- Do not run migrations from every application worker at startup.
- Test upgrade from the previous schema and downgrade only when downgrade is genuinely supported.

## Verification
Run migrations against an empty database and a representative prior revision; inspect locks, execution time, and resulting schema.

## Examples
```python
# Safe NOT NULL column in three deploys (expand, backfill, contract)
def upgrade():
    op.add_column("users", sa.Column("country", sa.String(2), nullable=True))     # deploy 1: nullable
# deploy 2 (separate migration/job): backfill in batches, then
def upgrade():
    op.alter_column("users", "country", nullable=False)                          # deploy 3: after code writes it

# Index on a live PostgreSQL table
def upgrade():
    with op.get_context().autocommit_block():
        op.create_index("ix_orders_org_created", "orders", ["org_id", "created_at"],
                        postgresql_concurrently=True)
```
Review the generated SQL (`alembic upgrade head --sql`), never edit a migration already applied elsewhere, and test upgrade on a copy of production-like data.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
