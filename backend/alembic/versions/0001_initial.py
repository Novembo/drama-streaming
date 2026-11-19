"""Initial Drama MVP schema."""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])
    op.create_index(
        "ix_refresh_sessions_token_hash",
        "refresh_sessions",
        ["token_hash"],
        unique=True,
    )
    op.create_table(
        "dramas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tmdb_id", sa.Integer(), unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("original_title", sa.String(255)),
        sa.Column("synopsis", sa.Text(), nullable=False),
        sa.Column("poster_url", sa.String(512), nullable=False),
        sa.Column("banner_url", sa.String(512), nullable=False),
        sa.Column("release_year", sa.Integer()),
        sa.Column("country", sa.String(80), nullable=False),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("rating", sa.Numeric(3, 1)),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dramas_title", "dramas", ["title"])
    op.create_index("ix_dramas_is_published", "dramas", ["is_published"])
    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "drama_id",
            sa.Integer(),
            sa.ForeignKey("dramas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("video_360p", sa.Text(), nullable=False),
        sa.Column("video_480p", sa.Text()),
        sa.Column("video_720p", sa.Text()),
        sa.Column("video_1080p", sa.Text()),
        sa.Column("thumbnail_url", sa.String(512), nullable=False),
        sa.Column("subtitles", sa.JSON(), nullable=False),
        sa.Column("audio_tracks", sa.JSON(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.UniqueConstraint(
            "drama_id", "episode_number", name="uq_episode_drama_number"
        ),
    )
    op.create_index("ix_episodes_drama_id", "episodes", ["drama_id"])
    op.create_table(
        "user_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "episode_id",
            sa.Integer(),
            sa.ForeignKey("episodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("progress_seconds", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "episode_id", name="uq_history_user_episode"),
    )
    op.create_index(
        "ix_history_user_updated", "user_history", ["user_id", "updated_at"]
    )
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "drama_id",
            sa.Integer(),
            sa.ForeignKey("dramas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "drama_id", name="uq_favorite_user_drama"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.create_index("ix_favorites_drama_id", "favorites", ["drama_id"])
    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("price_xof", sa.Integer(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            sa.String(40),
            sa.ForeignKey("subscription_plans.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            sa.Integer(),
            sa.ForeignKey("subscriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("provider_reference", sa.String(120), nullable=False),
        sa.Column("provider_transaction_id", sa.String(120)),
        sa.Column("checkout_url", sa.Text()),
        sa.Column("notify_token", sa.String(255)),
        sa.Column("amount_xof", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index(
        "ix_payments_provider_reference",
        "payments",
        ["provider_reference"],
        unique=True,
    )
    op.create_index(
        "ix_payments_provider_transaction_id", "payments", ["provider_transaction_id"]
    )


def downgrade():
    for table in [
        "payments",
        "subscriptions",
        "subscription_plans",
        "favorites",
        "user_history",
        "episodes",
        "dramas",
        "refresh_sessions",
        "users",
    ]:
        op.drop_table(table)
