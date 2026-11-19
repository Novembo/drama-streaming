---
name: mockup-to-ui-implementation
description: "Implement web or mobile UI faithfully from mockups: design tokens, component breakdown, responsive behavior, states, assets, and visual diff checks. Use when given Figma, screenshots, or PDF designs to turn into HTML/CSS, Vue, React, or React Native."
---

# Mockup to UI Implementation

## Workflow
1. Inventory the mockup: screens, flows, components, assets, copy, and data fields. List anything missing (states, breakpoints, error text, empty data, icons) and ask for it in one consolidated question rather than guessing silently.
2. Extract design tokens first: colors, typography scale, spacing scale, radii, shadows, breakpoints. Define them once as CSS variables or theme values.
3. Break the screens into reusable components (button, input, card, list item, modal) and build them in isolation with their variants and states.
4. Assemble screens from components; use semantic HTML, flexbox/grid, and relative units instead of absolute positioning.
5. Implement responsive behavior explicitly: confirm the mobile, tablet, and desktop layouts, or define reasonable rules and state them.
6. Implement every state: hover, focus, active, disabled, loading, empty, error, and success.
7. Optimize assets (SVG for icons, correctly sized WebP/AVIF images) and include alt text.
8. Compare against the mockup with side-by-side screenshots (for example Playwright screenshots at fixed viewport widths) and fix visible deviations.

## Rules
- Match the mockup for layout, spacing, typography, and color; where the mockup is ambiguous, choose the simplest accessible behavior and document it.
- Do not hardcode copy or data that should come from content or an API; keep text in constants or i18n files.
- Maintain accessibility: sufficient contrast, keyboard focus styles, labels for inputs, correct heading order, touch targets of adequate size.
- No pixel-perfect hacks that break at other viewport sizes or font settings.
- Keep components small and reusable; avoid copy-pasting near-duplicate markup.
- Never invent brand assets or fonts; request them or use clearly marked placeholders.

## Example
```css
:root {
  --color-primary: #0b5fff;  --color-text: #1b1f24;  --color-bg: #ffffff;
  --space-2: 0.5rem;  --space-4: 1rem;  --radius-md: 0.5rem;
  --font-body: "Inter", system-ui, sans-serif;
}
.btn { background: var(--color-primary); color: #fff; padding: var(--space-2) var(--space-4);
       border-radius: var(--radius-md); font: 600 1rem/1.25 var(--font-body); }
.btn:focus-visible { outline: 3px solid color-mix(in srgb, var(--color-primary) 40%, white); outline-offset: 2px; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
```

## Verification
Screenshot each screen at the agreed breakpoints, compare with the mockup, tab through the page with the keyboard, and run an accessibility checker (for example axe or Lighthouse).

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
