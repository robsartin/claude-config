# Architecture Decision Records

## Universal

- [1. Record architecture decisions with ADRs](0001-record-architecture-decisions.md) — _Accepted_
  Architecturally significant decisions — choices that shape structure, dependencies, interfaces, or the way the team works — need a durable record.
  Related: [6. Keep developer and user documentation current](0006-keep-documentation-current.md)
- [2. Develop with Test-Driven Development](0002-use-test-driven-development.md) — _Accepted_
  We want a fast feedback loop, a regression safety net, executable documentation of behavior, and the freedom to refactor without fear.
- [3. Integrate via a PR-based trunk workflow](0003-pr-based-trunk-workflow.md) — _Accepted_
  We want `main` to stay releasable at all times, changes to be reviewable in coherent units, and history to be legible.
  Related: [4. Use the Mikado Method to keep the build green](0004-mikado-method-for-changes.md), [5. Make CI the merge gate](0005-ci-is-the-merge-gate.md), [6. Keep developer and user documentation current](0006-keep-documentation-current.md)
- [4. Use the Mikado Method to keep the build green](0004-mikado-method-for-changes.md) — _Accepted_
  Large refactorings, and changes that ripple across a codebase, tempt us into long stretches where nothing compiles and nothing is committable.
  Related: [3. Integrate via a PR-based trunk workflow](0003-pr-based-trunk-workflow.md)
- [5. Make CI the merge gate](0005-ci-is-the-merge-gate.md) — _Accepted_
  Standards that are not enforced erode.
  Related: [10. Standardize the JS/TS quality toolchain](0010-js-ts-toolchain.md)
- [6. Keep developer and user documentation current](0006-keep-documentation-current.md) — _Accepted_
  Documentation that lags the code is worse than none — it misleads.
  Related: [1. Record architecture decisions with ADRs](0001-record-architecture-decisions.md), [3. Integrate via a PR-based trunk workflow](0003-pr-based-trunk-workflow.md)
- [7. Declare an explicit license and copyright](0007-license-and-copyright.md) — _Accepted_
  A repository with no license is "all rights reserved" by default — others (and future us) have no clear terms for use, and intent is ambiguous.
- [8. Maintain a security baseline](0008-security-baseline.md) — _Accepted_
  Secrets committed to a repository are effectively public and permanent — history preserves them even after deletion.

## Language

- [9. Structure JS/TS projects with TypeScript and ESM](0009-js-ts-project.md) — _Accepted_
  The JavaScript ecosystem offers many package managers, module systems, and language configurations.
  Related: [10. Standardize the JS/TS quality toolchain](0010-js-ts-toolchain.md), [11. Plain-JS (no-framework) conventions](0011-plain-js-conventions.md)
- [10. Standardize the JS/TS quality toolchain](0010-js-ts-toolchain.md) — _Accepted_
  The universal CI-gate decision requires enforced formatting, tests, and coverage, leaving the tools to each language.
  Related: [9. Structure JS/TS projects with TypeScript and ESM](0009-js-ts-project.md), [5. Make CI the merge gate](0005-ci-is-the-merge-gate.md)

## UI tech

- [11. Plain-JS (no-framework) conventions](0011-plain-js-conventions.md) — _Accepted_
  Some UI is best served without a component framework — small widgets, progressive enhancement, or performance-critical surfaces.
  Related: [9. Structure JS/TS projects with TypeScript and ESM](0009-js-ts-project.md), [13. D3 with plain JS — D3 owns the DOM](0013-d3-with-plain-dom.md)

## Library

- [12. Use D3 for bespoke data visualization](0012-d3-baseline.md) — _Accepted_
  Charting libraries cover common chart types quickly but constrain custom, data-driven visuals.
  Related: [13. D3 with plain JS — D3 owns the DOM](0013-d3-with-plain-dom.md)

## Interaction

- [13. D3 with plain JS — D3 owns the DOM](0013-d3-with-plain-dom.md) — _Accepted_
  Without a component framework reconciling the DOM, there is no conflict over ownership, and D3's data-join model is the idiomatic way to build and update a visualization.
  Related: [12. Use D3 for bespoke data visualization](0012-d3-baseline.md), [11. Plain-JS (no-framework) conventions](0011-plain-js-conventions.md)
