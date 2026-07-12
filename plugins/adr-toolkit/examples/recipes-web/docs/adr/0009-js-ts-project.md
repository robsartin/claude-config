---
status: Accepted
date: "2026-07-08"
topic: js-ts-project
tags: [language, js-ts, structure]
supersedes: []
related: [js-ts-toolchain, react-conventions, plain-js-conventions, i18n-in-js-ts]
---
# 9. Structure JS/TS projects with TypeScript and ESM

## Context

The JavaScript ecosystem offers many package managers, module systems, and language
configurations. Inconsistent choices make projects hard to move between and let avoidable
type and interop bugs through. We want one predictable baseline.

## Decision

- **TypeScript** is the language; source is typed, not plain JS.
- **`tsconfig.json` runs in strict mode** (`strict: true`, `noUncheckedIndexedAccess`),
  so the type checker earns its keep.
- **ES Modules** (`"type": "module"`) are the module system.
- **pnpm** is the package manager, with a committed lockfile for reproducible installs.
- Node's version is pinned (e.g. via `.nvmrc` / `engines`) so the toolchain is consistent.

## Alternatives considered

- **Plain JavaScript** — rejected because it defers type and interop errors to runtime
  instead of catching them at build time.
- **CommonJS modules** — rejected in favor of ESM; CommonJS's `require`/`module.exports`
  is the legacy module system and complicates interop with modern, ESM-only packages.
- **npm or Yarn as the package manager** — rejected in favor of pnpm, whose content-addressed
  store gives faster, disk-efficient installs with the same lockfile guarantees.

## Consequences

- Projects share one predictable shape: TypeScript, strict, ESM, pnpm.
- Strict typing catches a class of bugs at build time at the cost of stricter code.
- Contributors use pnpm and the pinned Node version; the lockfile keeps installs
  reproducible.
