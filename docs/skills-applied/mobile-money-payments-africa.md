---
name: mobile-money-payments-africa
description: "Integrate mobile money and local payment aggregators in African markets with provider abstraction, webhooks, idempotency, and reconciliation. Use when adding MTN/Moov/Orange mobile money, card or wallet checkout via aggregators, or payout flows."
---

# Mobile Money and Local Payments (Africa)

## Workflow
1. Identify target countries, currencies (for example XOF, GHS, NGN), providers, and whether you need collections, payouts, or both.
2. Read the chosen provider's current official documentation and sandbox rules; do not assume endpoints, fields, or fees from memory.
3. Wrap each provider behind your own interface (`create_charge`, `get_status`, `refund`, `payout`) so providers can change.
4. Model a payment state machine: `created -> pending -> succeeded | failed | expired | refunded`, with allowed transitions only.
5. Treat the provider webhook as a notification, not the truth: verify the signature, then fetch the transaction status from the provider API before fulfilling.
6. Make every step idempotent with your own reference and an idempotency key; ignore duplicate webhooks safely.
7. Reconcile daily: compare your ledger with provider statements and flag mismatches.

## Rules
- Store money as integer minor units (or whole units for currencies without decimals) plus currency code; never floats.
- Normalize phone numbers to E.164 and re-check each country's current numbering plan; local formats change.
- Mobile money confirmations are asynchronous and can take minutes; the UI must show a pending state and support retry or cancel.
- Never store card numbers or PINs; use hosted checkout or tokens, and keep API keys server-side in secrets management.
- Log provider references and status transitions, never full secrets or personal data.
- Handle timeouts as "unknown", not "failed": query status before retrying a charge to avoid double charges.
- Keep sandbox and live credentials strictly separate and test failure cases (insufficient funds, user cancels, expired prompt).
- This skill is engineering guidance, not legal or compliance advice; confirm licensing and KYC duties with the provider.

## Example
```python
def handle_webhook(payload: bytes, signature: str) -> None:
    if not provider.verify_signature(payload, signature):
        raise PermissionError("bad signature")
    event = parse(payload)
    with db.transaction():
        pay = Payment.objects.select_for_update().get(reference=event.reference)
        if pay.status == "succeeded":          # duplicate webhook: no-op
            return
        status = provider.get_status(event.provider_id)   # confirm with provider API
        if status == "succeeded" and provider_amount_matches(pay, status):
            pay.mark_succeeded(); fulfill_order(pay.order_id)
```

## Verification
Replay the same webhook twice, simulate a delayed confirmation and a timeout, and run a reconciliation on test data.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
