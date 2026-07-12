---
status: Accepted
date: "2026-07-08"
topic: js-ts-toolchain
tags: [language, js-ts, toolchain]
supersedes: []
related: [js-ts-project, ci-is-the-merge-gate, observability-in-js-ts]
---
# 10. Standardize the JS/TS quality toolchain

## Context

The universal CI-gate decision requires enforced formatting, tests, and coverage, leaving
the tools to each language. JS/TS projects need a concrete, consistent toolchain so the
gate is measurable and uniform.

## Decision

Configured in the project and run in CI:

- **ESLint** (with `typescript-eslint`) for linting and **Prettier** for formatting,
  failing the build on violations.
- **Vitest** as the test runner.
- **Coverage** via Vitest's **c8/V8** provider, enforcing the universal thresholds —
  **line > 80%, branch > 65%** — and failing the build below them. A project may tighten
  these but never loosen them.
- Type checking (`tsc --noEmit`) runs in CI as its own gate.

## Alternatives considered

- **Jest** — rejected in favor of Vitest; Vitest shares config and transforms with a
  Vite-based build instead of needing a separate transpilation pipeline.
- **istanbul/nyc coverage provider** — rejected in favor of Vitest's built-in c8/V8
  provider, which needs no extra instrumentation step and reuses the V8 engine's own data.
- **Biome (combined lint/format) in place of ESLint + Prettier** — rejected; ESLint's
  `typescript-eslint` plugin ecosystem has a larger set of type-aware lint rules (e.g.
  `no-unsafe-assignment`, `no-floating-promises`) than Biome currently ships.

## Consequences

- The universal coverage gate is concrete for JS/TS via Vitest coverage.
- Lint, format, type-check, and test are each enforced on every change.
- The toolchain is the modern Vite/Vitest stack; projects on other runners adopt this
  baseline or record a superseding decision.
- Four separate gates (lint, format, type-check, test) each run on every change, adding CI
  wall-clock the contributor waits on.
