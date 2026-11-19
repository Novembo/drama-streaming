---
name: api-security
description: "Audit or implement API security controls including validation, authorization, rate limiting, and secure error handling. Use when securing an API: input validation, authorization checks, rate limiting, CORS, error leakage, or a security audit."
---

# API Security Audit

## Threat review
- Identify assets, trust boundaries, actors, entry points, and sensitive data.
- Check authentication separately from authorization.
- Verify object-level and function-level authorization on every sensitive operation.
- Validate input with allowlists, length/range limits, and safe parsing.
- Review injection, SSRF, path traversal, mass assignment, insecure file uploads, CORS, CSRF, and unsafe redirects as applicable.
- Check rate limiting, brute-force protection, abuse controls, and resource limits.
- Review secrets, logs, error responses, TLS assumptions, and dependency exposure.

## Implementation rules
- Deny by default; grant least privilege.
- Enforce permissions server-side, not in the frontend.
- Avoid leaking stack traces, tokens, passwords, or personal data.
- Use parameterized database access and safe outbound URL validation.
- Store passwords with a modern password-hashing algorithm via a maintained library.
- Rotate/revoke credentials safely; use short-lived access tokens where appropriate.
- Do not invent compliance claims or guarantee security.

## Output
List verified findings, severity, exploit preconditions, impact, remediation, and tests needed. Clearly label unverified assumptions.

## Examples
```python
# BOLA / IDOR: broken (any logged-in user can read any invoice by guessing IDs)
invoice = db.get(Invoice, invoice_id)

# Fixed: scope the query to the caller's tenant and return 404 when not found
invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id, Invoice.org_id == user.org_id))
if invoice is None:
    raise NotFound()

# Mass assignment: broken
user = User(**request.json())                # attacker sends {"is_admin": true}

# Fixed: explicit input schema that forbids unknown fields
class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    name: str
```

## Finding report format
| ID | Severity | Location | Precondition | Impact | Fix | Test to add | Verified? |
|---|---|---|---|---|---|---|---|
| F-1 | High | GET /invoices/{id} | Any authenticated user | Cross-tenant data read | Scope query by org | `test_cannot_read_other_org_invoice` | Reproduced |

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
