---
status: Accepted
date: "{{date}}"
topic: d3-with-svelte
tags: [interaction, data-viz, svelte]
supersedes: []
related: [d3-baseline, svelte-conventions]
---
# {{number}}. D3 with Svelte — Svelte owns the DOM, D3 owns the math

## Context

D3 and Svelte both want to own the DOM. Svelte has no virtual DOM: the compiler emits
targeted update code against nodes it believes it owns. If D3 mutates those nodes, there is
no reconciliation pass to notice — Svelte's next update simply writes over or around D3's
work, or updates a node D3 has since moved. Svelte 5 adds a second hazard: `$state` on an
object or array is a deep proxy, so a dataset in `$state` is both deeply tracked (a real
cost on large arrays) and handed to D3 as a proxy rather than the object it expects.
Selecting both D3 and Svelte forces a decision on who owns what.

## Decision

- **D3 owns the math; Svelte owns the DOM.** Use D3's scales, shapes (`d3.line`, `d3.arc`),
  layouts, and geo generators to compute values, then render the resulting SVG in markup.
  Do not call `d3.select(...).append(...)` on Svelte-managed nodes.
- **Keep D3 objects and large datasets out of deep reactivity** — hold them in `$state.raw`
  so Svelte tracks the reference rather than every node of the structure, and D3 receives
  plain objects rather than proxies.
- Where an imperative D3 behavior is genuinely needed (complex transitions, zoom/brush),
  **isolate it behind `bind:this`** on an element Svelte renders but does not update after
  mount, and confine the D3 code to an `$effect` that owns that subtree and tears down its
  listeners and timers on cleanup.
- Derive scales and generators with `$derived`, so they recompute only when data or
  dimensions change.

## Alternatives considered

- **Let D3 select and mutate Svelte-managed nodes directly** — rejected because Svelte's
  generated update code assumes it is the only writer. There is no diff to reconcile the
  difference, so corruption shows up as nodes that stop updating or update the wrong row.
- **Render D3's output via `{@html}`** — rejected because it bypasses Svelte's event
  handling and updates for the chart subtree and reopens the XSS surface markup normally
  closes.
- **Put the dataset and D3 objects in plain `$state` like any other state** — consistent on
  its face, but deep proxying a large dataset costs on every access, and D3 internals handed
  a proxy can compare or mutate the wrong identity.
- **Adopt a higher-level Svelte charting library instead of raw D3** — rejected because it
  trades away direct access to D3's scales/shapes/layouts for a narrower, opinionated API,
  when the goal here is D3's full computational toolkit.

## Consequences

- No tug-of-war over the DOM: Svelte's update code and D3 no longer overwrite each other.
- Most charts become declarative markup driven by D3-computed values, which is testable and
  familiar to Svelte developers.
- Large datasets stay cheap, because they are not deeply proxied.
- The escape hatch (`bind:this` plus `$effect`) is imperative code inside a declarative
  component, so it needs closer review and explicit teardown, and cannot be tested the way
  markup-driven components are.
