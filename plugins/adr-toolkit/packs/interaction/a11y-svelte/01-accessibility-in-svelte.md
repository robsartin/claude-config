---
status: Accepted
date: "{{date}}"
topic: accessibility-in-svelte
tags: [interaction, accessibility, svelte]
supersedes: []
related: [accessibility-baseline, svelte-conventions]
---
# {{number}}. Applying the accessibility baseline in Svelte

## Context

The accessibility baseline (WCAG 2.1 AA) is mandatory for this UI. Svelte is unusual here:
its compiler emits accessibility warnings at build time (missing `alt`, click handlers on
non-interactive elements, mislabelled ARIA), so some of the baseline is checked before the
code ever runs. That coverage is real but partial, and it creates a temptation to treat a
clean build as a clean audit. Svelte also routes on the client, so focus needs the same
deliberate handling any SPA does. This ADR records the Svelte-specific mechanics.

## Decision

- **Compiler accessibility warnings are errors.** Fail the build on them rather than
  filtering them out; suppress an individual warning only inline, with a comment justifying
  it.
- **Treat the compiler as a floor, not the audit.** It checks markup it can see
  statically; contrast, focus order, live-region behavior, and anything assembled at
  runtime still need testing.
- **Semantic elements in markup** — `<button>`, `<nav>`, `<label>`, headings; reserve
  `role`/ARIA for genuine gaps. Never put `onclick` on a non-interactive element without
  full keyboard support (the compiler will say so).
- **Focus management** — on navigation and dialog open/close, move focus deliberately via
  `bind:this`, awaiting `tick()` so the element exists in the updated DOM; trap focus in
  modals and restore it to the trigger on close.
- **Announce dynamic changes** — render ARIA live regions up front and fill them, so async
  updates (loading, errors, toasts) are announced; a region inserted at the same moment as
  its message may not be.
- **Accessible forms** — `<label for>` tied to inputs, errors linked via `aria-describedby`,
  `aria-invalid` set.
- **Automated verification** — axe assertions in component tests plus Testing Library for
  Svelte queries by role/label.

## Alternatives considered

- **Filtering the compiler's a11y warnings globally** (a `warningFilter` that drops them) —
  rejected outright: it silences the cheapest accessibility signal in the stack, and does it
  invisibly for every future component.
- **Relying on the compiler's warnings as the accessibility strategy** — tempting because
  they are free and already wired in, but they are static checks over markup: they cannot
  see contrast, focus order, whether a live region actually announced, or anything composed
  at runtime.
- **`div` with `onclick` and ARIA roles instead of native elements** — rejected because it
  forces reimplementing keyboard activation, focus styles, and semantics that native
  elements provide for free.
- **Moving focus without awaiting `tick()`** — reads correctly, but Svelte batches DOM
  updates, so the target may not be in the DOM yet and the focus call silently does nothing.
- **CI-only end-to-end accessibility scans without component-level assertions** — rejected
  because regressions surface after merge instead of failing the component test that
  introduced them.

## Consequences

- The cheapest accessibility checks run on every build, and cannot be quietly disabled.
- The remaining baseline is covered by component tests, catching what static analysis
  cannot.
- Developers manage focus and announcements explicitly, including the `tick()` timing.
- Justified suppressions live inline next to the markup they excuse, so review sees them.
