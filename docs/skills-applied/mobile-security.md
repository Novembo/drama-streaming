---
name: mobile-security
description: "Review mobile app storage, authentication, transport, permissions, deep links, and release security. Use for mobile app security: secure storage, auth, TLS/pinning, permissions, deep links, release hardening."
---

# Mobile Application Security

## Threat review
Inspect token storage, local databases, logs, screenshots/clipboard, backup behavior, TLS, deep links, WebViews, exported components, permissions, and dependency supply chain.

## Rules
- Store sensitive credentials in platform-backed secure storage, not plain preferences or AsyncStorage.
- Use TLS and validate server identity; never disable certificate checks in production.
- Do not embed private API keys or signing secrets in app bundles.
- Validate deep-link parameters and authorization server-side.
- Request minimum permissions just in time.
- Avoid sensitive data in logs, crash reports, notifications, and screenshots.
- Use platform security features and keep dependencies updated.
- Define logout, revocation, and lost-device response behavior.

## Examples
```text
Checklist
- Tokens in the platform secure store (Keychain / Keystore, e.g. expo-secure-store), never AsyncStorage or plain files
- TLS only; consider certificate pinning for high-risk apps with a rotation plan
- No secrets in the app bundle: anything shipped can be extracted; use a backend for secrets
- Biometric/PIN gate for sensitive screens; clear sensitive data on logout; hide content in app switcher
- Jailbreak/root signals as risk input, not sole defense
```
Test the release build (not only debug), review third-party SDKs and permissions, and follow OWASP MASVS as a baseline.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
