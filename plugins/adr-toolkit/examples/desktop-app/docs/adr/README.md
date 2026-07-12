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
  Related: [10. Enforce JVM quality gates and layered tests](0010-jvm-quality-and-tests.md)
- [6. Keep developer and user documentation current](0006-keep-documentation-current.md) — _Accepted_
  Documentation that lags the code is worse than none — it misleads.
  Related: [1. Record architecture decisions with ADRs](0001-record-architecture-decisions.md), [3. Integrate via a PR-based trunk workflow](0003-pr-based-trunk-workflow.md)
- [7. Declare an explicit license and copyright](0007-license-and-copyright.md) — _Accepted_
  A repository with no license is "all rights reserved" by default — others (and future us) have no clear terms for use, and intent is ambiguous.
- [8. Maintain a security baseline](0008-security-baseline.md) — _Accepted_
  Secrets committed to a repository are effectively public and permanent — history preserves them even after deletion.

## Language

- [9. Build JVM projects with Gradle](0009-jvm-build-with-gradle.md) — _Accepted_
  JVM projects need a consistent build tool, dependency management, and package organization so repositories are predictable to build and navigate, and so shared tooling (formatting, coverage, arch tests) can be applied the same way everywhere.
  Related: [10. Enforce JVM quality gates and layered tests](0010-jvm-quality-and-tests.md)
- [10. Enforce JVM quality gates and layered tests](0010-jvm-quality-and-tests.md) — _Accepted_
  The universal CI-gate decision requires enforced formatting, tests, and coverage, and this project's baseline also calls for architecture tests and real-dependency integration tests.
  Related: [9. Build JVM projects with Gradle](0009-jvm-build-with-gradle.md), [5. Make CI the merge gate](0005-ci-is-the-merge-gate.md)

## App shape

- [11. Accessibility is a baseline requirement](0011-accessibility-baseline.md) — _Accepted_
  Accessibility is a first-class requirement for any user interface, not an enhancement to add later.
  Related: [14. Applying the accessibility baseline in Compose](0014-accessibility-in-compose.md), [12. Native UI baseline](0012-native-ui-baseline.md)
- [12. Native UI baseline](0012-native-ui-baseline.md) — _Accepted_
  A native desktop or mobile UI needs consistent structure so state, rendering, and testing do not require running the UI toolkit to verify, as the app grows, independent of the specific toolkit (recorded separately).
  Related: [11. Accessibility is a baseline requirement](0011-accessibility-baseline.md), [13. Compose conventions](0013-compose-conventions.md)

## UI tech

- [13. Compose conventions](0013-compose-conventions.md) — _Accepted_
  Jetpack Compose / Compose Multiplatform is declarative but unopinionated about state management and structure, so conventions are needed to keep composables predictable and performant.
  Related: [9. Build JVM projects with Gradle](0009-jvm-build-with-gradle.md), [10. Enforce JVM quality gates and layered tests](0010-jvm-quality-and-tests.md), [12. Native UI baseline](0012-native-ui-baseline.md), [14. Applying the accessibility baseline in Compose](0014-accessibility-in-compose.md)

## Interaction

- [14. Applying the accessibility baseline in Compose](0014-accessibility-in-compose.md) — _Accepted_
  The accessibility baseline (WCAG 2.1 AA) is mandatory for this UI.
  Related: [11. Accessibility is a baseline requirement](0011-accessibility-baseline.md), [13. Compose conventions](0013-compose-conventions.md)
