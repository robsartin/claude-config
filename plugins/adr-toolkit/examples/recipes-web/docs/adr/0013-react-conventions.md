---
status: Accepted
date: "2026-07-08"
topic: react-conventions
tags: [ui-tech, react]
supersedes: []
related: [js-ts-project, web-frontend-baseline, accessibility-in-react, d3-with-react]
---
# 13. React conventions

## Context

React is unopinionated about structure and state, so a project needs conventions to stay
consistent and avoid common footguns around effects, state ownership, and re-rendering.
This builds on the JS/TS and web-frontend baselines.

## Decision

- **Function components with hooks** only; no class components.
- **Unidirectional data flow** — state lives at the lowest common owner and flows down via
  props; children raise events up via callbacks.
- **Server/cache state via a data-fetching library** (e.g. TanStack Query) kept distinct
  from local UI state; avoid duplicating server data into a global store.
- **Effect discipline** — `useEffect` is for synchronizing with external systems, not for
  deriving state; derived values are computed during render or memoised.
- **Stable, meaningful `key`s** for lists (never array index for dynamic lists).
- Components are typed with explicit prop types; no implicit `any`.

## Alternatives considered

- **Class components** — support lifecycle methods directly, but hooks are the current
  idiom and mixing both styles fragments patterns across the codebase for no gain.
- **Duplicating server data into a global store** (e.g. Redux) — avoids adding a
  data-fetching library, but reintroduces the cache-consistency bugs a dedicated library
  (e.g. TanStack Query) solves.
- **Array index as list key** — least code to write, but breaks reconciliation identity on
  reorder/insert, causing the stale-state bugs this convention exists to avoid.

## Consequences

- State ownership and data flow are predictable, reducing a class of re-render and
  stale-state bugs.
- Keeping server state out of the global store avoids cache-consistency tangles.
- Hooks/effect discipline is enforced by review, not the compiler, so misuse can still
  land and depends on reviewer vigilance.
