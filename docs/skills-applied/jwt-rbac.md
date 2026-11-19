---
name: jwt-rbac
description: "Design, implement, or audit JWT authentication, roles, permissions, and resource-level access control. Use for JWT auth, refresh tokens, roles, permissions, multi-tenant RBAC, or resource-level access control."
---

# JWT Authentication and RBAC

## Workflow
1. Map actors, roles, permissions, resources, and actions.
2. Define authentication lifecycle: login, refresh, logout/revocation, expiry, key rotation.
3. Define authorization policy independently from token parsing.
4. Verify issuer, audience, expiry, not-before, signature, and allowed algorithms.
5. Enforce object-level checks after loading the target resource.
6. Test privilege escalation, cross-tenant access, revoked/expired tokens, and missing claims.
7. Document role/permission changes and migration implications.

## Rules
- Never accept `alg=none` or choose verification algorithm from untrusted token metadata.
- Keep signing keys in secret storage/environment configuration, never in source control.
- Do not treat a role claim as sufficient for object-level authorization.
- Use stable subject identifiers; avoid putting sensitive personal data in JWT payloads.
- Keep access tokens short-lived and design refresh-token rotation/reuse detection where needed.
- Return consistent 401 vs 403 semantics without disclosing sensitive details.
- Fail closed when authorization data is unavailable.

## Examples
```python
import jwt   # PyJWT
from fastapi import Depends, HTTPException, status

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, PUBLIC_KEY_OR_SECRET,
            algorithms=["RS256"],                       # allowlist; never trust the header's alg
            audience="my-api", issuer="https://auth.example.com",
            options={"require": ["exp", "iat", "sub"]},
            leeway=10,
        )
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

def require_role(*roles: str):
    def checker(claims: dict = Depends(current_claims)) -> dict:
        if not set(roles) & set(claims.get("roles", [])):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")
        return claims
    return checker
```
Keep access tokens short-lived, rotate refresh tokens and detect reuse, store signing keys in secrets management, and still check object-level ownership in the handler: a role claim alone does not authorize access to a specific record.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
