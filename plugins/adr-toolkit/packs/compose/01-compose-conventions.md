---
status: Accepted
date: "{{date}}"
topic: compose-conventions
tags: [ui-tech, compose]
supersedes: []
related: [jvm-build-with-gradle, jvm-quality-and-tests, native-ui-baseline, accessibility-in-compose]
---
# {{number}}. Compose conventions

## Context

Jetpack Compose / Compose Multiplatform is declarative but unopinionated about state
management and structure, so conventions are needed to keep composables predictable and
performant. This builds on the JVM and native-UI baselines.

## Decision

- **State hoisting** — composables are stateless where possible; state lives in a
  ViewModel or is hoisted to the caller, passed down as parameters, with events raised via
  lambdas (unidirectional data flow).
- **Stable, immutable state** drives recomposition; use `remember`/`derivedStateOf` to
  avoid redundant work and mark state types stable so Compose can skip recomposition.
- **Slot APIs and small composables** over large monoliths, for reuse and testability.
- **Material theming / design tokens** via the theme, not hard-coded values.
- **`@Preview`** for every significant composable; UI tests use `compose-test` with
  semantics matchers.

## Alternatives considered

- **Classic XML views / imperative Android UI** — familiar and well-documented, but loses
  the declarative "UI as a function of state" model this pack and the native-UI baseline
  require.
- **State owned inside composables** rather than hoisted — less boilerplate for a one-off
  composable, but blocks reuse and testability outside the toolkit.
- **Large monolithic composables** — fewer files to navigate, but harder to reuse, preview,
  and test than small composables built from slot APIs.

## Consequences

- Recomposition is efficient and predictable because state is stable and hoisted.
- Composables are reusable and testable via previews and semantics-based tests.
- Developers must understand stability/recomposition, the main Compose learning curve.
