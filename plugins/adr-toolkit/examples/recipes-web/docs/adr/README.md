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
  Related: [10. Standardize the JS/TS quality toolchain](0010-js-ts-toolchain.md), [13. React conventions](0013-react-conventions.md), [18. Internationalization in JS/TS](0018-i18n-in-js-ts.md)
- [10. Standardize the JS/TS quality toolchain](0010-js-ts-toolchain.md) — _Accepted_
  The universal CI-gate decision requires enforced formatting, tests, and coverage, leaving the tools to each language.
  Related: [9. Structure JS/TS projects with TypeScript and ESM](0009-js-ts-project.md), [5. Make CI the merge gate](0005-ci-is-the-merge-gate.md)

## App shape

- [11. Accessibility is a baseline requirement](0011-accessibility-baseline.md) — _Accepted_
  Accessibility is a first-class requirement for any user interface, not an enhancement to add later.
  Related: [16. Applying the accessibility baseline in React](0016-accessibility-in-react.md), [12. Web frontend baseline](0012-web-frontend-baseline.md)
- [12. Web frontend baseline](0012-web-frontend-baseline.md) — _Accepted_
  A web frontend needs a predictable build, component model, and boundaries so a new feature does not require re-deriving the build config or state boundaries each time, independent of the specific UI framework chosen (recorded separately).
  Related: [13. React conventions](0013-react-conventions.md), [11. Accessibility is a baseline requirement](0011-accessibility-baseline.md)

## UI tech

- [13. React conventions](0013-react-conventions.md) — _Accepted_
  React is unopinionated about structure and state, so a project needs conventions to stay consistent and avoid common footguns around effects, state ownership, and re-rendering.
  Related: [9. Structure JS/TS projects with TypeScript and ESM](0009-js-ts-project.md), [12. Web frontend baseline](0012-web-frontend-baseline.md), [16. Applying the accessibility baseline in React](0016-accessibility-in-react.md), [17. D3 with React — React owns the DOM, D3 owns the math](0017-d3-with-react.md)

## Library

- [14. Use D3 for bespoke data visualization](0014-d3-baseline.md) — _Accepted_
  Charting libraries cover common chart types quickly but constrain custom, data-driven visuals.
  Related: [17. D3 with React — React owns the DOM, D3 owns the math](0017-d3-with-react.md), [11. Accessibility is a baseline requirement](0011-accessibility-baseline.md)

## Concern

- [15. Internationalization baseline](0015-internationalization-baseline.md) — _Accepted_
  Retrofitting internationalization is expensive: hard-coded strings, concatenated sentences, and locale-naive formatting are pervasive and tedious to unpick.
  Related: [18. Internationalization in JS/TS](0018-i18n-in-js-ts.md)

## Interaction

- [16. Applying the accessibility baseline in React](0016-accessibility-in-react.md) — _Accepted_
  The accessibility baseline (WCAG 2.1 AA) is mandatory for this UI.
  Related: [11. Accessibility is a baseline requirement](0011-accessibility-baseline.md), [13. React conventions](0013-react-conventions.md)
- [17. D3 with React — React owns the DOM, D3 owns the math](0017-d3-with-react.md) — _Accepted_
  D3 and React both want to own the DOM.
  Related: [14. Use D3 for bespoke data visualization](0014-d3-baseline.md), [13. React conventions](0013-react-conventions.md)
- [18. Internationalization in JS/TS](0018-i18n-in-js-ts.md) — _Accepted_
  The internationalization baseline needs concrete JS/TS tooling that speaks ICU MessageFormat and integrates with the frontend.
  Related: [15. Internationalization baseline](0015-internationalization-baseline.md), [9. Structure JS/TS projects with TypeScript and ESM](0009-js-ts-project.md)
