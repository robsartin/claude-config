---
status: Accepted
date: "{{date}}"
topic: swiftui-conventions
tags: [ui-tech, swiftui]
supersedes: []
related: [swift-build-with-spm, swift-quality-and-tests, accessibility-in-swiftui]
---
# {{number}}. SwiftUI conventions

## Context

SwiftUI views are value types that the framework re-evaluates freely, and it offers several
overlapping ways to hold state: `@State`, `@Binding`, `@Observable` (the Observation
framework), and the older `ObservableObject`/`@Published`/`@StateObject` trio. Picking per
file produces components that look similar but invalidate differently, which shows up as
views that fail to update or update far too often. This builds on the Swift language
baseline.

## Decision

- **`@Observable` for reference-type model state**, not `ObservableObject` with `@Published`.
  Observation tracks the properties a view actually reads, so unrelated changes do not
  invalidate it.
- **State ownership follows the view tree** — `@State` owns, `@Binding` borrows, and shared
  dependencies arrive through the `Environment` rather than being passed down through views
  that do not use them.
- **Views stay declarative and cheap.** `body` may be called at any time, so it does no
  I/O, no side effects, and no expensive computation; work belongs in the model or in
  `.task`/`.onChange`.
- **Small composable views over one large `body`** — extract subviews rather than reaching
  for `AnyView`, which erases type information the framework uses to diff efficiently.
- **Stable identity in lists** — `ForEach` over `Identifiable` data with a real, stable id,
  never an array index or a value that changes when the row is edited.
- **Concurrency at the boundary** — `async` work runs in `.task` tied to view lifetime, with
  model types annotated for the main actor where they drive the UI.

## Alternatives considered

- **`ObservableObject` with `@Published` and `@StateObject`** — the established pattern in
  older codebases and most tutorials, but any published change invalidates every observing
  view, whether or not it read that property. `@Observable` narrows invalidation to what was
  actually read.
- **`AnyView` to satisfy the type checker** — the quickest way past a "mismatched types"
  error, but it discards the static view identity SwiftUI relies on to diff, trading a
  compile-time inconvenience for a runtime cost.
- **A strict MVVM layer with a view model per view** — familiar from UIKit, but it often
  reproduces state SwiftUI already manages, and value-type views with `@Observable` models
  cover the same ground with less machinery.
- **Index-based `ForEach` over mutable collections** — convenient with plain arrays, but
  identity shifts on insert or reorder, so row state attaches to the wrong element.

## Consequences

- Views update when the data they read changes, and not otherwise, which removes a common
  class of over- and under-invalidation bugs.
- Composition stays type-rich, so the framework can diff efficiently.
- `@Observable` and the Observation framework require a recent Swift and OS baseline;
  projects supporting older targets need the `ObservableObject` pattern instead, and should
  supersede this ADR rather than mixing both silently.
