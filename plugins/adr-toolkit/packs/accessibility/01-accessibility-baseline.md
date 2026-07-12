---
status: Accepted
date: "{{date}}"
topic: accessibility-baseline
tags: [app-shape, accessibility]
supersedes: []
related: [accessibility-in-react, accessibility-in-compose, web-frontend-baseline, native-ui-baseline]
---
# {{number}}. Accessibility is a baseline requirement

## Context

Accessibility is a first-class requirement for any user interface, not an enhancement to
add later. Retrofitting it is expensive and usually incomplete. Because this project has a
user interface, accessibility is in scope by default — it is not an opt-in concern. This
baseline is platform-agnostic; how it is achieved in a given UI toolkit is recorded in the
relevant interaction ADR.

## Decision

Every user-facing surface targets **WCAG 2.1 AA**:

- **Native accessible components first** — use the platform's built-in accessible controls
  and semantics before reaching for custom widgets; add explicit accessibility metadata
  only to fill genuine gaps.
- **Full keyboard / non-pointer operability** — every interactive element is reachable and
  operable without a mouse or touch, with a visible focus indicator and deliberate focus
  management for dialogs and navigation changes.
- **Perceivable content** — sufficient color contrast, text alternatives for non-text
  content, adequate touch-target sizing, and no information conveyed by color alone.
- **Clear status and errors** — changes, loading, and errors are communicated to assistive
  technology, not conveyed only visually.
- **Verification is part of done** — automated accessibility checks run in CI, complemented
  by keyboard and screen-reader spot-checks for significant UI.

## Alternatives considered

- **ARIA-retrofit on custom widgets** — building bespoke controls first and adding
  accessibility metadata later is rejected in favor of native controls, which get correct
  semantics and keyboard behavior for free.
- **Treat accessibility as a later enhancement** — deferring it is cheaper upfront but
  retrofitting is expensive and usually incomplete, the problem this baseline exists to
  avoid.
- **Automated checks only, no manual verification** — CI checks catch regressions cheaply
  but miss complex interaction issues that only keyboard/screen-reader spot-checks surface.

## Consequences

- The UI is usable by people relying on assistive technology and non-pointer input from the
  start.
- Accessibility acceptance criteria and verification are built into feature work, adding
  modest ongoing effort.
- Automated checks catch regressions but do not replace manual verification for complex
  interactions.
