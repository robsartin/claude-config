---
status: Accepted
date: "2026-07-08"
topic: web-frontend-baseline
tags: [app-shape, web-frontend]
supersedes: []
related: [react-conventions, accessibility-baseline]
---
# 12. Web frontend baseline

## Context

A web frontend needs a predictable build, component model, and boundaries so a new feature
does not require re-deriving the build config or state boundaries each time, independent of
the specific UI framework chosen (recorded separately).

## Decision

- **Vite** is the build/dev tooling (fast dev server, standard production build).
- **Component-based structure** with a clear separation between presentational components
  and state/data-fetching concerns.
- **Explicit state boundaries** — server/cache state is distinguished from local UI state
  rather than conflated in one global store.
- **Routing** is defined declaratively in one place.
- The app is built and served as static assets where possible; runtime configuration is
  injected, not baked into the bundle.

## Alternatives considered

- **Webpack/CRA-style tooling** — more configurable, but slower dev-server startup and more
  config to maintain than Vite.
- **A single global store for all state** (e.g. Redux holding server data) — rejected
  because it conflates cache/server state with UI state, the exact bug class we want to
  avoid.
- **File-based/implicit routing** — convenient for very small apps, but a single explicit
  route definition is easier to audit as the app grows.

## Consequences

- Frontends share one predictable build and structure regardless of framework.
- Separating server state from UI state avoids a common class of caching and consistency
  bugs.
- The specific UI framework (React, etc.) is a separate, layered decision.
- Enforcing separate server/UI state and one central route table is structure a trivial
  single-screen app does not need.
