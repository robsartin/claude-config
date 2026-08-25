---
status: Accepted
date: "{{date}}"
topic: vue-conventions
tags: [ui-tech, vue]
supersedes: []
related: [js-ts-project, web-frontend-baseline, accessibility-in-vue, d3-with-vue]
---
# {{number}}. Vue conventions

## Context

Vue offers two component styles (Options API and Composition API) and several state
patterns, and its reactivity is implicit — a value's reactive identity is not obvious from
the call site. A project needs conventions so components stay consistent and so the common
reactivity footguns (losing reactivity on destructure, deriving state in watchers) do not
appear. This builds on the JS/TS and web-frontend baselines.

## Decision

- **Single-file components with `<script setup lang="ts">`** — the Composition API only; no
  Options API components.
- **Typed props and emits** declared via `defineProps<Props>()` / `defineEmits<Emits>()`
  type-only signatures, so the compiler checks them; no implicit `any`.
- **Unidirectional data flow** — state lives at the lowest common owner and flows down via
  props; children raise events up via `emit`. Never mutate a prop.
- **Derived state is `computed`**, never a watcher that assigns to another ref. `watch` /
  `watchEffect` are for synchronizing with external systems (URLs, storage, sockets).
- **Server/cache state via a data-fetching library** (e.g. TanStack Query for Vue) kept
  distinct from client state; **Pinia** for cross-component client state, not for caching
  server responses.
- **Reactivity discipline** — keep reactive objects intact rather than destructuring them;
  where destructuring aids readability, use `toRefs`/`storeToRefs` so the binding survives.
- **Stable, meaningful `:key`** on every `v-for` (never the array index for dynamic lists).
- **`<style scoped>`** by default, so component styles cannot leak.

## Alternatives considered

- **Options API** — familiar and fine for small components, but it splits one concern
  across `data`/`computed`/`methods`, infers types more weakly than `<script setup>`, and
  mixing both styles fragments patterns across the codebase for no gain.
- **Vuex for client state** — rejected because Pinia is the current official recommendation,
  is typed without ceremony, and drops the mutations layer Vuex required.
- **Duplicating server data into Pinia** — avoids adding a data-fetching library, but
  reintroduces the cache-consistency and refetch bugs a dedicated library solves.
- **Watchers that assign derived values** — the imperative habit carried from other
  frameworks, but it re-runs on every dependency change and can cascade or land a frame
  late, producing exactly the stale-value bugs `computed` avoids.
- **Array index as `:key`** — least code to write, but breaks patching identity on
  reorder/insert, causing stale component state.

## Consequences

- Component structure, typing, and state ownership are predictable across the codebase.
- Derived values stay correct by construction, and reactivity survives refactors because
  reactive bindings are not casually destructured.
- Keeping server state out of Pinia avoids cache-consistency tangles.
- Reactivity discipline is enforced by review rather than the compiler, so misuse can still
  land and depends on reviewer vigilance.
