---
name: low-bandwidth-offline-first-design
description: "Design web and mobile apps that work on slow, expensive, or unreliable networks: budgets, caching, compression, sync queues, and lite modes. Use when users have poor connectivity, limited data plans, or low-end devices."
---

# Low-Bandwidth and Offline-First Design

## Workflow
1. Set explicit budgets: initial page weight, time to interactive on throttled 3G/slow 4G, API payload size, and app download size.
2. Measure on a throttled network and a low-end device profile, not only on fast hardware.
3. Reduce bytes: compress text (Brotli/gzip), serve WebP/AVIF images at sized dimensions, lazy-load below the fold, subset fonts, and drop unused JavaScript.
4. Reduce round trips: paginate, batch requests, return only needed fields, and cache with correct `Cache-Control`/ETag headers.
5. Make reads work offline with cached data, and make writes work offline through a local queue that syncs later.
6. Show honest connection and sync status; never lose user input on failure.

## Rules
- Writes sent from the sync queue must be idempotent (client-generated IDs or idempotency keys) so retries cannot duplicate data.
- Use exponential backoff with jitter for retries and pause syncing when the device is offline.
- Define conflict handling explicitly (last-write-wins, field-level merge, or user prompt) per data type.
- Offer a data-saver or lite mode and avoid auto-playing media or large background downloads.
- Do not cache sensitive data unencrypted on shared devices; clear caches on logout.
- Progressive enhancement: core tasks should work without heavy JavaScript where practical.

## Example
```js
// Offline write queue (concept)
async function saveNote(note) {
  note.id ||= crypto.randomUUID();           // client ID makes retries idempotent
  await localDb.notes.put({ ...note, sync: "pending" });
  trySync();
}
async function trySync() {
  if (!navigator.onLine) return;
  for (const n of await localDb.notes.where("sync").equals("pending").toArray()) {
    const r = await fetch("/api/notes", { method: "PUT", headers: { "Idempotency-Key": n.id }, body: JSON.stringify(n) });
    if (r.ok) await localDb.notes.update(n.id, { sync: "done" });
  }
}
```

## Verification
Test in airplane mode, with packet loss and 3G throttling, mid-sync disconnects, duplicate sends, and conflicting edits from two devices.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
