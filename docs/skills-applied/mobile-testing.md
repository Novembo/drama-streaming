---
name: mobile-testing
description: "Plan and implement mobile unit, component, integration, and end-to-end tests. Use for mobile unit, component, integration, or E2E tests (Jest, RNTL, Detox, Maestro)."
---

# Mobile Testing and QA

## Workflow
1. Identify supported OS versions, device classes, navigation flows, and risk-critical journeys.
2. Test domain logic separately from native integrations.
3. Add component tests for rendering, accessibility, and user interaction.
4. Add integration/E2E tests for login, navigation, network failures, permissions, and critical transactions.
5. Test app background/resume, offline behavior, orientation, keyboard, and deep links.
6. Verify release builds on representative physical devices when possible.
7. Record device/OS/build details for reproducibility.

## Rules
- Avoid flaky tests based on arbitrary sleeps.
- Mock external services at stable boundaries.
- Include permission-denied and expired-session scenarios.
- Test both Android and iOS when both are claimed as supported.
- Do not claim device coverage that was not performed.

## Examples
```ts
// Component test (React Native Testing Library)
test("shows error on failed login", async () => {
  render(<LoginScreen api={{ login: async () => { throw new Error("401"); } }} />);
  fireEvent.press(screen.getByText("Sign in"));
  expect(await screen.findByText("Invalid credentials")).toBeTruthy();
});
```
Layer the tests: unit and component tests on every commit, a few end-to-end flows on real or emulated devices (for example Maestro or Detox) before release, and manual checks for permissions, offline, interruptions, and low-end hardware.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
