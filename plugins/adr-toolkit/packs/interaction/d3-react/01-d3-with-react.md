---
status: Accepted
date: "{{date}}"
topic: d3-with-react
tags: [interaction, data-viz, react]
supersedes: []
related: [d3-baseline, react-conventions]
---
# {{number}}. D3 with React — React owns the DOM, D3 owns the math

## Context

D3 and React both want to own the DOM. If both mutate the same nodes, they fight:
React reconciles away D3's changes, or D3 mutates nodes React believes it controls, causing
subtle, hard-to-debug corruption. Selecting both D3 and React forces a decision on who owns
what.

## Decision

- **D3 owns the math; React owns the DOM.** Use D3's scales, shapes (`d3.line`, `d3.arc`),
  layouts, and geo generators to compute values, then render the resulting SVG/DOM with
  JSX. Do not call `d3.select(...).append(...)` on React-managed nodes.
- Where an imperative D3 behavior is genuinely needed (complex transitions, zoom/brush),
  **isolate it behind a `ref`** to a node that React renders but does not touch after mount,
  and confine the D3 code to a `useEffect` with clear ownership of that subtree.
- Keep the computed scales/generators memoised; recompute only when data or dimensions
  change.

## Alternatives considered

- **Let D3 select and mutate React-managed nodes directly** (`d3.select(ref).append(...)`
  outside the ref/effect boundary) — rejected because React's reconciler and D3's imperative
  mutations both believe they own the same nodes, producing the exact corruption this ADR
  exists to avoid.
- **Render D3's output via `dangerouslySetInnerHTML`** — rejected because it discards React's
  event delegation and diffing for the chart subtree and reopens the XSS surface that JSX
  normally closes.
- **Adopt a higher-level React charting library (Recharts, Visx) instead of raw D3** —
  rejected because it trades away direct access to D3's scales/shapes/layouts for a
  narrower, opinionated API, when the goal here is D3's full computational toolkit.

## Consequences

- No tug-of-war over the DOM: React reconciliation and D3 no longer corrupt each other.
- Most charts become declarative JSX driven by D3-computed values, which is testable and
  familiar to React developers.
- The escape hatch (ref + effect) is available for the few behaviors JSX can't express,
  with its imperative scope explicitly bounded.
- The ref/effect escape hatch is imperative code inside a declarative tree, so it needs
  closer review and cannot be tested the way JSX components are.
