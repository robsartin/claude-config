---
status: Accepted
date: "2026-07-08"
topic: accessibility-in-react
tags: [interaction, accessibility, react]
supersedes: []
related: [accessibility-baseline, react-conventions]
---
# 16. Applying the accessibility baseline in React

## Context

The accessibility baseline (WCAG 2.1 AA) is mandatory for this UI. React's model — virtual
DOM, re-rendering, and route changes without full page loads — changes *how* some of that
baseline is achieved, particularly focus management and dynamic updates. This ADR records
the React-specific mechanics.

## Decision

- **Semantic elements in JSX** — render `<button>`, `<nav>`, `<label>`, headings, etc.;
  reserve `role`/ARIA for genuine gaps. Never put click handlers on non-interactive
  elements without full keyboard support.
- **Focus management** — on client-side route changes and dialog open/close, move focus
  deliberately (e.g. via a `ref` in `useEffect`); trap focus in modals and restore it on
  close.
- **Announce dynamic changes** — use ARIA live regions for async updates (loading, errors,
  toast notifications) that happen without a focus change.
- **Accessible forms** — associate `<label htmlFor>` with inputs, tie errors to fields via
  `aria-describedby`, and set `aria-invalid`.
- **Automated verification** — `jest-axe` (or equivalent) in component tests plus
  Testing Library queries by role/label, so accessibility is asserted, not assumed.

## Alternatives considered

- **`div`/`span` with `onClick` and ARIA roles instead of native elements** — rejected
  because it forces reimplementing keyboard activation, focus styles, and semantics that
  native `<button>`/`<nav>`/`<label>` provide for free.
- **Let the browser manage focus, as a server-rendered app can** — full-page navigations
  reset focus for free, but a client-routed SPA never reloads, so focus strands on the old
  view; it has to be moved deliberately in a `useEffect` on route change.
- **CI-only end-to-end accessibility scans (e.g. Lighthouse/axe against built pages) without
  `jest-axe` at the component level** — rejected because regressions surface late, after
  merge, instead of failing the specific component test that introduced them.

## Consequences

- The accessibility baseline is met within React's rendering model, including the cases
  (focus, live updates) that a server-rendered app gets for free.
- Accessibility is covered by automated component tests, catching regressions in CI.
- Developers manage focus and announcements explicitly — work the framework does not do
  automatically.
