---
status: Accepted
date: "2026-07-08"
topic: plain-js-conventions
tags: [ui-tech, plain-js]
supersedes: []
related: [js-ts-project, d3-with-plain-dom]
---
# 11. Plain-JS (no-framework) conventions

## Context

Some UI is best served without a component framework — small widgets, progressive
enhancement, or performance-critical surfaces. Without a framework's structure, direct DOM
code can sprawl, so we hold conventions. This builds on the JS/TS baseline (still
TypeScript).

## Decision

- **TypeScript still applies** — no untyped JS just because there is no framework.
- **Direct, deliberate DOM ownership** — a module owns a known subtree of the DOM and is
  the only thing that mutates it; ownership boundaries are explicit.
- **Event delegation** over per-element listeners where lists are dynamic.
- **State is explicit** — a small module-scoped state object with a single render function
  that maps state to DOM, rather than ad-hoc scattered mutations.
- **Progressive enhancement** — server-rendered HTML works first; scripts enhance it.

## Alternatives considered

- **Pull in a component framework anyway** — gives structure for free, but is unwarranted
  overhead for small widgets and progressive-enhancement surfaces this pack targets.
- **Per-element event listeners** — simpler to read for a handful of static elements, but
  don't scale to dynamic lists the way delegation does.
- **Ad-hoc scattered DOM mutations** — fastest to write initially, but with no single
  render function, state and DOM drift out of sync as the module grows.

## Consequences

- No-framework UI stays structured and typed rather than devolving into scattered DOM edits.
- Clear DOM ownership makes behavior predictable and interoperable with other libraries
  (see the D3 interaction ADR).
- The explicit state/render split trades a little boilerplate for maintainability.
