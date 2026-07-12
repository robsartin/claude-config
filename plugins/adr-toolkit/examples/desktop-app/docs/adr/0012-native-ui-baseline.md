---
status: Accepted
date: "2026-07-08"
topic: native-ui-baseline
tags: [app-shape, native-ui]
supersedes: []
related: [accessibility-baseline, compose-conventions]
---
# 12. Native UI baseline

## Context

A native desktop or mobile UI needs consistent structure so state, rendering, and testing
do not require running the UI toolkit to verify, as the app grows, independent of the
specific toolkit (recorded separately). Because it is user-facing, it inherits the
accessibility baseline.

## Decision

- **Unidirectional data flow** with a clear presentation-state layer (MVVM / MVI): the UI
  renders immutable state and emits events; business logic lives outside the view.
- **Declarative UI** — the view is a function of state; avoid imperative widget mutation.
- **State is hoisted and testable** — presentation logic is unit-testable without the UI
  toolkit running.
- **Theming and design tokens** are centralized (color, type, spacing) rather than
  hard-coded per screen, which also supports contrast requirements.
- **Navigation** is modelled explicitly as state.

## Alternatives considered

- **Imperative widget mutation (traditional MVC)** — lets views hold and mutate their own
  state directly, but that couples logic to the UI toolkit and blocks unit testing.
- **State embedded in the view/controller** rather than hoisted — simpler for trivial
  screens, but state stops being testable without the UI running as the app grows.
- **Hard-coded colors/spacing per screen** — faster short-term, but drifts from contrast
  requirements and makes theming and consistency a per-screen chore.

## Consequences

- UI state is predictable and the presentation layer is testable in isolation.
- Declarative, state-driven rendering reduces a class of stale-view bugs.
- The specific toolkit (Compose, etc.) is a separate, layered decision, and accessibility
  applies by default.
- Hoisting state into a presentation layer adds boilerplate (view-model/state-holder
  classes) even for simple, single-screen features.
