---
name: rest-api-design
description: "Design consistent REST APIs: resources, status codes, pagination, filtering, error format (RFC 9457), idempotency, and versioning. Use when defining or reviewing endpoints, contracts, or breaking changes."
---

# REST API Design

## Resources and methods
- Nouns for resources (`/orders/{id}/items`), HTTP verbs for actions. GET safe/idempotent, PUT/DELETE idempotent, POST creates or triggers processes.
- Return correct status codes: 200/201 (with `Location`)/204, 400 validation, 401 unauthenticated, 403 forbidden, 404, 409 conflict, 422 semantic validation, 429 rate limited, 5xx server errors.
- Use 404 (not 403) when revealing a resource's existence would leak information.

## Collections
- Always paginate with bounded limits. Prefer cursor/keyset pagination for large or changing data; offset pagination only for small, stable sets.
- Support explicit filtering and sorting via whitelisted fields; reject unknown sort/filter keys.
- Return stable ordering (include a unique tiebreaker such as `id`).

## Errors
- One consistent error shape; RFC 9457 `application/problem+json` (`type`, `title`, `status`, `detail`, `instance`) plus field-level validation errors.
- Never leak stack traces, SQL, internal hostnames, or whether an account exists.

## Safety and evolution
- Idempotency: accept an `Idempotency-Key` header for POSTs with side effects (payments, orders) and store results.
- Concurrency: use `ETag`/`If-Match` or a version field to prevent lost updates.
- Versioning: avoid breaking changes; add fields instead of changing semantics. Version via path (`/v1`) or header, announce deprecations with dates and `Sunset`/`Deprecation` headers.
- Timestamps in ISO 8601 UTC; money as integer minor units plus currency code; IDs as opaque strings.
- Document everything in OpenAPI and verify the contract with tests.

## Examples
```http
GET /v1/invoices?limit=20&cursor=eyJpZCI6MTAwfQ HTTP/1.1
200 OK
{"data": [{"id": "inv_101", "status": "open"}], "next_cursor": "eyJpZCI6MTIwfQ"}

POST /v1/charges HTTP/1.1
Idempotency-Key: 7c1f0e52-9d1b-4c53-8a53-2f4b1f6d9c10     # retry-safe creation

422 Unprocessable Content
Content-Type: application/problem+json
{"type": "https://api.example.com/errors/validation", "title": "Validation failed",
 "status": 422, "errors": [{"field": "amount", "message": "must be > 0"}]}
```
Use cursor pagination for large or changing lists, one error shape everywhere, and `404` (not `403`) when hiding the existence of another tenant's object.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
