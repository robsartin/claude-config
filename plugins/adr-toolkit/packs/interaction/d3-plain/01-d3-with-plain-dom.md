---
status: Accepted
date: "{{date}}"
topic: d3-with-plain-dom
tags: [interaction, data-viz, plain-js]
supersedes: []
related: [d3-baseline, plain-js-conventions]
---
# {{number}}. D3 with plain JS — D3 owns the DOM

## Context

Without a component framework reconciling the DOM, there is no conflict over ownership, and
D3's data-join model is the idiomatic way to build and update a visualization. Selecting D3
alongside plain-JS settles how the two relate.

## Decision

- **D3 owns its visualization subtree directly**, using the **data-join** pattern
  (`selection.data(...).join(...)`, i.e. enter / update / exit) to create, update, and
  remove elements as data changes.
- The plain-JS module grants D3 a container element and treats that subtree as D3-owned —
  no other code mutates it, consistent with the plain-JS DOM-ownership convention.
- Re-render on data change by re-running the join, not by tearing down and rebuilding the
  whole subtree.
- Transitions and interaction (zoom, brush, drag) use D3's own facilities.

## Alternatives considered

- **Hand-rolled DOM diffing (manually tracking created/updated/removed elements)** — rejected
  because it reimplements enter/update/exit ad hoc, less reliably than D3's own join.
- **Tear down and rebuild the subtree on every data change** — rejected because it discards
  DOM state (transitions, focus, scroll position) and is wasteful compared to incremental
  joins.
- **Let D3 compute values only and hand DOM mutation to separate plain-JS code** (mirroring
  the D3-with-React split) — rejected because, without a reconciler, that split adds
  indirection with no ownership conflict to resolve — D3's join is already idiomatic here.

## Consequences

- The visualization uses D3 idiomatically, with efficient incremental updates via joins.
- Ownership is unambiguous: the container subtree belongs to D3, the rest to the app.
- Developers must understand the enter/update/exit model, which is the price of D3's
  control in a no-framework setting.
