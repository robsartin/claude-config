---
status: Accepted
date: "{{date}}"
topic: svelte-conventions
tags: [ui-tech, svelte]
supersedes: []
related: [js-ts-project, web-frontend-baseline, accessibility-in-svelte, d3-with-svelte]
---
# {{number}}. Svelte conventions

## Context

Svelte 5 introduced runes (`$state`, `$derived`, `$props`, `$effect`), which replace the
Svelte 4 model of `let` plus `$:` reactive statements and writable stores. Both still
compile, so a project has to say which one it writes, or it accumulates two mental models
for the same job. Svelte's reactivity is also compile-time: what reacts to what is inferred
from the source, which is convenient until a refactor silently changes the inference. This
builds on the JS/TS and web-frontend baselines.

## Decision

- **Svelte 5 runes only.** `$state` for mutable state, `$derived` for computed values,
  `$props()` for inputs, `$effect` for synchronizing with external systems. No `$:`
  reactive statements.
- **TypeScript in every component** (`<script lang="ts">`), with props typed through
  `$props()`; no implicit `any`.
- **Unidirectional data flow** — state lives at the lowest common owner and flows down via
  props; children raise events through **callback props**, not `createEventDispatcher`.
- **Derived state is `$derived`**, never an `$effect` that assigns to other state. `$effect`
  is for external systems (storage, sockets, imperative libraries) and needs a teardown.
- **Shared state lives in `.svelte.ts` modules** using runes, rather than legacy writable
  stores; server/cache state belongs in a data-fetching library, kept distinct from client
  state.
- **Keyed `{#each}` for anything dynamic** — `{#each items as item (item.id)}`. An unkeyed
  each block is positional.
- **Component styles stay in the component**; reach for `:global()` only with a comment
  saying why.

## Alternatives considered

- **Svelte 4 stores plus `$:` reactive statements** — still supported, and familiar from
  older codebases, but `$:` infers its dependencies from the statement body, so extracting a
  variable can silently drop a dependency or reorder execution. Runes make the dependency
  explicit at the point of declaration.
- **Mixing runes with `$:` in different components** — rejected because the two express the
  same idea differently, and reviewers then have to know which rules apply per file.
- **`createEventDispatcher` for child-to-parent communication** — the Svelte 4 idiom,
  discouraged in Svelte 5: callback props are typed, and dispatched custom events are not.
- **Unkeyed `{#each}`** — fewer characters, but blocks are matched by position, so
  inserting or reordering rebinds existing DOM and component state to the wrong item. This
  is the same class of bug as an index `key` elsewhere, and it is easier to hit here because
  omitting the key is the shorter syntax.
- **`$effect` that assigns derived values** — the habit carried in from other frameworks;
  it runs after render, so consumers can observe a stale value for a frame, and it can
  cascade into further effect runs.

## Consequences

- One reactivity model across the codebase, with dependencies visible at the declaration
  rather than inferred from a statement body.
- Derived values are correct by construction, and effects are reserved for genuine external
  synchronization, where their teardown obligation is obvious.
- List rendering keeps component state attached to the right item across reordering.
- Runes require Svelte 5; components copied from Svelte 4 sources need translating rather
  than pasting, and older third-party examples will not match this style.
