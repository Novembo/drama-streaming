from app.models.entities import Episode, Payment, Subscription
from tests.support import TestingSession, client, engine  # noqa: F401


def test_health_live():
    assert client.get("/health/live").json() == {"status": "alive"}


def test_register_login_and_me():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "full_name": "Test User",
            "password": "StrongPass!123",
        },
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "wrong"},
        ).status_code
        == 401
    )


def test_catalog_public_and_search():
    assert client.get("/api/v1/dramas").status_code == 200
    assert len(client.get("/api/v1/dramas?q=Drama").json()) == 1
    assert len(client.get("/api/v1/dramas?q=absent").json()) == 0


def test_private_endpoint_requires_auth():
    assert client.get("/api/v1/me/favorites").status_code == 401


def test_plan_prices():
    data = client.get("/api/v1/subscriptions/plans").json()
    assert [p["price_xof"] for p in data] == [1000, 2500, 18000]


def auth_token():
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "journey@example.com",
            "full_name": "Journey User",
            "password": "StrongPass!123",
        },
    )
    return r.json()["access_token"]


def test_favorite_and_history_user_journey():
    with TestingSession() as db:
        db.add(
            Episode(
                id=1,
                drama_id=1,
                episode_number=1,
                title="Premier pas",
                duration_seconds=1800,
                video_360p="https://media.example/360.m3u8",
                subtitles=["FR", "EN"],
                audio_tracks=["FR"],
                is_published=True,
            )
        )
        db.commit()
    token = auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/v1/me/favorites/1", headers=headers).status_code == 204
    assert len(client.get("/api/v1/me/favorites", headers=headers).json()) == 1
    assert (
        client.put(
            "/api/v1/me/progress",
            headers=headers,
            json={"episode_id": 1, "progress_seconds": 950, "completed": False},
        ).status_code
        == 200
    )
    history = client.get("/api/v1/me/history", headers=headers).json()
    assert len(history) == 1 and history[0]["progress_seconds"] == 950
    assert client.delete("/api/v1/me/favorites/1", headers=headers).status_code == 204
    assert client.get("/api/v1/me/favorites", headers=headers).json() == []


def test_admin_route_forbidden_for_regular_user():
    token = auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/v1/admin/dramas", headers=headers, json={"title": "Injected"}).status_code == 403


def test_checkout_does_not_fake_payment_when_not_configured():
    token = auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/v1/subscriptions/checkout",
        headers=headers,
        json={"plan_id": "plan_weekly", "provider": "fedapay"},
    )
    assert response.status_code == 503


def test_free_playback_is_limited_to_360p_and_vip_gets_hd():
    with TestingSession() as db:
        db.add(
            Episode(
                id=1,
                drama_id=1,
                episode_number=1,
                title="Premier pas",
                duration_seconds=1800,
                video_360p="https://media.example/360.m3u8",
                video_480p="https://media.example/480.m3u8",
                video_720p="https://media.example/720.m3u8",
                video_1080p="https://media.example/1080.m3u8",
                is_published=True,
            )
        )
        db.commit()
    token = auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    free = client.get("/api/v1/episodes/1", headers=headers).json()
    assert [q["resolution"] for q in free["qualities"]] == ["360p"]
    assert free["vip_required_for_hd"] is True
    with TestingSession() as db:
        user = (
            db.query(__import__("app.models.entities", fromlist=["User"]).User)
            .filter_by(email="journey@example.com")
            .first()
        )
        from app.api.billing import seed_plans

        seed_plans(db)  # PostgreSQL enforces the plan foreign key (SQLite silently ignored it)
        db.add(
            Subscription(
                user_id=user.id,
                plan_id="plan_monthly",
                status="active",
                ends_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc)
                + __import__("datetime").timedelta(days=30),
            )
        )
        db.commit()
    vip = client.get("/api/v1/episodes/1", headers=headers).json()
    assert [q["resolution"] for q in vip["qualities"]] == [
        "360p",
        "480p",
        "720p",
        "1080p",
    ]
    assert vip["vip_required_for_hd"] is False


def _pending_payment(provider, reference, notify_token=None, transaction_id=None):
    from app.models.entities import Payment, Subscription, SubscriptionPlan, User

    with TestingSession() as db:
        user = db.query(User).filter_by(email="journey@example.com").first()
        plan = db.get(SubscriptionPlan, "plan_weekly")
        if plan is None:
            plan = SubscriptionPlan(
                id="plan_weekly",
                name="Pass Hebdo",
                duration_days=7,
                price_xof=1000,
                features=[],
            )
            db.add(plan)
            db.flush()
        sub = Subscription(user_id=user.id, plan_id=plan.id, status="pending")
        db.add(sub)
        db.flush()
        payment = Payment(
            user_id=user.id,
            subscription_id=sub.id,
            provider=provider,
            provider_reference=reference,
            provider_transaction_id=transaction_id,
            notify_token=__import__("hashlib").sha256(notify_token.encode()).hexdigest() if notify_token else None,
            amount_xof=1000,
            status="pending",
        )
        db.add(payment)
        db.commit()
        return payment.id, sub.id


def test_cinetpay_webhook_verifies_notify_token_and_provider_status(monkeypatch):
    from app.api import billing as billing_api

    auth_token()
    payment_id, sub_id = _pending_payment("cinetpay", "DRM-CINETPAY-001", "notify-secret", "cp-123")

    async def fake_verify(identifier):
        assert identifier == "cp-123"
        return {
            "status": "SUCCESS",
            "merchant_transaction_id": "DRM-CINETPAY-001",
            "amount": 1000,
            "currency": "XOF",
        }

    monkeypatch.setattr(billing_api, "verify_cinetpay_transaction", fake_verify)
    response = client.post(
        "/api/v1/webhooks/cinetpay",
        json={
            "merchant_transaction_id": "DRM-CINETPAY-001",
            "transaction_id": "cp-123",
            "notify_token": "notify-secret",
        },
    )
    assert response.status_code == 200 and response.json()["status"] == "success"
    with TestingSession() as db:
        assert db.get(Subscription, sub_id).status == "active"
        assert db.get(Payment, payment_id).status == "paid"


def test_fedapay_webhook_verifies_signature_and_canonical_transaction(monkeypatch):
    import hashlib
    import hmac
    import json
    import time

    from app.api import billing as billing_api
    from app.core.config import settings

    auth_token()
    payment_id, sub_id = _pending_payment("fedapay", "DRM-FEDAPAY-001", transaction_id="fp-123")
    settings.fedapay_webhook_secret = "fedapay-test-secret"
    monkeypatch.setattr(
        billing_api,
        "verify_fedapay_transaction",
        lambda transaction_id: {
            "id": transaction_id,
            "status": "approved",
            "amount": 1000,
            "currency": {"iso": "XOF"},
        },
    )
    payload = {"name": "transaction.approved", "entity": {"id": "fp-123"}}
    raw = json.dumps(payload, separators=(",", ":")).encode()
    timestamp = str(int(time.time()))
    signature = hmac.new(
        settings.fedapay_webhook_secret.encode(),
        timestamp.encode() + b"." + raw,
        hashlib.sha256,
    ).hexdigest()
    response = client.post(
        "/api/v1/webhooks/fedapay",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-FEDAPAY-Signature": f"t={timestamp},s={signature}",
        },
    )
    assert response.status_code == 200 and response.json()["status"] == "success"
    with TestingSession() as db:
        assert db.get(Subscription, sub_id).status == "active"
        assert db.get(Payment, payment_id).status == "paid"
