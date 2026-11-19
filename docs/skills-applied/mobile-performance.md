---
name: mobile-performance
description: "Optimize React Native/Expo performance: startup time, list virtualization, rendering, images, JS thread blocking, memory, and bundle size. Use when apps feel slow, janky, or heavy."
---

# Mobile Performance

## Measure first
Profile on real **mid/low-end devices** in release builds (React Native DevTools profiler, Xcode Instruments, Android Studio/Perfetto). Define targets: cold start, time-to-interactive, frame rate (smooth 60fps), memory, app size.

## Startup and bundle
- Use Hermes; keep the initial bundle small: lazy-load heavy screens/libraries, remove unused dependencies, avoid large JSON imports at startup.
- Defer non-critical work (analytics, prefetch) until after first render; keep the splash-to-content path minimal.

## Rendering
- Use `FlatList`/`FlashList` with stable `keyExtractor`, `getItemLayout` where possible, windowing tuned, and memoized row components; avoid inline functions/objects that break memoization in hot paths.
- Avoid unnecessary re-renders (state colocated, selectors, `memo`/`useCallback` where profiling shows benefit).
- Run animations on the UI thread (Reanimated); avoid layout thrash and heavy work during gestures.

## Data and media
- Resize and cache images (appropriate dimensions, modern formats, caching libraries); lazy-load offscreen media.
- Keep heavy parsing/crypto off the JS thread when it blocks interaction; paginate and cache API data; compress payloads.

## Resources
Clean up timers, listeners, and subscriptions; watch for memory leaks in navigation stacks; minimize background work for battery and data use, which matters on metered or slow networks.

## Verify
Compare before/after metrics on the same device, in release mode, and guard regressions with performance budgets in CI where feasible.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
