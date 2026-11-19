---
name: payments-webhooks
description: "Integrate payments and webhooks safely (Stripe, mobile money, local aggregators): signature verification, idempotency, reconciliation. Use when handling money, payment callbacks, subscriptions, or any third-party webhook."
---

# Payments and Webhooks

## Payment design
- Use the provider's hosted checkout/SDK so card and wallet data never touch your servers.
- Store money as integer minor units plus currency; never floats.
- The **server decides** amount, currency, and product; never trust prices or totals sent by the client.
- Model an explicit order/payment state machine (`pending → paid | failed | refunded`) with allowed transitions only.
- Use idempotency keys on create/charge calls so retries cannot double-charge.
- For regional providers (mobile money or local aggregators such as FedaPay, KkiaPay, or operator APIs), read the provider's current documentation for callback formats, signature schemes, sandbox behavior, and timeout semantics, and do not assume parity with Stripe.

## Webhook handling
1. Read the **raw body** and verify the signature (HMAC) with a constant-time comparison; reject stale timestamps to prevent replay.
2. Deduplicate by event ID (unique constraint) and process idempotently.
3. Acknowledge quickly with 2xx, then process asynchronously; return non-2xx only when a retry is desired.
4. Handle out-of-order and duplicate events; re-fetch the authoritative object from the provider API before fulfilling.
5. Never rely on the browser redirect/"success page" as proof of payment.

## Operations
- Reconcile payments against provider reports regularly; alert on mismatches and stuck pending orders.
- Log provider references, not card data or secrets; keep an audit trail of state changes.
- Test with provider sandboxes, including failures, duplicates, and delayed callbacks. Comply with provider terms and applicable financial regulations.

## Examples
```python
# runnable
import hashlib, hmac

def verify_signature(secret: bytes, payload: bytes, signature_hex: str) -> bool:
    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_hex)        # constant-time comparison

secret = b"whsec_example"
body = b'{"event":"payment.succeeded","id":"evt_1"}'
good = hmac.new(secret, body, hashlib.sha256).hexdigest()
assert verify_signature(secret, body, good)
assert not verify_signature(secret, body + b" ", good)          # any change to the body fails
print("ok")
```
Verify the signature on the raw body, reject old timestamps if the provider sends one, store processed event IDs to ignore duplicates, return `2xx` quickly, and confirm important state with the provider API. Check each provider's documented signature scheme.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
