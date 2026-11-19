"""Hardening: JSONB categories + GIN index (PostgreSQL), refresh-token families."""

import sqlalchemy as sa

from alembic import op

revision = "0002_hardening"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "refresh_sessions", sa.Column("family_id", sa.String(36), nullable=True)
    )
    op.create_index("ix_refresh_sessions_family_id", "refresh_sessions", ["family_id"])
    if op.get_bind().dialect.name == "postgresql":
        # `JSON` has no containment operator: the category filter returned HTTP 500 on PostgreSQL.
        op.execute(
            "ALTER TABLE dramas ALTER COLUMN categories TYPE JSONB USING categories::jsonb"
        )
    op.create_index(
        "ix_dramas_categories_gin", "dramas", ["categories"], postgresql_using="gin"
    )


def downgrade():
    op.drop_index("ix_dramas_categories_gin", table_name="dramas")
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE dramas ALTER COLUMN categories TYPE JSON USING categories::json"
        )
    op.drop_index("ix_refresh_sessions_family_id", table_name="refresh_sessions")
    op.drop_column("refresh_sessions", "family_id")
