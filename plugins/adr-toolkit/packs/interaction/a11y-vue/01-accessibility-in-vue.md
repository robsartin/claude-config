---
status: Accepted
date: "{{date}}"
topic: accessibility-in-vue
tags: [interaction, accessibility, vue]
supersedes: []
related: [accessibility-baseline, vue-conventions]
---
# {{number}}. Applying the accessibility baseline in Vue

## Context

The accessibility baseline (WCAG 2.1 AA) is mandatory for this UI. Vue's model — a patched
DOM, client-side routing without full page loads, and `<Teleport>` moving content out of its
authoring position — changes *how* parts of that baseline are achieved, particularly focus
management and dynamic updates. This ADR records the Vue-specific mechanics.

## Decision

- **Semantic elements in templates** — render `<button>`, `<nav>`, `<label>`, headings, etc.;
  reserve `role`/ARIA for genuine gaps. Never put `@click` on a non-interactive element
  without full keyboard support.
- **Focus management** — on router navigation and dialog open/close, move focus deliberately
  via a template `ref`, awaiting `nextTick()` so the target exists in the patched DOM; trap
  focus in modals and restore it to the trigger on close.
- **`<Teleport>` moves the DOM, not the reading order guarantee** — teleported dialogs and
  menus need explicit focus handling and `aria-modal`/labelling, because their new DOM
  position no longer follows the trigger.
- **Announce dynamic changes** — use ARIA live regions for async updates (loading, errors,
  toasts) that happen without a focus change. A region added to the DOM at the same moment
  its message appears may not announce, so render the region up front and fill it.
- **Accessible forms** — associate `<label for>` with inputs, tie errors to fields via
  `aria-describedby`, and set `aria-invalid`.
- **Automated verification** — `axe` assertions in component tests plus Testing Library for
  Vue queries by role/label, so accessibility is asserted, not assumed.

## Alternatives considered

- **`div`/`span` with `@click` and ARIA roles instead of native elements** — rejected
  because it forces reimplementing keyboard activation, focus styles, and semantics that
  native `<button>`/`<nav>`/`<label>` provide for free.
- **Let the browser manage focus, as a server-rendered app can** — full-page navigations
  reset focus for free, but a client-routed SPA never reloads, so focus strands on the old
  view; it has to be moved deliberately after navigation.
- **Moving focus synchronously in the navigation guard, without `nextTick()`** — reads as
  the obvious place, but the incoming view has not been patched into the DOM yet, so the
  focus target does not exist and the call silently does nothing.
- **CI-only end-to-end accessibility scans (e.g. Lighthouse/axe against built pages) without
  component-level assertions** — rejected because regressions surface late, after merge,
  instead of failing the specific component test that introduced them.

## Consequences

- The accessibility baseline is met within Vue's rendering model, including the cases
  (focus, teleported overlays, live updates) that a server-rendered app gets for free.
- Accessibility is covered by automated component tests, catching regressions in CI.
- Developers manage focus and announcements explicitly, including the `nextTick()` timing —
  work the framework does not do automatically.
