"""Regression tests for the defects found in the review (each one failed before the fix)."""

import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.api import billing
from app.core.config import Settings
from app.models.entities import Drama, Payment, Subscription, User
from tests.support import TestingSession, client, register_user


def add_dramas():
    with TestingSession() as db:
        db.add_all(
            [
                Drama(
                    id=101,
                    title="Nuit Noire",
                    categories=["Thriller", "Mystère"],
                    is_published=True,
                ),
                Drama(
                    id=102,
                    title="Cœurs Unis",
                    categories=["Romance"],
                    is_published=True,
                ),
            ]
        )
        db.commit()


def test_category_filter_works_on_the_production_engine():
    add_dramas()
    r = client.get("/api/v1/dramas", params={"category": "Thriller"})
    assert r.status_code == 200, r.text  # was HTTP 500 on PostgreSQL (JSON column has no @>)
    assert [d["title"] for d in r.json()] == ["Nuit Noire"]
    assert client.get("/api/v1/dramas", params={"category": "Action"}).json() == []


def test_search_treats_like_wildcards_literally():
    assert client.get("/api/v1/dramas", params={"q": "%"}).json() == []
    assert client.get("/api/v1/dramas", params={"q": "___"}).json() == []
    assert len(client.get("/api/v1/dramas", params={"q": "drama"}).json()) == 1


def test_login_attempts_are_throttled():
    register_user()
    codes = [
        client.post(
            "/api/v1/auth/login",
            json={"email": "journey@example.com", "password": "nope"},
        ).status_code
        for _ in range(7)
    ]
    assert codes[:5] == [401] * 5 and codes[5] == 429


def test_unknown_and_wrong_password_look_identical():
    register_user()
    a = client.post("/api/v1/auth/login", json={"email": "journey@example.com", "password": "bad"})
    b = client.post("/api/v1/auth/login", json={"email": "ghost@example.com", "password": "bad"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


def test_refresh_rotation_and_reuse_revokes_the_whole_family():
    t1 = register_user()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": t1["refresh_token"]})
    assert r.status_code == 200
    t2 = r.json()
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": t1["refresh_token"]}).status_code == 401  # replay
    assert (
        client.post("/api/v1/auth/refresh", json={"refresh_token": t2["refresh_token"]}).status_code == 401
    )  # family dead


def test_security_headers_present():
    r = client.get("/health/live")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"


# ---------------------------------------------------------------- configuration
def test_missing_environment_fails_closed(monkeypatch):
    for name in ("ENVIRONMENT", "JWT_SECRET", "DATABASE_URL"):
        monkeypatch.delenv(name)
    with pytest.raises(ValueError, match="Unsafe production configuration"):
        Settings(_env_file=None)  # defaults to production: default secret + sqlite are refused


def test_production_rejects_default_secret_and_long_access_tokens():
    good_db = "postgresql+asyncpg://u:p@db:5432/x"
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(environment="production", database_url=good_db, jwt_secret="short")
    with pytest.raises(ValueError, match="ACCESS_TOKEN_MINUTES"):
        Settings(
            environment="production",
            database_url=good_db,
            jwt_secret="x" * 40,
            access_token_minutes=43200,
        )
    ok = Settings(environment="prod", database_url=good_db, jwt_secret="x" * 40)
    assert ok.environment == "production" and ok.database_url == "postgresql+psycopg://u:p@db:5432/x"


def test_jwt_secret_key_alias_is_honoured():
    assert Settings(environment="test", jwt_secret_key="z" * 40).jwt_secret == "z" * 40  # used to be ignored


# ---------------------------------------------------------------- payments
def test_fedapay_webhook_for_unknown_transaction_is_acknowledged_not_retried(
    monkeypatch,
):
    monkeypatch.setattr(billing.settings, "fedapay_webhook_secret", "whsec")
    body = json.dumps({"name": "transaction.approved", "entity": {"id": 999}}).encode()
    ts = int(time.time())
    sig = hmac.new(b"whsec", f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    r = client.post(
        "/api/v1/webhooks/fedapay",
        content=body,
        headers={"x-fedapay-signature": f"t={ts},s={sig}"},
    )
    assert r.status_code == 200 and r.json()["ignored"] is True  # was 404 => endless provider retries


def test_renewals_stack_after_the_current_period():
    with TestingSession() as db:
        user = User(email="s@x.co", full_name="S", password_hash="x")
        db.add(user)
        db.flush()
        billing.seed_plans(db)
        for i, plan in enumerate(["plan_weekly", "plan_monthly"]):
            sub = Subscription(user_id=user.id, plan_id=plan, status="pending")
            db.add(sub)
            db.flush()
            pay = Payment(
                user_id=user.id,
                subscription_id=sub.id,
                provider="fedapay",
                provider_reference=f"REF{i}",
                amount_xof=1000,
                status="pending",
            )
            db.add(pay)
            db.commit()
            assert billing._apply_payment_result(db, pay, True) == "success"
        last = db.scalar(select(Subscription).where(Subscription.plan_id == "plan_monthly"))
        ends = last.ends_at if last.ends_at.tzinfo else last.ends_at.replace(tzinfo=UTC)
        assert timedelta(days=36) < ends - datetime.now(UTC) <= timedelta(days=37)
