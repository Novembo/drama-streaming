import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.entities import Payment, Subscription, SubscriptionPlan, User
from app.schemas.contracts import CheckoutInput, CheckoutOut, PlanOut
from app.services.payments import (
    initiate_cinetpay,
    initiate_fedapay,
    verify_cinetpay_transaction,
    verify_fedapay_signature,
    verify_fedapay_transaction,
)

router = APIRouter(tags=["subscriptions & payments"])
DEFAULT_PLANS = [
    {
        "id": "plan_weekly",
        "name": "Pass Hebdomadaire",
        "duration_days": 7,
        "price_xof": 1000,
        "features": ["Sans publicité", "Qualité jusqu’à 1080p", "Tous les dramas"],
    },
    {
        "id": "plan_monthly",
        "name": "Pass Mensuel",
        "duration_days": 30,
        "price_xof": 2500,
        "features": [
            "Sans publicité",
            "Qualité jusqu’à 1080p",
            "Téléchargement hors-ligne (à activer)",
        ],
    },
    {
        "id": "plan_yearly",
        "name": "Pass Annuel",
        "duration_days": 365,
        "price_xof": 18000,
        "features": ["Tous les avantages VIP", "Économie annoncée de 40 %"],
    },
]


def seed_plans(db: Session):
    if db.scalar(select(SubscriptionPlan.id).limit(1)) is not None:
        return  # no write on every GET
    for p in DEFAULT_PLANS:
        if not db.get(SubscriptionPlan, p["id"]):
            db.add(SubscriptionPlan(**p))
    db.commit()


@router.get("/subscriptions/plans", response_model=list[PlanOut])
def plans(db: Session = Depends(get_db)):
    seed_plans(db)
    return [
        PlanOut(
            id=p.id,
            name=p.name,
            duration_days=p.duration_days,
            price_xof=p.price_xof,
            features=p.features,
        )
        for p in db.scalars(select(SubscriptionPlan).where(SubscriptionPlan.is_active.is_(True))).all()
    ]


@router.post("/subscriptions/checkout", response_model=CheckoutOut, status_code=201)
def checkout(
    payload: CheckoutInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    seed_plans(db)
    plan = db.get(SubscriptionPlan, payload.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(404, "Formule indisponible")
    sub = Subscription(user_id=user.id, plan_id=plan.id, status="pending")
    db.add(sub)
    db.flush()
    ref = "DRM" + secrets.token_hex(12).upper()  # <= 30 chars for CinetPay merchant references
    payment = Payment(
        user_id=user.id,
        subscription_id=sub.id,
        provider=payload.provider,
        provider_reference=ref,
        amount_xof=plan.price_xof,
        status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    try:
        checkout_url = (
            initiate_fedapay(payment, plan, user, payload.phone_number)
            if payload.provider == "fedapay"
            else initiate_cinetpay(payment, plan, user, payload.phone_number)
        )
        payment.checkout_url = checkout_url
        db.commit()
        db.refresh(payment)
    except HTTPException:
        payment.status = "failed"
        sub.status = "cancelled"
        db.commit()
        raise
    return CheckoutOut(
        payment_id=payment.id,
        reference=payment.provider_reference,
        status=payment.status,
        amount_xof=payment.amount_xof,
        checkout_url=checkout_url,
        message="Redirigez le client vers la page de paiement sécurisée du prestataire.",
    )


@router.get("/subscriptions/me")
def my_subscription(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sub = db.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.ends_at > datetime.now(UTC),
        )
        .order_by(Subscription.ends_at.desc())
    )
    return {
        "vip": bool(sub),
        "plan_id": sub.plan_id if sub else None,
        "ends_at": sub.ends_at.isoformat() if sub and sub.ends_at else None,
    }


def _apply_payment_result(db: Session, payment: Payment, success: bool):
    if payment.status == "paid":
        return "already_processed"
    sub = db.scalar(select(Subscription).where(Subscription.id == payment.subscription_id).with_for_update())
    payment = db.scalar(select(Payment).where(Payment.id == payment.id).with_for_update())
    if payment.status == "paid":
        return "already_processed"
    if success:
        plan = db.get(SubscriptionPlan, sub.plan_id)
        now = datetime.now(UTC)
        latest = db.scalar(
            select(func.max(Subscription.ends_at)).where(
                Subscription.user_id == sub.user_id, Subscription.status == "active"
            )
        )
        if latest is not None and latest.tzinfo is None:
            latest = latest.replace(tzinfo=UTC)
        start = max(now, latest) if latest else now  # a renewal stacks after the current period instead of wasting it
        payment.status = "paid"
        payment.paid_at = now
        sub.status = "active"
        sub.starts_at = start
        sub.ends_at = start + timedelta(days=plan.duration_days)
        db.commit()
        return "success"
    payment.status = "failed"
    sub.status = "cancelled"
    db.commit()
    return "failed"


@router.post("/webhooks/fedapay")
async def fedapay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_fedapay_signature: str | None = Header(default=None),
):
    if not settings.fedapay_webhook_secret:
        raise HTTPException(503, "FEDAPAY_WEBHOOK_SECRET non configurée")
    raw = await request.body()
    if not verify_fedapay_signature(raw, x_fedapay_signature, settings.fedapay_webhook_secret):
        raise HTTPException(401, "Signature FedaPay invalide")
    try:
        event = await request.json()
    except Exception:
        raise HTTPException(400, "Événement JSON invalide") from None
    event_name = event.get("name") or event.get("type")
    entity = event.get("entity") or event.get("data") or {}
    transaction_id = str(entity.get("id") or "")
    if not transaction_id:
        return {"received": True, "ignored": True}
    payment = db.scalar(
        select(Payment).where(
            Payment.provider == "fedapay",
            Payment.provider_transaction_id == transaction_id,
        )
    )
    if not payment:
        return {
            "received": True,
            "ignored": True,
        }  # not ours: a 404 would make FedaPay retry for days
    if event_name == "transaction.approved":
        verified = await run_in_threadpool(verify_fedapay_transaction, transaction_id)
        verified_status = verified.get("status")
        currency = verified.get("currency") or {}
        currency_iso = currency.get("iso") if isinstance(currency, dict) else currency
        try:
            verified_amount = int(verified.get("amount", -1))
        except (TypeError, ValueError):
            raise HTTPException(400, "Montant FedaPay invalide") from None
        if (
            verified_status != "approved"
            or verified_amount != payment.amount_xof
            or (currency_iso and currency_iso != "XOF")
        ):
            raise HTTPException(
                400,
                "Transaction FedaPay non conforme au montant ou à la devise attendue",
            )
        return {"status": _apply_payment_result(db, payment, True)}
    if event_name in (
        "transaction.declined",
        "transaction.canceled",
        "transaction.cancelled",
    ):
        return {"status": _apply_payment_result(db, payment, False)}
    return {"received": True, "ignored": True}


@router.post("/webhooks/cinetpay")
async def cinetpay_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Notification JSON invalide") from None
    reference = str(payload.get("merchant_transaction_id") or payload.get("cpm_trans_id") or "")
    notify_token = str(payload.get("notify_token") or payload.get("cpm_notify_token") or "")
    if not reference or not notify_token:
        raise HTTPException(400, "Référence ou jeton de notification manquant")
    payment = db.scalar(select(Payment).where(Payment.provider == "cinetpay", Payment.provider_reference == reference))
    if not payment:
        raise HTTPException(404, "Paiement CinetPay inconnu")
    notify_hash = hashlib.sha256(notify_token.encode()).hexdigest()
    if not payment.notify_token or not secrets.compare_digest(payment.notify_token, notify_hash):
        raise HTTPException(401, "Jeton CinetPay invalide")
    if payment.status == "paid":
        return {"status": "already_processed"}
    identifier = str(payload.get("transaction_id") or payload.get("cpm_trans_id") or reference)
    verified = await verify_cinetpay_transaction(identifier)
    status_value = str(verified.get("status") or "").upper()
    merchant_ref = str(verified.get("merchant_transaction_id") or reference)
    amount = verified.get("amount")
    currency = verified.get("currency")
    if merchant_ref != payment.provider_reference:
        raise HTTPException(400, "Référence marchand incohérente")
    if amount is not None:
        try:
            amount_value = int(amount)
        except (TypeError, ValueError):
            raise HTTPException(400, "Montant CinetPay invalide") from None
        if amount_value != payment.amount_xof:
            raise HTTPException(400, "Montant CinetPay incohérent")
    if currency is not None and currency != "XOF":
        raise HTTPException(400, "Devise CinetPay incohérente")
    if status_value == "SUCCESS":
        return {"status": _apply_payment_result(db, payment, True)}
    if status_value in ("FAILED", "CANCELLED", "CANCELED", "REFUSED"):
        return {"status": _apply_payment_result(db, payment, False)}
    return {"status": "pending"}
