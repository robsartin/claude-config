---
status: Accepted
date: "{{date}}"
topic: d3-baseline
tags: [library, data-viz]
supersedes: []
related: [d3-with-react, d3-with-plain-dom, accessibility-baseline]
---
# {{number}}. Use D3 for bespoke data visualization

## Context

Charting libraries cover common chart types quickly but constrain custom, data-driven
visuals. D3 offers full control at the cost of more code and a sharper learning curve. We
record when and how to reach for it, independent of the host UI (the host-specific DOM
ownership rules live in the relevant interaction ADR).

## Decision

- **Use D3 for bespoke or highly data-driven visualization**; prefer a charting library
  for standard charts where its constraints are acceptable.
- **Lean on D3's non-DOM modules freely** — scales, shapes, layouts, geo, interpolation,
  time — regardless of who renders.
- **Responsive by design** — dimensions derive from the container (e.g. `ResizeObserver`),
  not hard-coded; use `viewBox` for SVG scaling.
- **Charts are accessible** — provide a text alternative / data table, meaningful labels,
  and non-color-only encodings, consistent with the accessibility baseline.

## Alternatives considered

- **A charting library alone (Chart.js, Highcharts, Recharts)** — faster for common chart
  types, but rejected as the sole tool because its chart-type abstractions fight bespoke,
  data-driven visuals.
- **Hand-rolled Canvas/WebGL rendering** — full control without a library dependency, but
  rejected because it reinvents the scales, shapes, and layout primitives D3 already
  provides.
- **A narrow specialist library (e.g. deck.gl, Leaflet) for the general case** — excellent
  for its niche, but rejected as a default because it doesn't generalize across the range
  of bespoke visualization this ADR needs to cover.

## Consequences

- Custom visualizations are possible without fighting a charting library's assumptions.
- Responsive, accessible charts are the default expectation, not an afterthought.
- Who owns the DOM (D3 vs. the framework) is deliberately deferred to the host interaction
  ADR, so this baseline stays host-agnostic.
- More code and a steeper learning curve than a charting library — the price of the
  bespoke control this ADR accepts.
