"""Server-side payment adapters. Provider credentials never leave this module."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.models.entities import Payment, SubscriptionPlan, User

TIMEOUT = httpx.Timeout(12.0, connect=4.0)


def _fedapay_base() -> str:
    if settings.fedapay_environment not in ("sandbox", "live"):
        raise HTTPException(500, "FEDAPAY_ENVIRONMENT doit être sandbox ou live")
    return (
        "https://sandbox-api.fedapay.com/v1"
        if settings.fedapay_environment == "sandbox"
        else "https://api.fedapay.com/v1"
    )


def _cinetpay_base() -> str:
    if settings.cinetpay_environment not in ("sandbox", "live"):
        raise HTTPException(500, "CINETPAY_ENVIRONMENT doit être sandbox ou live")
    if settings.cinetpay_base_url:
        return settings.cinetpay_base_url.rstrip("/")
    if settings.cinetpay_api_key.startswith("sk_test_"):
        return "https://api.cinetpay.net"
    if settings.cinetpay_api_key.startswith("sk_live_"):
        return "https://api.cinetpay.co"
    return "https://api.cinetpay.net" if settings.cinetpay_environment == "sandbox" else "https://api.cinetpay.co"


def _public_urls(provider: str) -> tuple[str, str]:
    if not settings.public_api_url or not settings.payment_return_url:
        raise HTTPException(
            503,
            "PUBLIC_API_URL et PAYMENT_RETURN_URL doivent être configurées pour les paiements.",
        )
    base = settings.public_api_url.rstrip("/")
    if not base.startswith("https://") and settings.environment == "production":
        raise HTTPException(503, "Les URLs publiques de paiement doivent utiliser HTTPS.")
    return f"{base}/api/v1/webhooks/{provider}", settings.payment_return_url


def _names(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    return (
        parts[0] if parts else "Client",
        " ".join(parts[1:]) if len(parts) > 1 else "Drama",
    )


def initiate_fedapay(payment: Payment, plan: SubscriptionPlan, user: User, phone_number: str | None) -> str:
    if not settings.fedapay_secret_key:
        raise HTTPException(503, "FEDAPAY_SECRET_KEY non configurée.")
    notify_url, return_url = _public_urls("fedapay")
    first, last = _names(user.full_name)
    customer: dict[str, Any] = {
        "firstname": first,
        "lastname": last,
        "email": user.email,
    }
    if phone_number:
        digits = "".join(c for c in phone_number if c.isdigit())
        digits = digits.removeprefix("229")
        customer["phone_number"] = {"number": digits, "country": "bj"}
    payload = {
        "description": f"Drama — {plan.name}",
        "amount": plan.price_xof,
        "currency": {"iso": "XOF"},
        "callback_url": return_url,
        "customer": customer,
        "custom_metadata": {
            "merchant_reference": payment.provider_reference,
            "user_id": user.id,
            "subscription_id": payment.subscription_id,
        },
    }
    headers = {
        "Authorization": f"Bearer {settings.fedapay_secret_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(f"{_fedapay_base()}/transactions", json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
            transaction = body.get("v1/transaction") or body.get("transaction") or body.get("data") or body
            transaction_id = transaction.get("id")
            if not transaction_id:
                raise ValueError("FedaPay did not return a transaction id")
            token_response = client.post(
                f"{_fedapay_base()}/transactions/{transaction_id}/token",
                json={},
                headers=headers,
            )
            token_response.raise_for_status()
            token_body = token_response.json()
            token = (
                token_body.get("token")
                or token_body.get("v1/transaction/token")
                or token_body.get("data")
                or token_body
            )
            checkout_url = token.get("url") if isinstance(token, dict) else None
            if not checkout_url:
                raise ValueError("FedaPay did not return a checkout URL")
            payment.provider_transaction_id = str(transaction_id)
            return checkout_url
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise HTTPException(
            502,
            "Impossible de créer le paiement FedaPay. Vérifiez les clés et le compte marchand.",
        ) from exc


def _cinetpay_token(client: httpx.Client) -> str:
    if not settings.cinetpay_api_key or not settings.cinetpay_api_password:
        raise HTTPException(503, "CINETPAY_API_KEY et CINETPAY_API_PASSWORD doivent être configurées.")
    try:
        r = client.post(
            f"{_cinetpay_base()}/v1/oauth/login",
            json={
                "api_key": settings.cinetpay_api_key,
                "api_password": settings.cinetpay_api_password,
            },
        )
        r.raise_for_status()
        token = r.json().get("access_token")
        if not token:
            raise ValueError("Missing access_token")
        return token
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            502,
            "Authentification CinetPay impossible. Vérifiez les identifiants marchands du Bénin.",
        ) from exc


def initiate_cinetpay(payment: Payment, plan: SubscriptionPlan, user: User, phone_number: str | None) -> str:
    if not phone_number:
        raise HTTPException(422, "Le numéro Mobile Money est requis pour CinetPay.")
    notify_url, return_url = _public_urls("cinetpay")
    first, last = _names(user.full_name)
    payload = {
        "currency": "XOF",
        "merchant_transaction_id": payment.provider_reference,
        "amount": plan.price_xof,
        "lang": "fr",
        "designation": f"Drama — {plan.name}",
        "client_email": user.email,
        "client_first_name": first,
        "client_last_name": last,
        "client_phone_number": phone_number,
        "success_url": return_url,
        "failed_url": return_url,
        "notify_url": notify_url,
        "channel": "PUSH",
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            token = _cinetpay_token(client)
            r = client.post(
                f"{_cinetpay_base()}/v1/payment",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            r.raise_for_status()
            body = r.json()
            checkout_url = body.get("payment_url")
            notify_token = body.get("notify_token")
            payment.notify_token = hashlib.sha256(notify_token.encode()).hexdigest() if notify_token else None
            payment.provider_transaction_id = str(body.get("transaction_id") or "") or None
            if not checkout_url or not payment.notify_token:
                raise ValueError("Incomplete CinetPay payment response")
            return checkout_url
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise HTTPException(
            502,
            "Impossible de créer le paiement CinetPay. Vérifiez les identifiants et le service marchand.",
        ) from exc


def verify_fedapay_signature(raw: bytes, header: str | None, secret: str, tolerance_seconds: int = 300) -> bool:
    if not header or not secret:
        return False
    timestamp = None
    signatures = []
    for item in header.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                return False
        elif key == "s":
            signatures.append(value)
    if timestamp is None or abs(int(time.time()) - timestamp) > tolerance_seconds or not signatures:
        return False
    expected = hmac.new(secret.encode(), str(timestamp).encode() + b"." + raw, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, sig) for sig in signatures)


def verify_fedapay_transaction(transaction_id: str) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {settings.fedapay_secret_key}",
        "Accept": "application/json",
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(
                f"{_fedapay_base()}/transactions/{quote(transaction_id, safe='')}",
                headers=headers,
            )
            r.raise_for_status()
            body = r.json()
            return body.get("v1/transaction") or body.get("transaction") or body.get("data") or body
    except httpx.HTTPError as exc:
        raise HTTPException(502, "Vérification FedaPay indisponible") from exc


async def verify_cinetpay_transaction(identifier: str) -> dict[str, Any]:
    if not settings.cinetpay_api_key or not settings.cinetpay_api_password:
        raise HTTPException(503, "CinetPay non configuré")
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            auth = await client.post(
                f"{_cinetpay_base()}/v1/oauth/login",
                json={
                    "api_key": settings.cinetpay_api_key,
                    "api_password": settings.cinetpay_api_password,
                },
            )
            auth.raise_for_status()
            token = auth.json().get("access_token")
            if not token:
                raise ValueError("Missing access token")
            r = await client.get(
                f"{_cinetpay_base()}/v1/payment/{quote(identifier, safe='')}",
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            body = r.json()
            return body.get("data") or body
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "Vérification CinetPay indisponible") from exc
